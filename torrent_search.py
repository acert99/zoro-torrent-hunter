"""LLM-friendly torrent search built on qBittorrent search plugins (nova3).

Usage:
  python -I torrent_search.py "query" ["query 2" ...] [--cat all] [--top 10] [--engines a,b] [--json]
  python -I torrent_search.py --magnet ENGINE LINK     # resolve a page link into a magnet
  python -I torrent_search.py --open N                 # open result N of the last search in the torrent client

Each positional argument is a separate query; queries and engines run in parallel.
piratebay, nyaa and archive.org are fetched natively to expose uploader trust and download counts.
"""
import argparse
import json
import math
import os
import re
import subprocess
import sys
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor

# Frozen by PyInstaller (Zoro.exe): bundled files live in sys._MEIPASS and there is no python.exe,
# so the exe re-launches itself with --child to run engines (see child_cmd / run_child).
FROZEN = getattr(sys, "frozen", False)
HERE = getattr(sys, "_MEIPASS", "") if FROZEN else os.path.dirname(os.path.abspath(__file__))

# Windows cert stores can hold stale roots ("certificate has expired"); prefer certifi's bundle.
# Set in os.environ so nova2 subprocesses inherit it too.
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

NOVA_DIR = os.environ.get("LTS_NOVA_DIR", os.path.join(HERE, "vendor", "nova3"))
RUNNER = os.path.join(HERE, "run_engine.py")
NOVA_DL = os.path.join(NOVA_DIR, "nova2dl.py")

NATIVE = ("piratebay", "nyaa", "archive")
DEFAULT_ENGINES = "piratebay,nyaa,limetorrents,torrentscsv,rutor"
ENGINE_TIMEOUT = 20
LAST_RESULTS = os.path.join(os.path.expanduser("~"), ".cache", "llm-torrent-search", "last.json")

ENGINE_RE = re.compile(r"[a-z0-9_]{1,40}")
# Only plain btih magnets are opened or returned: no quotes, $, backticks or whitespace that a shell could act on.
MAGNET_RE = re.compile(r"magnet:\?xt=urn:btih:[A-Za-z0-9]{32,40}(&[A-Za-z0-9._~%=+&:/-]*)?")

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0"
TRUST_WEIGHT = {"vip": 2.0, "trusted": 1.5, "licensed": 1.3, "remake": 0.3}

PB_CATS = {"all": None, "movies": "200", "tv": "200", "music": "100", "games": "400",
           "software": "300", "books": "601", "anime": "200"}
NYAA_CATS = {"all": "0_0", "anime": "1_0", "music": "2_0", "books": "3_0", "software": "6_0",
             "games": "6_2", "movies": "4_0", "tv": "4_0"}
PB_TRACKERS = "&".join("tr=" + urllib.parse.quote(t, safe="") for t in (
    "udp://tracker.opentrackr.org:1337/announce",
    "udp://open.stealth.si:80/announce",
    "udp://exodus.desync.com:6969/announce",
    "udp://tracker.torrent.eu.org:451/announce",
))


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=ENGINE_TIMEOUT) as r:
        return r.read().decode("utf-8", errors="replace")


def row(name, size, seeds, leech, engine, link, trust="", downloads=None):
    return {"name": name, "size": int(size) if str(size).lstrip("-").isdigit() else -1,
            "seeds": int(seeds), "leech": int(leech), "engine": engine, "link": link,
            "trust": trust, "downloads": downloads}


def search_piratebay(query, cat):
    params = {"q": query}
    if PB_CATS.get(cat):
        params["cat"] = PB_CATS[cat]
    out = []
    for r in json.loads(fetch("https://apibay.org/q.php?" + urllib.parse.urlencode(params))):
        if r["info_hash"] == "0" * 40:
            continue
        magnet = (f"magnet:?xt=urn:btih:{r['info_hash']}&"
                  f"{urllib.parse.urlencode({'dn': r['name']})}&{PB_TRACKERS}")
        trust = r.get("status") if r.get("status") in ("vip", "trusted") else ""
        out.append(row(r["name"], r["size"], r["seeders"], r["leechers"], "piratebay", magnet, trust))
    return out


def search_nyaa(query, cat):
    url = "https://nyaa.si/?" + urllib.parse.urlencode(
        {"page": "rss", "q": query, "c": NYAA_CATS.get(cat, "0_0"), "f": "0"})
    ns = {"nyaa": "https://nyaa.si/xmlns/nyaa"}
    out = []
    for it in ET.fromstring(fetch(url)).iter("item"):
        g = lambda tag: it.findtext(tag, default="", namespaces=ns)
        h = g("nyaa:infoHash")
        magnet = f"magnet:?xt=urn:btih:{h}&{urllib.parse.urlencode({'dn': g('title')})}&{PB_TRACKERS}"
        trust = "trusted" if g("nyaa:trusted") == "Yes" else "remake" if g("nyaa:remake") == "Yes" else ""
        out.append(row(g("title"), parse_size(g("nyaa:size")), g("nyaa:seeders"), g("nyaa:leechers"),
                       "nyaa", magnet, trust, int(g("nyaa:downloads") or 0)))
    return out


def search_archive(query, cat):
    # archive.org: every item with format "Archive BitTorrent" has a .torrent; no seed counts exposed
    q = f'title:({query}) AND format:"Archive BitTorrent"'
    if cat in ("movies", "tv", "anime"):
        q += " AND mediatype:movies"
    elif cat in ("music",):
        q += " AND mediatype:audio"
    elif cat in ("books",):
        q += " AND mediatype:texts"
    elif cat in ("software", "games"):
        q += " AND mediatype:software"
    params = [("q", q), ("rows", "50"), ("output", "json"), ("sort[]", "downloads desc")]
    params += [("fl[]", f) for f in ("identifier", "title", "downloads", "item_size", "licenseurl")]
    data = json.loads(fetch("https://archive.org/advancedsearch.php?" + urllib.parse.urlencode(params)))
    out = []
    for d in data["response"]["docs"]:
        ident = d["identifier"]
        title = d.get("title") or ident
        title = title[0] if isinstance(title, list) else title
        link = f"https://archive.org/download/{ident}/{ident}_archive.torrent"
        out.append(row(title, d.get("item_size", -1), -1, -1, "archive", link,  # -1 = site has no peer counts
                       "licensed" if d.get("licenseurl") else "", int(d.get("downloads") or 0)))
    return out


def parse_size(text):
    m = re.match(r"([\d.]+)\s*([KMGT]?i?B)", text or "")
    if not m:
        return -1
    mult = {"B": 0, "KiB": 1, "KB": 1, "MiB": 2, "MB": 2, "GiB": 3, "GB": 3, "TiB": 4, "TB": 4}
    return int(float(m.group(1)) * 1024 ** mult.get(m.group(2), 0))


def child_cmd(kind, *args):
    if FROZEN:
        return [sys.executable, "--child", kind, *args]
    return [sys.executable, "-I", RUNNER if kind == "engine" else NOVA_DL, *args]


def run_child(argv):
    """Entry point for `Zoro.exe --child engine|dl ...` (frozen builds only)."""
    kind, args = argv[0], argv[1:]
    sys.path.insert(0, NOVA_DIR)
    if kind == "engine":
        import run_engine
        sys.argv = ["run_engine", *args]
        run_engine.main()
    elif kind == "dl":
        import runpy
        sys.argv = [NOVA_DL, *args]
        runpy.run_path(NOVA_DL, run_name="__main__")


def kill_tree(proc):
    if os.name == "nt":
        subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
    else:
        try:
            os.killpg(proc.pid, 9)
        except ProcessLookupError:  # finished between the timeout and the kill
            pass


def search_nova(engine, query, cat):
    # Slow sites keep printing results; on timeout kill the process and keep what it printed.
    proc = subprocess.Popen(
        child_cmd("engine", NOVA_DIR, engine, cat, query),
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8", errors="replace",
        start_new_session=os.name != "nt",
    )
    try:
        stdout, _ = proc.communicate(timeout=ENGINE_TIMEOUT)
    except subprocess.TimeoutExpired:
        kill_tree(proc)
        stdout, _ = proc.communicate()
    out = []
    for line in stdout.splitlines():
        parts = line.split("|")
        if len(parts) < 6:
            continue
        link, name, size, seeds, leech = parts[:5]
        try:
            out.append(row(urllib.parse.unquote(name), size, seeds, leech, engine, link))
        except ValueError:
            continue
    return out


def run_engine(engine, query, cat):
    try:
        return dispatch(engine, query, cat)
    except Exception as e:  # one dead site must not kill the search
        print(f"[{engine}] {type(e).__name__}: {e}", file=sys.stderr)
        return []


def dispatch(engine, query, cat):
    if not ENGINE_RE.fullmatch(engine) or engine not in installed_engines():
        raise ValueError(f"unknown engine: {engine!r}")
    if engine == "piratebay":
        return search_piratebay(query, cat)
    if engine == "nyaa":
        return search_nyaa(query, cat)
    if engine == "archive":
        return search_archive(query, cat)
    return search_nova(engine, query, cat)


def score(r):
    # downloads count on a log scale so archive.org/nyaa totals don't swamp live seeds
    base = max(r["seeds"], 0) + 0.25 * max(r["leech"], 0) + 10 * math.log10(1 + (r["downloads"] or 0))
    return round(base * TRUST_WEIGHT.get(r["trust"], 1.0), 1)


def merge(results):
    best = {}
    for r in results:
        m = re.search(r"btih:([A-Za-z0-9]+)", r["link"])
        key = m.group(1).lower() if m else r["link"]
        if key not in best or score(r) > score(best[key]):
            best[key] = r
    rows = list(best.values())
    for r in rows:
        r["score"] = score(r)
    return sorted(rows, key=lambda r: r["score"], reverse=True)


def human(n):
    if n < 0:
        return "?"
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def installed_engines():
    files = os.listdir(os.path.join(NOVA_DIR, "engines")) if os.path.isdir(NOVA_DIR) else []
    nova = sorted(f[:-3] for f in files if f.endswith(".py") and f not in ("__init__.py", "jackett.py", "piratebay.py"))
    return list(NATIVE) + [e for e in nova if e not in NATIVE]


def resolve_host(engine):
    """Host of the engine's own site if it can turn page links into magnets, else "".

    Engines without download_torrent make nova2dl download any URL to a temp file, and
    download_torrent fetches whatever link it gets: both are SSRF unless the host is pinned.
    """
    if not ENGINE_RE.fullmatch(engine) or engine in NATIVE:
        return ""
    path = os.path.join(NOVA_DIR, "engines", engine + ".py")
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            src = f.read()
    except OSError:
        return ""
    m = re.search(r"""^\s*url\s*(?::\s*str\s*)?=\s*['"](https?://[^'"]+)""", src, re.M)
    if "def download_torrent" not in src or not m:
        return ""
    return urllib.parse.urlparse(m.group(1)).hostname or ""


def resolve_magnet(engine, link):
    """Return a validated magnet for a result link, or "" if it can't be resolved safely."""
    if link.startswith("magnet:"):
        return link if MAGNET_RE.fullmatch(link) else ""
    host = resolve_host(engine)
    if not host or not link.startswith(("http://", "https://")) or urllib.parse.urlparse(link).hostname != host:
        return ""
    try:
        proc = subprocess.run(
            child_cmd("dl", engine, link),
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60,
        )
    except subprocess.TimeoutExpired:
        return ""
    out = proc.stdout.strip().split(" ")[0]
    return out if MAGNET_RE.fullmatch(out) else ""


def save_last(report):
    try:
        os.makedirs(os.path.dirname(LAST_RESULTS), exist_ok=True)
        flat = [r for rows in report.values() for r in rows]
        with open(LAST_RESULTS, "w", encoding="utf-8") as f:
            json.dump(flat, f, ensure_ascii=False)
    except OSError:
        pass


def open_result(n):
    """Open result N of the last search. Takes only an integer so no result text ever reaches a shell."""
    try:
        with open(LAST_RESULTS, encoding="utf-8") as f:
            rows = json.load(f)
        r = rows[n - 1]
    except (OSError, ValueError, IndexError):
        sys.exit(f"no result {n} in last search")
    if r["link"].endswith(".torrent") and r["link"].startswith("https://archive.org/download/"):
        target = r["link"]
    else:
        target = resolve_magnet(r["engine"], r["link"])
    if not target:
        sys.exit(f"result {n}: link could not be validated, not opening")
    if os.name == "nt":
        os.startfile(target)
    else:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", target], check=False)
    print(f"opened: {r['name']}")


def main():
    global ENGINE_TIMEOUT
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252; names can be Cyrillic etc.
    if len(sys.argv) == 4 and sys.argv[1] == "--magnet":
        print(resolve_magnet(sys.argv[2], sys.argv[3]) or "could not resolve a valid magnet")
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--open":
        open_result(int(sys.argv[2]))
        return
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--cat", default="all")
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--engines", default=DEFAULT_ENGINES)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--timeout", type=int, default=ENGINE_TIMEOUT, help="seconds per engine")
    args = ap.parse_args()
    ENGINE_TIMEOUT = args.timeout

    engines = [e.strip() for e in args.engines.split(",") if e.strip()]
    jobs = [(q, e) for q in args.queries for e in engines]
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        futures = [(q, pool.submit(run_engine, e, q, args.cat)) for q, e in jobs]
    by_query = {q: [] for q in args.queries}
    for q, f in futures:
        by_query[q].extend(f.result())

    report = {q: merge(rs)[: args.top] for q, rs in by_query.items()}
    save_last(report)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
        return
    # numbering is global across queries so --open N matches the saved list
    i = 0
    for q, rows in report.items():
        print(f"=== {q}")
        if not rows:
            print("(no results)")
        for r in rows:
            i += 1
            extra = "".join(f" {x}" for x in (r["trust"].upper() if r["trust"] else "",
                                              f"{r['downloads']}dl" if r["downloads"] is not None else "") if x)
            print(f"{i}. [score {r['score']}] {r['seeds']}S/{r['leech']}L {human(r['size'])}{extra}"
                  f" | {r['name']} ({r['engine']})")
            print(f"   {r['link']}")


if __name__ == "__main__":
    main()

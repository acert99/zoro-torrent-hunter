"""Local browser UI for torrent_search: every engine queried in parallel, results stream in.

Usage: python -I web.py [--port 8765] [--timeout 30] [--no-browser]
Listens on 127.0.0.1 only. Requests from other sites (CSRF) and other Host names (DNS rebinding)
are rejected, and only links this server returned can be resolved to magnets (no SSRF).
"""
import argparse
import json
import os
import sys
import threading
import time
import urllib.parse
import webbrowser
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import torrent_search as ts  # noqa: E402

STATIC = {"/": ("ui.html", "text/html; charset=utf-8"), "/ui.js": ("ui.js", "text/javascript; charset=utf-8"),
          "/logo-dark.png": (os.path.join("assets", "logo-dark.png"), "image/png"),
          "/logo-light.png": (os.path.join("assets", "logo-light.png"), "image/png"),
          "/favicon.ico": (os.path.join("assets", "icon.ico"), "image/x-icon")}
CATS = ("all", "movies", "tv", "music", "games", "anime", "software", "books")
MAX_QUERY = 200
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; "
                               "connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'self'; "
                               "frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}

WORKERS = threading.BoundedSemaphore(32)  # caps concurrent engine subprocesses
SEEN_LOCK = threading.Lock()
SEEN = OrderedDict()  # (engine, link) pairs this server returned; only these may be resolved
SEEN_MAX = 20000


def remember(engine, rows):
    with SEEN_LOCK:
        for r in rows:
            SEEN[(engine, r["link"])] = True
            SEEN.move_to_end((engine, r["link"]))
        while len(SEEN) > SEEN_MAX:
            SEEN.popitem(last=False)


class Handler(BaseHTTPRequestHandler):
    timeout = 15  # drop slow/idle clients (slowloris)
    allowed_hosts = set()

    def log_message(self, *args):
        pass

    def send(self, code, body, ctype="application/json; charset=utf-8"):
        data = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        for k, v in SECURITY_HEADERS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def trusted(self, path):
        if self.headers.get("Host", "") not in self.allowed_hosts:
            return False  # DNS rebinding: evil.com resolving to 127.0.0.1
        origin = self.headers.get("Origin")
        if origin and urllib.parse.urlparse(origin).netloc not in self.allowed_hosts:
            return False  # cross-site fetch/form
        if path == "/" and self.headers.get("Sec-Fetch-Mode", "navigate") == "navigate":
            return True  # opening the page from a bookmark/other tab is fine; framing is blocked by CSP
        return self.headers.get("Sec-Fetch-Site", "same-origin") in ("same-origin", "none")

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        if not self.trusted(url.path):
            print(f"403 {self.path} host={self.headers.get('Host')} origin={self.headers.get('Origin')} "
                  f"site={self.headers.get('Sec-Fetch-Site')}", file=sys.stderr)
            return self.send(403, {"error": "forbidden"})
        q = {k: v[0] for k, v in urllib.parse.parse_qs(url.query).items()}
        if url.path in STATIC:
            name, ctype = STATIC[url.path]
            with open(os.path.join(ts.HERE, name), "rb") as f:
                return self.send(200, f.read(), ctype)
        if url.path == "/api/engines":
            return self.send(200, {"engines": ts.installed_engines(),
                                   "default": ts.DEFAULT_ENGINES.split(","), "cats": CATS})
        if url.path in ("/api/search", "/api/magnet"):
            if not WORKERS.acquire(blocking=False):
                return self.send(503, {"error": "busy"})
            try:
                return self.search(q) if url.path == "/api/search" else self.magnet(q)
            finally:
                WORKERS.release()
        self.send(404, {"error": "not found"})

    def do_POST(self):
        self.send(405, {"error": "method not allowed"})

    def search(self, q):
        engine, query, cat = q.get("engine", ""), q.get("q", "").strip(), q.get("cat", "all")
        if engine not in ts.installed_engines() or not query or len(query) > MAX_QUERY or cat not in CATS:
            return self.send(400, {"error": "bad request"})
        start = time.time()
        try:
            rows, err = ts.dispatch(engine, query, cat), ""
        except Exception as e:
            print(f"[{engine}] {type(e).__name__}: {e}", file=sys.stderr)
            rows, err = [], "site falhou ou fora do ar"
        for r in rows:
            r["score"] = ts.score(r)
        remember(engine, rows)
        self.send(200, {"engine": engine, "rows": rows, "error": err, "ms": int((time.time() - start) * 1000)})

    def magnet(self, q):
        engine, link = q.get("engine", ""), q.get("link", "")
        with SEEN_LOCK:
            known = (engine, link) in SEEN
        if not known:
            return self.send(400, {"error": "unknown link"})
        out = ts.resolve_magnet(engine, link)
        self.send(200, {"magnet": out, "error": "" if out else "não foi possível obter o magnet"})


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--child":
        return ts.run_child(sys.argv[2:])
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--timeout", type=int, default=30, help="seconds per engine")
    ap.add_argument("--no-browser", action="store_true")
    args = ap.parse_args()
    ts.ENGINE_TIMEOUT = args.timeout
    Handler.allowed_hosts = {f"127.0.0.1:{args.port}", f"localhost:{args.port}"}
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    url = f"http://127.0.0.1:{args.port}/"
    print(f"Zoro - O caçador de Torrents em {url}  (Ctrl+C para sair)")
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()

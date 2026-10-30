"""Download the qBittorrent nova3 runtime and search plugins into vendor/nova3.

Usage:
  python -I setup.py              # download pinned files, refuse any whose sha256 doesn't match
  python -I setup.py --rehash     # after bumping a commit in SOURCES: print new hashes to paste below

Plugins are third-party Python that runs with your user's privileges, so every file is pinned to a
commit and checked against a sha256. To update one: review the new code, bump its commit, --rehash.
"""
import hashlib
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))

# Windows cert stores can hold stale roots ("certificate has expired"); prefer certifi's bundle.
# Set in os.environ so nova2 subprocesses inherit it too.
try:
    import certifi
    os.environ.setdefault("SSL_CERT_FILE", certifi.where())
except ImportError:
    pass

NOVA_DIR = os.path.join(HERE, "vendor", "nova3")
ENGINES_DIR = os.path.join(NOVA_DIR, "engines")

GH = "https://raw.githubusercontent.com/"
QBT = GH + "qbittorrent/qBittorrent/f6cf56c5fd85ce32c1af54566d43bb476dbcc4cd/src/searchengine/nova3/"
OFFICIAL = GH + "qbittorrent/search-plugins/42809399050293dc94ad25d7ac090a24649f9580/nova3/engines/"
LD = GH + "LightDestory/qBittorrent-Search-Plugins/0d3b18677c6f059031149abc7c2f46e994354298/src/engines/"

# (destination relative to vendor/nova3, url, sha256)
# Unofficial plugins come from https://github.com/qbittorrent/search-plugins/wiki/Unofficial-search-plugins;
# all 73 public-site ones were tested on 2026-10-28 and these returned results.
SOURCES = (
    ("nova2.py", QBT + "nova2.py", "63e0774bf46759fb7913e0465acf8524ac3b0e4b4a183bc677449e29ecf3e098"),
    ("nova2dl.py", QBT + "nova2dl.py", "233149d6265d8300156a5846d8cd57638e43d97d03344650f192365b1e4e6d5f"),
    ("helpers.py", QBT + "helpers.py", "bd438096c1f3d0ad404cda442c9f7d2646adae14c98a937885c3c1fb5237f856"),
    ("novaprinter.py", QBT + "novaprinter.py", "e503109129b9bbe3efaab67e6196602c977f2a9bf824cc914e7f753f8dfc5636"),
    ("socks.py", QBT + "socks.py", "80af424d5bf0271e23f27328e34909a28d2fbdc01f1575da6c02ade64bbd3002"),
    ("engines/limetorrents.py", OFFICIAL + "limetorrents.py", "aca3fbc4956970474a66295f5e61f02532bcdf5399ae97c144bf826a7c8fddce"),
    ("engines/torrentscsv.py", OFFICIAL + "torrentscsv.py", "7c7c8a54249e5f2ce237df6421a735a5c1bd7acefd1304d736ee8f925fd6031b"),
    ("engines/rutor.py", GH + "imDMG/qBt_SE/a53fe22e8810c65a45cde8ccf4b61fa2647bf7e2/engines/rutor.py", "1cf9c5c302ad8defbe6ddb90bcbdf56cc905b49517b9233618b0f5a252845913"),
    ("engines/pirateiro.py", LD + "pirateiro.py", "eb71a8f5e9cd05b5e469193cc5960c2ba9c109fafc8498752c868e1dabe26f15"),
    ("engines/academictorrents.py", LD + "academictorrents.py", "5a4e025814e1fc8ae97a6c267fb706e03976fef1b629cb63eeb9944ebd9b49d3"),
    ("engines/yts.py", "https://codeberg.org/lazulyra/qbit-plugins/raw/commit/2537f6ddeeea10a8580c1ff0a49769941c5edc38/yts/yts.py", "cb066319b5f6092621b21debc4303d937bacd2bdaef643f1740a516145cbfb9e"),
    ("engines/animetosho.py", GH + "Phlexis96/qBitTorrent-animetosho-search-plugin/beaf4808db7454a5d0c4528cece5ee0e629eaa04/animetosho.py", "78af019cbf2c0b315f2c6b877541ea40483e4c48209b06f9d4c9e9941cfef6d9"),
    ("engines/sktorrent.py", GH + "Ashalda/sktorrent-qbt/2c88a66408ae98f4544fd4fe4081a4f201205a36/sktorrent.py", "a917b482741a0b301f09ce0c1edbfe5d7b4663c2367ede1a1bcde2641d62e28c"),
)


def download(url):
    with urllib.request.urlopen(url, timeout=30) as r:
        return r.read()


def main():
    rehash = "--rehash" in sys.argv
    os.makedirs(ENGINES_DIR, exist_ok=True)
    for d in (NOVA_DIR, ENGINES_DIR):
        open(os.path.join(d, "__init__.py"), "a").close()
    failed = 0
    for dest, url, expected in SOURCES:
        data = download(url)
        digest = hashlib.sha256(data).hexdigest()
        if rehash:
            print(f'{dest} {digest}')
            continue
        if digest != expected:
            print(f"REFUSED {dest}: sha256 {digest} != pinned {expected}", file=sys.stderr)
            failed += 1
            continue
        with open(os.path.join(NOVA_DIR, dest), "wb") as f:
            f.write(data)
        print("ok", dest)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

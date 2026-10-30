"""Run one nova3 engine without nova2.py's multiprocessing (slow to spawn on Windows).

Usage: python -I run_engine.py NOVA_DIR ENGINE CATEGORY QUERY
Prints novaprinter lines (link|name|size|seeds|leech|engine_url|...) to stdout.
"""
import importlib
import sys
import urllib.parse


def main():
    nova_dir, engine, cat, query = sys.argv[1:5]
    sys.path.insert(0, nova_dir)
    mod = importlib.import_module("engines." + engine)
    plugin = getattr(mod, engine)()
    if cat not in getattr(plugin, "supported_categories", {"all": ""}):
        return
    plugin.search(urllib.parse.quote(query), cat)


if __name__ == "__main__":
    main()

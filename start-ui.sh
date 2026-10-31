#!/bin/sh
# Zoro - O cacador de Torrents: local browser UI (http://127.0.0.1:8765)
exec python3 -I "$(dirname "$0")/web.py" "$@"

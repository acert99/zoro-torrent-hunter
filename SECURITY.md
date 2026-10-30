# Security

## Pentest 2026-10-28

The test combined a white-box code review with a live black-box attack on the local server. Every finding below was fixed and then re-tested.

| # | Severity | Finding | Fix | Re-test |
|---|---|---|---|---|
| 1 | high | **Drive-by SSRF**: any website could call `/api/magnet` and make the server fetch arbitrary URLs (LAN, router, `169.254.169.254`). The `nova2dl` fallback also wrote the response to a temp file. | `/api/magnet` only resolves `(engine, link)` pairs this server returned from a search. The link host must match the engine's own site, and engines without `download_torrent` are refused. | a listener on 127.0.0.1:9999 received 0 hits |
| 2 | high | **DNS rebinding / CSRF**: no `Host` or `Origin` check. | `Host` allowlist (`127.0.0.1:PORT`, `localhost:PORT`). Requests with a foreign `Origin` or `Sec-Fetch-Site: cross-site` are rejected; top-level navigation to `/` is the only exception. | 403 |
| 3 | high | **Supply chain**: plugins were fetched from `master`/`main` with no integrity check, and they run with your user's privileges. | Each file is pinned to a commit and a sha256 in `setup.py`, and a mismatch is refused. The 4 dead official plugins were dropped. | 13/13 ok, identical to the reviewed copies |
| 4 | high | **Command / prompt injection via the skill**: the LLM built `Start-Process "magnet..."` from untrusted result text. | `torrent_search.py --open N` takes only an integer and validates the magnet (`MAGNET_RE`) before calling `os.startfile`. The skill now treats result text as data and forbids shell commands built from it. | `$(...)` and `"; cmd` payloads rejected |
| 5 | med | **DOM XSS**: `javascript:` links from plugins went straight into `href`. | `safeUrl()` allows only `magnet:?` and `http(s)://`. The JS moved to `ui.js`, under CSP `script-src 'self'` (no inline scripts). Also added `frame-ancestors 'none'`, `nosniff` and `no-referrer`. | `javascript:`, `data:` and mixed-case variants blocked |
| 6 | med | **DoS**: unbounded threads and subprocesses, no socket timeout. | `BoundedSemaphore(32)` returns 503 when full, `Handler.timeout = 15`, query limited to 200 chars. | 60 parallel requests: 43 ok, 17 got 503 |
| 7 | med | **Info leak**: tracebacks and temp paths were returned to the client. | The client gets a generic error; details are logged to stderr only. | ok |
| 8 | low | `--engines` / `engine` could import arbitrary modules. | `ENGINE_RE` check plus membership in `installed_engines()`. | `../../x` returns 400 |
| 9 | low | Engine names were not escaped in the UI. | `esc()` applied. | ok |

## Remaining trust assumptions

- Search plugins are third-party Python and run with your privileges. This is the same model qBittorrent itself uses. Review the code before bumping a commit in `setup.py`.
- The server binds to `127.0.0.1` only. Don't expose it on a LAN.

## Reporting a vulnerability

Please do not open a public issue. Use [private vulnerability reporting](https://github.com/acert99/zoro-torrent-hunter/security/advisories/new).

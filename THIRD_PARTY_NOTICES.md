# Third-party notices

Zoro's own code is MIT (see `LICENSE`). The Windows build also ships the third-party components below, which keep their own licenses. Full texts are in `licenses/`.

The plugin `.py` files ship unmodified and in source form inside the app, under `_internal/vendor/nova3/`. Each one is pinned by commit and sha256 in `setup.py`, and runs in its own process.

## Search runtime and plugins

| File | License | Copyright / authors | Upstream | Commit |
|---|---|---|---|---|
| `nova2.py`, `nova2dl.py`, `helpers.py`, `novaprinter.py`, `socks.py` | BSD-style, see `licenses/BSD-qBittorrent-nova3.txt` | Fabien Devaux, Christophe Dumez and contributors; Dan Haim (`socks.py`) | [qbittorrent/qBittorrent](https://github.com/qbittorrent/qBittorrent) | `f6cf56c5fd85ce32c1af54566d43bb476dbcc4cd` |
| `engines/torrentscsv.py` | BSD-style, see `licenses/BSD-qBittorrent-nova3.txt` | Dessalines | [qbittorrent/search-plugins](https://github.com/qbittorrent/search-plugins) | `42809399050293dc94ad25d7ac090a24649f9580` |
| `engines/limetorrents.py` | GPL-2.0 (repository license), see `licenses/GPL-2.0.txt` | Lima66, Diego de las Heras | [qbittorrent/search-plugins](https://github.com/qbittorrent/search-plugins) | `42809399050293dc94ad25d7ac090a24649f9580` |
| `engines/rutor.py` | MIT, see `licenses/MIT-qBt_SE.txt` | imDMG | [imDMG/qBt_SE](https://github.com/imDMG/qBt_SE) | `a53fe22e8810c65a45cde8ccf4b61fa2647bf7e2` |
| `engines/pirateiro.py` | GPL-3.0 (repository license), see `licenses/GPL-3.0.txt` | LightDestory, YoWhatupGee | [LightDestory/qBittorrent-Search-Plugins](https://github.com/LightDestory/qBittorrent-Search-Plugins) | `0d3b18677c6f059031149abc7c2f46e994354298` |
| `engines/academictorrents.py` | GPL-3.0 (repository license), see `licenses/GPL-3.0.txt` | LightDestory, achernet | [LightDestory/qBittorrent-Search-Plugins](https://github.com/LightDestory/qBittorrent-Search-Plugins) | `0d3b18677c6f059031149abc7c2f46e994354298` |
| `engines/animetosho.py` | GPL-3.0-or-later (file header), see `licenses/GPL-3.0.txt` | ALAA_BRAHIM, phlexis96 | [Phlexis96/qBitTorrent-animetosho-search-plugin](https://github.com/Phlexis96/qBitTorrent-animetosho-search-plugin) | `beaf4808db7454a5d0c4528cece5ee0e629eaa04` |

## Plugins without a license

These two files declare no license, so their authors have **not** granted permission to redistribute them. They are included for now, and permission is being requested from each author. Zoro does not claim any license over them.

| File | Author | Upstream | Commit | Status |
|---|---|---|---|---|
| `engines/yts.py` | Lyra Aranha | [codeberg.org/lazulyra/qbit-plugins](https://codeberg.org/lazulyra/qbit-plugins) | `2537f6ddeeea10a8580c1ff0a49769941c5edc38` | no license, permission to be requested |
| `engines/sktorrent.py` | Ashalda | [Ashalda/sktorrent-qbt](https://github.com/Ashalda/sktorrent-qbt) | `2c88a66408ae98f4544fd4fe4081a4f201205a36` | no license, permission to be requested |

If you are one of these authors and want your file removed, open an issue and it will be taken out of the build.

## Runtime bundled by PyInstaller

| Component | License | Text |
|---|---|---|
| CPython 3.12.10 | PSF-2.0 | `licenses/Python.txt` |
| Components inside CPython's Windows build (zlib, expat, libmpdec, bzip2, libffi and others) | their own permissive licenses | `licenses/Python-bundled-components.txt`, `licenses/Python.txt` |
| OpenSSL 3.0.16 | Apache-2.0 | `licenses/Apache-2.0.txt` |
| Microsoft Visual C++ and Universal C runtime DLLs | Microsoft redistributable terms | `licenses/Python.txt` |
| PyInstaller 6.22.3 bootloader | GPL-2.0 with a bootloader exception | `licenses/PyInstaller.txt` |
| certifi 2026.07.22 (Mozilla CA bundle) | MPL-2.0 | `licenses/MPL-2.0.txt`, `licenses/MPL-2.0-certifi.txt` |

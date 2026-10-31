# Contribuindo com o Zoro

Toda ajuda é bem-vinda: código, testes, tradução, design, documentação ou um bom relato de bug. English is fine too.

## Rodar localmente

```bash
git clone https://github.com/acert99/zoro-torrent-hunter
cd zoro-torrent-hunter
pip install certifi
python -I setup.py     # baixa os plugins fixados para vendor/
python -I web.py       # abre http://127.0.0.1:8765
```

Testes (sem rede, sem plugins):

```bash
python -m unittest discover -s tests
```

## Mapa do código

| Arquivo | Função |
|---|---|
| `torrent_search.py` | núcleo e CLI: busca, ranking, merge por infohash |
| `web.py` | servidor local e API (`/api/engines`, `/api/search`, `/api/magnet`) |
| `ui.html`, `ui.js` | interface, sem framework e sem build |
| `run_engine.py` | roda um plugin nova3 em processo próprio |
| `setup.py` | lista de plugins fixados por commit e sha256 |
| `build.py`, `installer.iss` | exe (PyInstaller) e instalador (Inno Setup) |

## Regras do projeto

1. **Segurança primeiro.** O servidor escuta só em `127.0.0.1`. Não enfraqueça a checagem de Host/Origin, a CSP nem a allowlist de links. Veja [SECURITY.md](SECURITY.md).
2. **Resultado de site é dado não confiável.** No `ui.js`, todo texto vindo de site passa por `esc()` e todo link por `safeUrl()`.
3. **Plugin novo** entra em `SOURCES` no `setup.py`, com commit e sha256 (`python -I setup.py --rehash`). Leia o código do plugin antes de propor.
4. **Sem dependências novas** sem motivo forte. A interface continua sem framework.
5. **Conteúdo legal.** Exemplos, testes e prints usam distros Linux, domínio público ou obras liberadas. PRs e issues não devem pedir nem conter links para material pirata.

## Pull request

1. Crie um branch a partir de `main`.
2. Faça uma mudança por PR.
3. Rode os testes, teste a busca no navegador e descreva o que testou.
4. Use commits no formato [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`).

Vulnerabilidade de segurança não vai em issue pública: siga o [SECURITY.md](SECURITY.md).

# Línia d'ordres

```text
uv run horizon-mcp [opcions]
```

| Opció | Valor | Descripció |
|---|---|---|
| `--transport` | `stdio` (per defecte) \| `streamable-http` | `stdio` per a clients locals (Claude Desktop, Claude Code); `streamable-http` per a un servei compartit. |
| `--host` | `127.0.0.1` | Adreça d'escolta en mode HTTP. |
| `--port` | `8000` | Port d'escolta en mode HTTP. L'endpoint és `/mcp`. |
| `--allow-unauthenticated` | — | Només HTTP: arrenca en una adreça no loopback sense `HORIZON_MCP_BEARER_TOKEN`. Només darrere d'un proxy que ja autentiqui. |
| `--log-level` | `INFO` (`DEBUG`, `WARNING`, `ERROR`) | Nivell de registre per `stderr`. Amb `DEBUG` es veu cada petició HTTP a HORIZON. |
| `--check` | — | Valida la configuració i surt, sense cap crida. |
| `--ping` | — | Crida HORIZON (arrel, compte, inventari) per verificar clau i connectivitat, i surt. |
| `--version` | — | Mostra la versió. |

## Codis de sortida

| Codi | Quan |
|---|---|
| `0` | Tot correcte (o el servidor ha acabat normalment). |
| `1` | `--ping` ha fallat en parlar amb HORIZON. |
| `2` | Error de configuració (clau absent, valor no numèric) o mode HTTP refusat per falta d'autenticació. |

En `stdio`, el protocol viatja per `stdout`: tots els missatges del servidor van per
`stderr`.

## Altres ordres del projecte

```bash
uv run mcp dev inspector.py   # MCP Inspector (requereix Node.js)
uv run pytest                 # tests; no toquen HORIZON
```

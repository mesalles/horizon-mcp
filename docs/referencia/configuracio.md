# Configuració

Tot es configura per variables d'entorn, directament o a través d'un fitxer `.env`. El
servidor carrega el `.env` de l'arrel del projecte o, si no hi és, del directori actual; una
variable d'entorn real sempre té prioritat sobre el fitxer.

| Variable | Per defecte | Descripció |
|---|---|---|
| `HORIZON_API_KEY` | — | **Obligatòria.** Clau d'API del compte d'HORIZON. |
| `HORIZON_API_URL` | `https://api.horizon.delta90.com` | URL base de l'API. |
| `HORIZON_TIMEOUT` | `60` | Segons d'espera màxima per petició. |
| `HORIZON_MIN_INTERVAL` | `0.5` | Segons mínims entre dues peticions a HORIZON (ritme amable amb l'API). |
| `HORIZON_MAX_ROWS` | `200` | Files per defecte de les eines de llista; el màxim absolut que es pot demanar amb `limit` és 1.000. |
| `HORIZON_MCP_BEARER_TOKEN` | — | Només en mode `streamable-http`: secret que els clients han d'enviar com a `Authorization: Bearer …`. Sense ell, el servidor no escolta en adreces que no siguin loopback. |
| `HORIZON_USER_AGENT` | `horizon-mcp/<versió> (+https://github.com/mesalles/horizon-mcp)` | *User-Agent* de les peticions. HORIZON és darrere de Cloudflare, que bloqueja el *User-Agent* per defecte de les biblioteques HTTP (error 1010). El valor per defecte està verificat; un de navegador també passa. |

Valors fixos (no configurables per entorn): pàgines de 1.000 files en la paginació, prefix
IPv4 mínim /16, màxim de 4 adreces per nom de host.

## Exemple de `.env`

```bash
HORIZON_API_KEY=<la clau>
# HORIZON_TIMEOUT=60
# HORIZON_MIN_INTERVAL=0.5
# HORIZON_MAX_ROWS=200
# HORIZON_MCP_BEARER_TOKEN=
# HORIZON_USER_AGENT=
```

El `.env` és al `.gitignore`. Mai posis la clau real en cap fitxer que es pugi al repositori.

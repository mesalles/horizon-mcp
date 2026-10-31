# Diagnosticar problemes

Els errors del servidor arriben al model com a dades (`{"error": "…"}`), perquè pugui
explicar-los en lloc de trencar el torn. Els mateixos missatges surten a `--ping` i als
registres (`stderr`).

## Per missatge

| Missatge | Causa | Què fer |
|---|---|---|
| `HORIZON_API_KEY is not set` | No hi ha clau ni al `.env` ni a l'entorn | Revisa on és el `.env` (arrel del projecte o directori actual) |
| `HORIZON rejected the API key (HTTP 401)` | Clau incorrecta o caducada | Torna-la a copiar d'HORIZON (**Mi perfil → Información**) |
| `HORIZON's WAF (Cloudflare) blocked the request with HTTP 403` | El tallafoc d'HORIZON rebutja el *User-Agent* (error 1010) o la IP | Defineix `HORIZON_USER_AGENT` amb un valor de navegador (n'hi ha un a `.env.example`); si persisteix, pot ser un bloqueig per IP |
| `HORIZON rejected the parameters (HTTP 422)` | Paràmetre que l'API no accepta | Normalment un objectiu mal format que ha passat la validació; revisa'l |
| `network error calling HORIZON` | Sense xarxa, proxy, DNS | Comprova la sortida cap a `api.horizon.delta90.com` i `HORIZON_TIMEOUT` |
| `HORIZON returned an error for …` | L'API ha respost `ok: false` | El text de l'error ve d'HORIZON; sovint és un compte sense dades per a aquest objectiu |
| `… is not an IP address or CIDR` | Objectiu no vàlid | IP, CIDR (/16 o més estret) o nom de host |
| `prefix /N is too wide` | CIDR més ample que /16 | Estreny-lo |
| `… does not resolve` | El nom no resol a la màquina del servidor | DNS intern, nom mal escrit; resol-lo tu i passa la IP |
| `… resolves to N addresses` | Més de 4 adreces | Consulta les IP d'una en una |
| `refusing to listen on …` | Mode HTTP en adreça no loopback sense token | Vegeu [Servei compartit (HTTP)](servei-compartit.md) |

## Veure què passa per sota

```bash
uv run horizon-mcp --log-level DEBUG --ping
```

Amb `DEBUG`, cada petició HTTP a HORIZON surt per `stderr` (ruta i paràmetres, mai la clau).
En un client MCP, els registres del servidor són els de `stderr`: Claude Desktop els guarda
a la seva carpeta `logs`; Claude Code els mostra a `/mcp`.

## Lentitud

- El servidor espera com a mínim 0,5 s entre dues peticions a HORIZON
  (`HORIZON_MIN_INTERVAL`) per no saturar l'API. Un `/24` amb molts serveis i diverses
  pàgines de 1.000 files triga uns segons.
- `exposure_summary` fa cinc consultes (ports, HTTP, CVE, web, TLS) sense truncar: és normal
  que trigui més que una eina de llista.
- `recent_changes` fa una consulta extra d'HTTP només si hi ha serveis web nous.

## Com saber que ha funcionat

- `--ping` acaba amb `status=ok` i el client torna a mostrar les eines.

## Si falla

- Si després d'aquestes comprovacions l'error persisteix, obre una issue al repositori amb
  el missatge exacte, el valor de `--log-level DEBUG` **sense la clau ni dades reals
  d'exposició**, i la versió (`--version`).

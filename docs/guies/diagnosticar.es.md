# Diagnosticar problemas

Los errores del servidor llegan al modelo como datos (`{"error": "…"}`), para que pueda
explicarlos en lugar de romper el turno. Los mismos mensajes salen en `--ping` y en los
registros (`stderr`).

## Por mensaje

| Mensaje | Causa | Qué hacer |
|---|---|---|
| `HORIZON_API_KEY is not set` | No hay clave ni en el `.env` ni en el entorno | Revisa dónde está el `.env` (raíz del proyecto o directorio actual) |
| `HORIZON rejected the API key (HTTP 401)` | Clave incorrecta o caducada | Vuelve a copiarla de HORIZON (**Mi perfil → Información**) |
| `HORIZON's WAF (Cloudflare) blocked the request with HTTP 403` | El cortafuegos de HORIZON rechaza el *User-Agent* (error 1010) o la IP | Define `HORIZON_USER_AGENT` con un valor de navegador (hay uno en `.env.example`); si persiste, puede ser un bloqueo por IP |
| `HORIZON rejected the parameters (HTTP 422)` | Parámetro que la API no acepta | Normalmente un objetivo mal formado que ha pasado la validación; revísalo |
| `network error calling HORIZON` | Sin red, proxy, DNS | Comprueba la salida hacia `api.horizon.delta90.com` y `HORIZON_TIMEOUT` |
| `HORIZON returned an error for …` | La API ha respondido `ok: false` | El texto del error viene de HORIZON; a menudo es una cuenta sin datos para ese objetivo |
| `… is not an IP address or CIDR` | Objetivo no válido | IP, CIDR (/16 o más estrecho) o nombre de host |
| `prefix /N is too wide` | CIDR más ancho que /16 | Estréchalo |
| `… does not resolve` | El nombre no resuelve en la máquina del servidor | DNS interno, nombre mal escrito; resuélvelo tú y pasa la IP |
| `… resolves to N addresses` | Más de 4 direcciones | Consulta las IP de una en una |
| `refusing to listen on …` | Modo HTTP en dirección no loopback sin token | Véase [Servicio compartido (HTTP)](servei-compartit.md) |

## Ver qué pasa por debajo

```bash
uv run horizon-mcp --log-level DEBUG --ping
```

Con `DEBUG`, cada petición HTTP a HORIZON sale por `stderr` (ruta y parámetros, nunca la
clave). En un cliente MCP, los registros del servidor son los de `stderr`: Claude Desktop los
guarda en su carpeta `logs`; Claude Code los muestra en `/mcp`.

## Lentitud

- El servidor espera como mínimo 0,5 s entre dos peticiones a HORIZON
  (`HORIZON_MIN_INTERVAL`) para no saturar la API. Un `/24` con muchos servicios y varias
  páginas de 1.000 filas tarda unos segundos.
- `exposure_summary` hace cinco consultas (puertos, HTTP, CVE, web, TLS) sin truncar: es
  normal que tarde más que una herramienta de lista.
- `recent_changes` hace una consulta extra de HTTP solo si hay servicios web nuevos.

## Cómo saber que ha funcionado

- `--ping` termina con `status=ok` y el cliente vuelve a mostrar las herramientas.

## Si falla

- Si tras estas comprobaciones el error persiste, abre una issue en el repositorio con el
  mensaje exacto, la salida de `--log-level DEBUG` **sin la clave ni datos reales de
  exposición**, y la versión (`--version`).

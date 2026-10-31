# Configuración

Todo se configura por variables de entorno, directamente o a través de un archivo `.env`.
El servidor carga el `.env` de la raíz del proyecto o, si no está, del directorio actual;
una variable de entorno real siempre tiene prioridad sobre el archivo.

| Variable | Por defecto | Descripción |
|---|---|---|
| `HORIZON_API_KEY` | — | **Obligatoria.** Clave de API de la cuenta de HORIZON. |
| `HORIZON_API_URL` | `https://api.horizon.delta90.com` | URL base de la API. |
| `HORIZON_TIMEOUT` | `60` | Segundos de espera máxima por petición. |
| `HORIZON_MIN_INTERVAL` | `0.5` | Segundos mínimos entre dos peticiones a HORIZON (ritmo amable con la API). |
| `HORIZON_MAX_ROWS` | `200` | Filas por defecto de las herramientas de lista; el máximo absoluto que se puede pedir con `limit` es 1.000. |
| `HORIZON_MCP_BEARER_TOKEN` | — | Solo en modo `streamable-http`: secreto que los clientes deben enviar como `Authorization: Bearer …`. Sin él, el servidor no escucha en direcciones que no sean loopback. |
| `HORIZON_USER_AGENT` | `horizon-mcp/<versión> (+https://github.com/mesalles/horizon-mcp)` | *User-Agent* de las peticiones. HORIZON está detrás de Cloudflare, que bloquea el *User-Agent* por defecto de las bibliotecas HTTP (error 1010). El valor por defecto está verificado; uno de navegador también pasa. |

Valores fijos (no configurables por entorno): páginas de 1.000 filas en la paginación,
prefijo IPv4 mínimo /16, máximo de 4 direcciones por nombre de host.

## Ejemplo de `.env`

```bash
HORIZON_API_KEY=<la clave>
# HORIZON_TIMEOUT=60
# HORIZON_MIN_INTERVAL=0.5
# HORIZON_MAX_ROWS=200
# HORIZON_MCP_BEARER_TOKEN=
# HORIZON_USER_AGENT=
```

El `.env` está en el `.gitignore`. Nunca pongas la clave real en ningún archivo que se suba
al repositorio.

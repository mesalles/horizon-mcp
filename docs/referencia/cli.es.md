# Línea de comandos

```text
uv run horizon-mcp [opciones]
```

| Opción | Valor | Descripción |
|---|---|---|
| `--transport` | `stdio` (por defecto) \| `streamable-http` | `stdio` para clientes locales (Claude Desktop, Claude Code); `streamable-http` para un servicio compartido. |
| `--host` | `127.0.0.1` | Dirección de escucha en modo HTTP. |
| `--port` | `8000` | Puerto de escucha en modo HTTP. El endpoint es `/mcp`. |
| `--allow-unauthenticated` | — | Solo HTTP: arranca en una dirección no loopback sin `HORIZON_MCP_BEARER_TOKEN`. Solo detrás de un proxy que ya autentique. |
| `--log-level` | `INFO` (`DEBUG`, `WARNING`, `ERROR`) | Nivel de registro por `stderr`. Con `DEBUG` se ve cada petición HTTP a HORIZON. |
| `--check` | — | Valida la configuración y sale, sin ninguna llamada. |
| `--ping` | — | Llama a HORIZON (raíz, cuenta, inventario) para verificar clave y conectividad, y sale. |
| `--version` | — | Muestra la versión. |

## Códigos de salida

| Código | Cuándo |
|---|---|
| `0` | Todo correcto (o el servidor ha terminado normalmente). |
| `1` | `--ping` ha fallado al hablar con HORIZON. |
| `2` | Error de configuración (clave ausente, valor no numérico) o modo HTTP rechazado por falta de autenticación. |

En `stdio`, el protocolo viaja por `stdout`: todos los mensajes del servidor van por
`stderr`.

## Otros comandos del proyecto

```bash
uv run mcp dev inspector.py   # MCP Inspector (requiere Node.js)
uv run pytest                 # tests; no tocan HORIZON
```

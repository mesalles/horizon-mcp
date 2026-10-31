# Conectar Claude Code

Claude Code arranca el servidor por `stdio` en cada sesión. La configuración se registra una
vez con `claude mcp add`.

## Pasos

1. Registra el servidor para todas las sesiones de tu usuario:

    ```bash
    claude mcp add --transport stdio --scope user horizon -- uv run --directory /ruta/absoluta/a/horizon-mcp horizon-mcp
    ```

    Con `--scope project` en lugar de `user`, la configuración queda en el proyecto actual
    (archivo `.mcp.json`) y se comparte con quien lo clone.

2. Abre Claude Code y escribe `/mcp`: muestra el estado del servidor y las herramientas
   cargadas.

3. Pregunta en lenguaje natural; el modelo elige la herramienta. Para forzar una, nómbrala:
   «usa `recent_changes` sobre 192.0.2.0/24».

## Servicio compartido

Si el servidor corre como servicio HTTP del equipo (véase
[Servicio compartido (HTTP)](servei-compartit.md)), el cliente se registra con la dirección y
el token:

```bash
claude mcp add --transport http horizon https://vuestro-host/mcp --header "Authorization: Bearer <token>"
```

## Cómo saber que ha funcionado

- `/mcp` muestra `horizon` como conectado, con nueve herramientas.
- «¿Qué rangos vigila HORIZON?» devuelve los rangos de la cuenta.

## Si falla

- **`/mcp` muestra el servidor con error**: ejecuta el comando tal cual en un terminal (`uv
  run --directory <ruta> horizon-mcp --check`) para ver el mensaje.
- **Ruta con espacios**: ponla entre comillas en `claude mcp add`.
- **Quieres quitarlo o cambiarlo**: `claude mcp remove horizon` y vuelve a añadirlo.
- **El servicio HTTP responde 401**: el token de la cabecera no coincide con el del servidor
  (`HORIZON_MCP_BEARER_TOKEN`).

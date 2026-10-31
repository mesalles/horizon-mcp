# Conectar Claude Desktop

Claude Desktop arranca el servidor él mismo cada vez que se abre (transporte `stdio`) y lo
cierra al salir. No hace falta tener nada en marcha.

## Pasos

1. Localiza el archivo de configuración:
    - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
    - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Añade el servidor (o el bloque `mcpServers` entero si el archivo está vacío):

    === "macOS y Linux"

        ```json
        {
          "mcpServers": {
            "horizon": {
              "command": "uv",
              "args": ["run", "--directory", "/ruta/absoluta/a/horizon-mcp", "horizon-mcp"]
            }
          }
        }
        ```

    === "Windows"

        ```json
        {
          "mcpServers": {
            "horizon": {
              "command": "C:\\Users\\<usuario>\\.local\\bin\\uv.exe",
              "args": ["run", "--directory", "C:\\Users\\<usuario>\\horizon-mcp", "horizon-mcp"]
            }
          }
        }
        ```

        En Windows, `command` debe ser la **ruta absoluta de `uv.exe`**: la aplicación de
        escritorio no tiene el `PATH` de la consola. Las barras de las rutas van dobles.
        Para saber dónde está `uv.exe`: `where uv` en la consola.

3. Cierra Claude Desktop del todo (también de la bandeja del sistema) y vuelve a abrirlo.

4. Las herramientas aparecen en el selector de herramientas del chat (el icono de
   herramientas bajo el campo de texto).

## Cómo saber que ha funcionado

- El selector de herramientas lista `horizon` con nueve herramientas (`inventory`,
  `open_ports`, …).
- Pregunta «¿Qué rangos vigila HORIZON?» y el modelo llama a `inventory`.

## Si falla

- **El servidor no aparece**: el JSON tiene un error de sintaxis (una coma de más, comillas
  simples). Valídalo con un editor que marque JSON.
- **Aparece pero con error al arrancar**: la ruta de `--directory` no existe o `command` no
  es la ruta de `uv.exe`. Prueba el comando exacto en una consola: `uv run --directory
  <ruta> horizon-mcp --check`.
- **Error de clave**: el `.env` debe estar en la raíz de `horizon-mcp`. Si prefieres no
  tener archivo, añade `"env": {"HORIZON_API_KEY": "…"}` al bloque del servidor; entonces el
  secreto está en el archivo de configuración de Claude Desktop y hay que protegerlo igual.
- **Los registros**: Claude Desktop los guarda en la carpeta `logs` junto al archivo de
  configuración (`mcp-server-horizon.log`). El servidor escribe sus mensajes por `stderr`,
  que es lo que aparece ahí.

# Connectar Claude Desktop

Claude Desktop arrenca el servidor ell mateix cada vegada que s'obre (transport `stdio`) i
el tanca en sortir. No cal tenir res en marxa.

## Passos

1. Localitza el fitxer de configuració:
    - Windows: `%APPDATA%\Claude\claude_desktop_config.json`
    - macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`

2. Afegeix-hi el servidor (o el bloc `mcpServers` sencer si el fitxer és buit):

    === "macOS i Linux"

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
              "command": "C:\\Users\\<usuari>\\.local\\bin\\uv.exe",
              "args": ["run", "--directory", "C:\\Users\\<usuari>\\horizon-mcp", "horizon-mcp"]
            }
          }
        }
        ```

        A Windows, `command` ha de ser la **ruta absoluta d'`uv.exe`**: l'aplicació
        d'escriptori no té el `PATH` de la consola. Les barres de les rutes van dobles.
        Per saber on és `uv.exe`: `where uv` a la consola.

3. Tanca Claude Desktop del tot (també de la safata del sistema) i torna'l a obrir.

4. Les eines apareixen al selector d'eines del xat (la icona d'eines sota el camp de text).

## Com saber que ha funcionat

- El selector d'eines llista `horizon` amb nou eines (`inventory`, `open_ports`, …).
- Pregunta «Quins rangs vigila HORIZON?» i el model crida `inventory`.

## Si falla

- **El servidor no apareix**: el JSON té un error de sintaxi (una coma de més, cometes
  simples). Valida'l amb un editor que marqui JSON.
- **Apareix però amb error en arrencar**: la ruta de `--directory` no existeix o `command`
  no és la ruta d'`uv.exe`. Prova l'ordre exacta en una consola: `uv run --directory
  <ruta> horizon-mcp --check`.
- **Error de clau**: el `.env` ha de ser a l'arrel de `horizon-mcp`. Si prefereixes no
  tenir-hi fitxer, afegeix `"env": {"HORIZON_API_KEY": "…"}` al bloc del servidor; aleshores
  el secret és al fitxer de configuració de Claude Desktop, i cal protegir-lo igual.
- **Els registres**: Claude Desktop els guarda a la carpeta `logs` al costat del fitxer de
  configuració (`mcp-server-horizon.log`). El servidor escriu els seus missatges per
  `stderr`, que és el que hi surt.

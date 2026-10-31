# Connectar Claude Code

Claude Code arrenca el servidor per `stdio` a cada sessió. La configuració es registra una
vegada amb `claude mcp add`.

## Passos

1. Registra el servidor per a totes les sessions del teu usuari:

    ```bash
    claude mcp add --transport stdio --scope user horizon -- uv run --directory /ruta/absoluta/a/horizon-mcp horizon-mcp
    ```

    Amb `--scope project` en lloc de `user`, la configuració queda al projecte actual
    (fitxer `.mcp.json`) i es comparteix amb qui el cloni.

2. Obre Claude Code i escriu `/mcp`: mostra l'estat del servidor i les eines carregades.

3. Pregunta en llenguatge natural; el model tria l'eina. Per forçar-ne una, anomena-la:
   «fes servir `recent_changes` sobre 192.0.2.0/24».

## Servei compartit

Si el servidor corre com a servei HTTP de l'equip (vegeu
[Servei compartit (HTTP)](servei-compartit.md)), el client es registra amb l'adreça i el
token:

```bash
claude mcp add --transport http horizon https://el-vostre-host/mcp --header "Authorization: Bearer <token>"
```

## Com saber que ha funcionat

- `/mcp` mostra `horizon` com a connectat, amb nou eines.
- «Quins rangs vigila HORIZON?» torna els rangs del compte.

## Si falla

- **`/mcp` mostra el servidor amb error**: executa l'ordre tal qual en un terminal (`uv run
  --directory <ruta> horizon-mcp --check`) per veure el missatge.
- **Ruta amb espais**: posa-la entre cometes a `claude mcp add`.
- **Vols treure'l o canviar-lo**: `claude mcp remove horizon` i torna a afegir-lo.
- **El servei HTTP respon 401**: el token de la capçalera no coincideix amb el del servidor
  (`HORIZON_MCP_BEARER_TOKEN`).

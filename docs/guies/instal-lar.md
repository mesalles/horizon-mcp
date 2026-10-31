# Instal·lar

## Requisits

- Python ≥ 3.13.
- [uv](https://docs.astral.sh/uv/), que gestiona l'entorn virtual i les dependències.
- Una clau d'API d'HORIZON (menú d'usuari → **Mi perfil** → **Información** a la interfície
  web d'HORIZON).
- Accés de sortida a `https://api.horizon.delta90.com` des de la màquina on corri.

## Passos

1. Clona el repositori i entra-hi:

    ```bash
    git clone https://github.com/mesalles/horizon-mcp.git
    cd horizon-mcp
    ```

2. Instal·la les dependències (crea `.venv/` dins del projecte):

    ```bash
    uv sync
    ```

3. Crea el fitxer de configuració a partir de l'exemple i escriu-hi la clau:

    ```bash
    cp .env.example .env
    ```

    La resta de variables són opcionals i tenen valors per defecte raonables
    (vegeu [Configuració](../referencia/configuracio.md)).

4. Valida la configuració sense tocar HORIZON:

    ```bash
    uv run horizon-mcp --check
    ```

## On viu la clau

Dues opcions:

- **Al fitxer `.env`** (recomanat): la configuració del client MCP no conté cap secret, només
  l'ordre per arrencar el servidor.
- **Com a variable d'entorn** definida pel client MCP (`env` a la configuració de Claude
  Desktop, per exemple). Una variable d'entorn real sempre té prioritat sobre el `.env`.

El servidor busca el `.env` primer a l'arrel del projecte i, si no hi és, al directori
actual.

## Com saber que ha funcionat

- `uv run horizon-mcp --check` imprimeix `configuration OK` i l'URL de l'API.
- `uv run horizon-mcp --version` imprimeix la versió.

## Si falla

- **`uv: command not found`**: instal·la uv seguint la seva documentació i obre un terminal
  nou.
- **`uv sync` es queixa de la versió de Python**: cal 3.13 o superior; `uv python install
  3.13` la baixa sense tocar el sistema.
- **`HORIZON_API_KEY is not set`**: el `.env` és en una altra carpeta, o la línia té la clau
  entre cometes o amb espais. Escriu-la tal qual, sense cometes.

## Actualitzar

```bash
git pull
uv sync
```

Reinicia després el client MCP (Claude Desktop o Claude Code) perquè arrenqui la versió nova.

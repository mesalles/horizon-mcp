# Instalar

## Requisitos

- Python ≥ 3.13.
- [uv](https://docs.astral.sh/uv/), que gestiona el entorno virtual y las dependencias.
- Una clave de API de HORIZON (menú de usuario → **Mi perfil** → **Información** en la
  interfaz web de HORIZON).
- Acceso de salida a `https://api.horizon.delta90.com` desde la máquina donde se ejecute.

## Pasos

1. Clona el repositorio y entra en él:

    ```bash
    git clone https://github.com/mesalles/horizon-mcp.git
    cd horizon-mcp
    ```

2. Instala las dependencias (crea `.venv/` dentro del proyecto):

    ```bash
    uv sync
    ```

3. Crea el archivo de configuración a partir del ejemplo y escribe la clave:

    ```bash
    cp .env.example .env
    ```

    El resto de variables son opcionales y tienen valores por defecto razonables
    (véase [Configuración](../referencia/configuracio.md)).

4. Valida la configuración sin tocar HORIZON:

    ```bash
    uv run horizon-mcp --check
    ```

## Dónde vive la clave

Dos opciones:

- **En el archivo `.env`** (recomendado): la configuración del cliente MCP no contiene
  ningún secreto, solo el comando para arrancar el servidor.
- **Como variable de entorno** definida por el cliente MCP (`env` en la configuración de
  Claude Desktop, por ejemplo). Una variable de entorno real siempre tiene prioridad sobre
  el `.env`.

El servidor busca el `.env` primero en la raíz del proyecto y, si no está, en el directorio
actual.

## Cómo saber que ha funcionado

- `uv run horizon-mcp --check` imprime `configuration OK` y la URL de la API.
- `uv run horizon-mcp --version` imprime la versión.

## Si falla

- **`uv: command not found`**: instala uv siguiendo su documentación y abre un terminal
  nuevo.
- **`uv sync` se queja de la versión de Python**: hace falta 3.13 o superior; `uv python
  install 3.13` la descarga sin tocar el sistema.
- **`HORIZON_API_KEY is not set`**: el `.env` está en otra carpeta, o la línea tiene la clave
  entre comillas o con espacios. Escríbela tal cual, sin comillas.

## Actualizar

```bash
git pull
uv sync
```

Reinicia después el cliente MCP (Claude Desktop o Claude Code) para que arranque la versión
nueva.

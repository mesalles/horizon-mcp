# Primer uso

En un cuarto de hora: instalar horizon-mcp, poner la clave de API, comprobar que habla con
HORIZON, conectarlo a Claude Code y hacer la primera pregunta.

## Antes de empezar

- Python 3.13 o superior y [uv](https://docs.astral.sh/uv/) instalados.
- La clave de API de la cuenta de HORIZON de tu institución. Está en la interfaz web de
  HORIZON: menú de usuario (arriba a la derecha) → **Mi perfil** → **Información**.
- Claude Code instalado (para el paso 4). Si usas Claude Desktop, sigue
  [Conectar Claude Desktop](../guies/claude-desktop.md) en lugar del paso 4.

## 1. Instala

```bash
git clone https://github.com/mesalles/horizon-mcp.git
cd horizon-mcp
uv sync
```

`uv sync` crea un entorno virtual dentro del proyecto con las dependencias exactas.

## 2. Pon la clave

```bash
cp .env.example .env
```

Abre `.env` con un editor y escribe la clave en la línea `HORIZON_API_KEY=`. El archivo
`.env` está en el `.gitignore`: nunca se subirá al repositorio.

## 3. Comprueba la conexión

```bash
uv run horizon-mcp --ping
```

Hace tres llamadas reales a HORIZON (versión de la API, cuenta, inventario) y sale. Si todo
va bien muestra algo así:

```text
API: horizon-api 2.5.3 status=ok
Account(s): 00000000-0000-4000-8000-000000000001
Ranges: 192.0.2.0/24
Root domains: (none)
User-Agent accepted: 'horizon-mcp/0.2.0 (+https://github.com/mesalles/horizon-mcp)'
Client bearer token (streamable-http): not set
```

`Ranges` son los rangos IP que HORIZON vigila para tu cuenta. `Root domains` suele estar
vacío en las cuentas provisionadas por RedIRIS.

## 4. Conéctalo a Claude Code

```bash
claude mcp add --transport stdio --scope user horizon -- uv run --directory /ruta/absoluta/a/horizon-mcp horizon-mcp
```

Sustituye `/ruta/absoluta/a/horizon-mcp` por la carpeta donde lo has clonado. Abre Claude
Code y escribe `/mcp`: debe listar el servidor `horizon` con sus herramientas.

## 5. Haz la primera pregunta

Dentro de Claude Code, pide:

> ¿Qué rangos vigila HORIZON para nuestra institución?

El modelo llamará a la herramienta `inventory` y te responderá con los rangos. Después, con
una dirección de uno de los rangos:

> ¿Qué expone a Internet el host 192.0.2.41?

Ahora llamará a `exposure_summary` y te hará un resumen: puertos y servicios, ficha HTTP,
CVE por servicio, hallazgos web y certificados.

## Cómo saber que ha funcionado

- `--ping` ha mostrado `status=ok` y al menos un rango.
- `/mcp` en Claude Code muestra `horizon` conectado.
- La respuesta a la pregunta del host cita puertos y servicios concretos, y una fecha de
  última observación.

## Si falla

- **`HORIZON_API_KEY is not set`**: el `.env` no está en la raíz del proyecto o la línea
  está vacía.
- **`HORIZON rejected the API key (HTTP 401)`**: la clave es incorrecta o ha caducado.
  Vuelve a copiarla de HORIZON.
- **`HORIZON's WAF (Cloudflare) blocked the request`**: el cortafuegos de HORIZON rechaza
  el *User-Agent*. Véase [Diagnosticar problemas](../guies/diagnosticar.md).
- **`/mcp` no muestra `horizon`**: la ruta de `--directory` no es absoluta o no es correcta.
  Vuelve a ejecutar `claude mcp add` con la ruta correcta.
- En Windows, si `uv` no se encuentra desde el cliente, pon la ruta completa de `uv.exe`
  (véase [Conectar Claude Desktop](../guies/claude-desktop.md)).

## Siguientes pasos

- [Preguntar bien](../guies/preguntar-be.md): qué herramienta usa el modelo para cada
  pregunta.
- [Interpretar las CVE](../guies/interpretar-cve.md): antes de reportar nada.
- [Seguridad](../explicacio/seguretat.md): adónde van los datos que consultas.

[Català](README.md) · [Castellano](README.es.md)

# horizon-mcp

Servidor **MCP** ([Model Context Protocol](https://modelcontextprotocol.io)) de **solo lectura** sobre la API
de **HORIZON**, la plataforma de monitorización de superficie de exposición externa de Delta90 que RedIRIS
pone a disposición de las universidades públicas (y que el CCN-CERT ofrece, en versión reducida, como **ELSA**).

Permite que un asistente de IA compatible con MCP (Claude Desktop, Claude Code o cualquier otro cliente)
responda preguntas de un analista del SOC como:

- «¿Qué expone a Internet el host 192.0.2.41?»
- «¿Qué servicios del rango 192.0.2.0/24 tienen CVE con CVSS ≥ 9?»
- «¿Qué paneles de administración tenemos expuestos?»
- «¿Qué servicios nuevos han aparecido en el último ciclo de escaneo?»

Pensado para ser **compartido entre universidades**: cada institución ejecuta su propia copia con su
propia clave de API. En el código no hay nada específico de ninguna institución; los rangos y la cuenta
salen de la API.

## Qué hace y qué no hace

- **Solo lectura.** Todas las herramientas son consultas GET a HORIZON, declaradas como `readOnly` en el protocolo.
- **Pocas herramientas de alto nivel**, no un espejo de los 24 endpoints de la API. Los resultados se
  **recortan y agregan** en el servidor (fuera `geoip`, `asn`, banners en bruto; CVE agrupadas por servicio;
  hallazgos web agrupados por URL) para que quepan en el contexto del modelo.
- **Paginación y ritmo** gestionados internamente (páginas de 1.000 filas, espaciado mínimo entre peticiones).
- **La clave de API nunca sale** del servidor: ni al modelo, ni a los registros, ni a los errores.
- No escribe nada, no lanza escaneos, no modifica el inventario de HORIZON.

## Herramientas

| Herramienta | Qué devuelve |
|---|---|
| `inventory()` | Rangos IP y dominios raíz de la cuenta. Llamadla primero si no conocéis los rangos. |
| `open_ports(target, limit?, new_only?)` | Puertos y servicios abiertos (estilo Nmap) por IP o CIDR, con resumen por host. |
| `cves(target, min_cvss?, limit?, new_only?)` | CVE inferidas del CPE, **agrupadas por servicio** (IP, puerto, CPE), ordenadas por CVSS máximo. |
| `web_findings(target, limit?, new_only?)` | Hallazgos de plantillas Nuclei (paneles, malas configuraciones, fugas de información…), agrupados por (IP, puerto, nombre). |
| `tls_certificates(target, limit?)` | Certificados y conexión TLS de los servicios HTTPS: CN, SAN, emisor, caducidad, versión y cifrado. |
| `http_services(target, limit?)` | Fingerprint HTTP: código, título, tecnologías detectadas, CPE derivados. |
| `end_of_life(target, limit?)` | Servicios con software en fin de vida (datos tipo endoflife.date). |
| `exposure_summary(host, min_cvss?)` | Resumen en una llamada de todo lo que HORIZON sabe de un único host (IP o nombre): servicios, ficha HTTP, CVE por servicio (top 10 por CVSS, con el recuento total), hallazgos web, certificados y frescura de cada fuente. |
| `recent_changes(target, limit?)` | Novedades del último ciclo de escaneo en una llamada: servicios nuevos (con la ficha HTTP de los que son web), CVE nuevas por servicio y hallazgos web nuevos, con la fecha del ciclo. |

`target` puede ser una **IP, un CIDR** (/16 o más estrecho) **o un nombre de host**. HORIZON solo entiende
IP, así que los nombres los resuelve el propio servidor (A y AAAA, hasta 4 direcciones) y la respuesta incluye
`resolved_ips`; tened en cuenta que la resolución la hace la máquina donde corre el servidor, no Internet.
Las listas devuelven `total` y `returned` para que el modelo sepa si se han truncado.

> **Interpretad las CVE con cuidado.** HORIZON las infiere del producto y la versión detectados (CPE), no
> las verifica. Hay falsos positivos habituales por *backports* de distribución (Ubuntu, Debian) y rangos de
> versión abiertos en NVD. Las instrucciones del servidor ya se lo recuerdan al modelo.

## Requisitos

- Python ≥ 3.13 y [uv](https://docs.astral.sh/uv/).
- Una clave de API de HORIZON. Está en la interfaz web: menú de usuario (arriba a la derecha) → **Mi perfil** → **Información**.

## Instalación

```bash
git clone https://github.com/mesalles/horizon-mcp.git
cd horizon-mcp
uv sync
cp .env.example .env        # y poned HORIZON_API_KEY
uv run horizon-mcp --ping   # comprueba clave, conectividad e inventario sin arrancar el servidor
```

El fichero `.env` está en el `.gitignore`. Alternativamente, la clave puede pasarse como variable de
entorno desde la configuración del cliente MCP; el `.env` tiene la ventaja de que la configuración del
cliente no contiene ningún secreto.

## Uso con Claude Desktop

Editad `claude_desktop_config.json` (Windows: `%APPDATA%\Claude\`; macOS:
`~/Library/Application Support/Claude/`) y añadid:

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

En Windows, `command` debe ser la ruta absoluta de `uv.exe` (la aplicación de escritorio no tiene el PATH
de la consola) y las barras de la ruta, dobles (`C:\\Users\\...`). Reiniciad Claude Desktop: las
herramientas aparecen en el selector de herramientas del chat.

## Uso con Claude Code

```bash
claude mcp add --transport stdio --scope user horizon -- uv run --directory /ruta/absoluta/a/horizon-mcp horizon-mcp
```

Dentro de Claude Code, `/mcp` muestra el estado del servidor y las herramientas cargadas.

## Probarlo sin ningún cliente

```bash
uv run mcp dev src/horizon_mcp/server.py
```

Abre el **MCP Inspector** en el navegador: lista de herramientas, esquemas y llamadas manuales con el
JSON de respuesta.

## Servicio compartido (HTTP)

El mismo código puede correr como servicio para todo un equipo:

```bash
uv run horizon-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

El servidor **no autentica a los clientes**: ponedlo detrás de un proxy inverso con TLS y autenticación
(Caddy, nginx, Traefik…) y exponed solo `/mcp`. Los clientes se conectan con
`claude mcp add --transport http horizon https://vuestro-host/mcp`.

## Configuración

| Variable | Por defecto | Descripción |
|---|---|---|
| `HORIZON_API_KEY` | — | **Obligatoria.** Clave de API de la cuenta. |
| `HORIZON_API_URL` | `https://api.horizon.delta90.com` | URL base de la API. |
| `HORIZON_TIMEOUT` | `60` | Segundos por petición. |
| `HORIZON_MIN_INTERVAL` | `0.5` | Segundos mínimos entre dos peticiones a HORIZON. |
| `HORIZON_MAX_ROWS` | `200` | Límite por defecto de filas de las herramientas de lista (máximo absoluto 1.000). |
| `HORIZON_USER_AGENT` | `horizon-mcp/<versión> (+URL del repo)` | HORIZON está detrás de Cloudflare, que bloquea el User-Agent por defecto de las bibliotecas HTTP (error 1010). El valor por defecto, que identifica este proyecto, está verificado; un UA de navegador también pasa. |

## Cosas que conviene saber sobre los datos de HORIZON

Descubiertas empíricamente: la documentación de la API no describe los campos de respuesta.

- El ciclo de escaneo es, en la práctica, **semanal**. `last_seen` indica la frescura de un registro;
  `new` / `new_only` significa «visto por primera vez en el último ciclo», no «desde vuestra última consulta».
- El inventario de las cuentas provisionadas por RedIRIS contiene **solo rangos IP**, por contrato. Los
  endpoints por dominio (DNS, typosquatting, correo…) devuelven vacío y por eso no se exponen como herramientas.
- Los CPE llegan en formato **2.2** en `/ports`, `/cves` y `/eol`, y en **2.3** en `/httpinfo` y `/tls`.
  Se devuelven tal como vienen; hay un conversor en `normalize.cpe22_to_23` si lo necesitáis.
- Los nombres de los hallazgos web son **traducciones al castellano** de los títulos de plantilla de Nuclei;
  la API no da el identificador de plantilla ni CVE/CVSS para estos.
- `/eol` **no incluye el puerto**.
- La severidad `panel` (página de inicio de sesión expuesta) es una categoría propia de HORIZON.
- **HORIZON conecta por IP**, sin SNI ni cabecera `Host` del nombre real: los títulos y tecnologías HTTP son
  los del *virtual host* por defecto, y el certificado nunca coincide con el nombre (por eso no se reporta
  ningún `name_mismatch`). El sitio real que hay detrás de un nombre puede ser otro.
- **Cada índice tiene su cadencia.** Todas las filas llevan `last_seen` y `days_since_last_seen`; el resumen
  de un host incluye `data_freshness` (última observación por fuente) y marca cada hallazgo web y grupo de CVE
  con `observed_in_latest_cycle`. Un hallazgo con `false` no se ha vuelto a ver en el último ciclo de los
  servicios del host y probablemente es histórico.

## Desarrollo

```bash
uv sync
uv run pytest
```

Los tests no tocan HORIZON: usan muestras con la forma exacta de las respuestas reales y direcciones de
documentación (192.0.2.0/24).

## Condiciones de uso de HORIZON

Las condiciones del portal prohíben «cualquier tipo de automatización» pensando en la interfaz web.
Este servidor usa la **API oficial** que IRISCERT ha activado para las instituciones, solo en lectura y
con ritmo limitado. Aun así, si lo desplegáis como servicio compartido, es recomendable informar a IRISCERT.

## Licencia

MIT. Ver [LICENSE](LICENSE).

[Català](README.md) · [Castellano](README.es.md) · **Manual: [català](https://mesalles.github.io/horizon-mcp/) · [castellano](https://mesalles.github.io/horizon-mcp/es/)**

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
  **recortan y agregan** en el servidor para que quepan en el contexto del modelo.
- **Paginación y ritmo** gestionados internamente.
- **La clave de API nunca sale** del servidor: ni al modelo, ni a los registros, ni a los errores.
- No escribe nada, no lanza escaneos, no modifica el inventario de HORIZON.

## Herramientas

| Herramienta | Qué devuelve |
|---|---|
| `inventory()` | Rangos IP y dominios raíz de la cuenta. |
| `open_ports(target, limit?, new_only?)` | Puertos y servicios abiertos (estilo Nmap), con resumen por host. |
| `cves(target, min_cvss?, limit?, new_only?)` | CVE inferidas del CPE, agrupadas por servicio, ordenadas por CVSS máximo. |
| `web_findings(target, limit?, new_only?)` | Hallazgos de plantillas Nuclei, agrupados por (IP, puerto, nombre). |
| `tls_certificates(target, limit?)` | Certificados y conexión TLS de los servicios HTTPS. |
| `http_services(target, limit?)` | Fingerprint HTTP: código, título, tecnologías, CPE derivados. |
| `end_of_life(target, limit?)` | Servicios con software en fin de vida. |
| `exposure_summary(host, min_cvss?)` | Todo lo que HORIZON sabe de un único host, en una llamada. |
| `recent_changes(target, limit?)` | Novedades del último ciclo de escaneo, en una llamada. |

`target` puede ser una IP, un CIDR (/16 o más estrecho) o un nombre de host (resuelto por el servidor). Detalles,
parámetros y campos de respuesta: [Herramientas](https://mesalles.github.io/horizon-mcp/es/referencia/eines/) y
[Campos de respuesta](https://mesalles.github.io/horizon-mcp/es/referencia/camps/) en el manual.

> **Interpretad las CVE con cuidado.** HORIZON las infiere del producto y la versión detectados (CPE), no
> las verifica. Ver [Interpretar las CVE](https://mesalles.github.io/horizon-mcp/es/guies/interpretar-cve/).

## Instalación rápida

Requisitos: Python ≥ 3.13, [uv](https://docs.astral.sh/uv/) y una clave de API de HORIZON (interfaz web:
menú de usuario → **Mi perfil** → **Información**).

```bash
git clone https://github.com/mesalles/horizon-mcp.git
cd horizon-mcp
uv sync
cp .env.example .env        # y poned HORIZON_API_KEY
uv run horizon-mcp --ping   # comprueba clave, conectividad e inventario sin arrancar el servidor
```

Después, en el manual:

- [Primer uso](https://mesalles.github.io/horizon-mcp/es/tutorials/primer-us/) (paso a paso hasta la primera pregunta)
- [Conectar Claude Desktop](https://mesalles.github.io/horizon-mcp/es/guies/claude-desktop/) ·
  [Conectar Claude Code](https://mesalles.github.io/horizon-mcp/es/guies/claude-code/) ·
  [Probar sin ningún cliente](https://mesalles.github.io/horizon-mcp/es/guies/provar-sense-client/)
- [Servicio compartido (HTTP)](https://mesalles.github.io/horizon-mcp/es/guies/servei-compartit/) con token para los clientes
- [Configuración](https://mesalles.github.io/horizon-mcp/es/referencia/configuracio/) ·
  [Línea de comandos](https://mesalles.github.io/horizon-mcp/es/referencia/cli/) ·
  [Los datos de HORIZON](https://mesalles.github.io/horizon-mcp/es/referencia/dades-horizon/) ·
  [Seguridad](https://mesalles.github.io/horizon-mcp/es/explicacio/seguretat/)

## Desarrollo

```bash
uv sync
uv run pytest
```

Los tests no tocan HORIZON: usan muestras con la forma exacta de las respuestas reales y direcciones de
documentación (192.0.2.0/24). El manual está en `docs/` (MkDocs Material, catalán y castellano) y se
publica en GitHub Pages al fusionar en `main`; `mkdocs build --strict` se comprueba en cada PR.

## Condiciones de uso de HORIZON

Las condiciones del portal prohíben «cualquier tipo de automatización» pensando en la interfaz web.
Este servidor usa la **API oficial** que IRISCERT ha activado para las instituciones, solo en lectura y
con ritmo limitado. Aun así, si lo desplegáis como servicio compartido, es recomendable informar a IRISCERT.

## Licencia

MIT. Ver [LICENSE](LICENSE).

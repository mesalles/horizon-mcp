# Glosario

**HORIZON**
: Plataforma de monitorización de la superficie de exposición externa (Delta90) que RedIRIS
  pone a disposición de las universidades públicas. El CCN-CERT ofrece una versión reducida,
  ELSA.

**Superficie de exposición externa**
: Todo lo que una organización tiene visible desde Internet: puertos, servicios, webs,
  certificados.

**MCP** (Model Context Protocol)
: Protocolo abierto con el que un asistente de IA descubre y llama a herramientas de un
  servidor externo. Véase [Qué es MCP](../explicacio/que-es-mcp.md).

**Servidor MCP**
: Programa que expone herramientas a un cliente MCP. horizon-mcp es uno.

**Cliente MCP**
: La aplicación que usa las herramientas: Claude Desktop, Claude Code, el MCP Inspector…

**Herramienta**
: Una función que el modelo puede llamar, con nombre, parámetros y resultado. horizon-mcp
  tiene nueve.

**Transporte**
: Cómo se comunican cliente y servidor: `stdio` (el cliente arranca el proceso y le habla por
  la entrada y la salida estándar) o `streamable-http` (servicio HTTP).

**Objetivo** (`target`)
: Lo que se consulta: una IP, un CIDR o un nombre de host.

**CIDR**
: Notación de un rango de direcciones, como `192.0.2.0/24`. El número tras la barra dice
  cuántos bits fija el prefijo: /24 son 256 direcciones; /16, 65.536.

**Ciclo de escaneo**
: Cada pasada completa de HORIZON por los rangos de la cuenta; en la práctica, semanal.

**CPE**
: Identificador normalizado de un producto de software y su versión
  (`cpe:/a:apache:http_server:2.4.52`). HORIZON lo detecta y lo usa para inferir CVE.

**CVE**
: Identificador público de una vulnerabilidad conocida (`CVE-2022-31813`).

**CVSS**
: Puntuación de 0 a 10 de la gravedad de una CVE. De 7.0 a 8.9 es alta; 9.0 o más, crítica.

**Nuclei**
: Herramienta de plantillas con la que HORIZON detecta hallazgos web (paneles, mala
  configuración, fugas).

**Panel** (`panel`)
: Severidad propia de HORIZON: una página de inicio de sesión expuesta a Internet.

**Fin de vida** (EOL)
: Software que ya no recibe mantenimiento del fabricante.

**Virtual host por defecto**
: El sitio web que un servidor sirve cuando se le pide por IP, sin nombre. Es el que ve
  HORIZON.

**Loopback**
: Direcciones solo accesibles desde la misma máquina (`127.0.0.1`, `::1`, `localhost`).

**Token Bearer**
: Secreto que un cliente envía en la cabecera `Authorization: Bearer <token>` para
  identificarse ante el servicio HTTP.

**Proxy inverso**
: Servidor (Caddy, nginx, Traefik) que recibe las conexiones de fuera, les pone TLS y las
  reenvía al servicio interno.

**`.env`**
: Archivo de variables de entorno en la raíz del proyecto, ignorado por git, donde vive la
  clave.

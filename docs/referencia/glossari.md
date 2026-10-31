# Glossari

**HORIZON**
: Plataforma de monitoratge de la superfície d'exposició externa (Delta90) que RedIRIS posa
  a disposició de les universitats públiques. El CCN-CERT n'ofereix una versió reduïda, ELSA.

**Superfície d'exposició externa**
: Tot el que una organització té visible des d'Internet: ports, serveis, webs, certificats.

**MCP** (Model Context Protocol)
: Protocol obert amb què un assistent d'IA descobreix i crida eines d'un servidor extern.
  Vegeu [Què és MCP](../explicacio/que-es-mcp.md).

**Servidor MCP**
: Programa que exposa eines a un client MCP. horizon-mcp n'és un.

**Client MCP**
: L'aplicació que fa servir les eines: Claude Desktop, Claude Code, l'MCP Inspector…

**Eina**
: Una funció que el model pot cridar, amb nom, paràmetres i resultat. horizon-mcp en té nou.

**Transport**
: Com es comuniquen client i servidor: `stdio` (el client arrenca el procés i hi parla per
  l'entrada i la sortida estàndard) o `streamable-http` (servei HTTP).

**Objectiu** (`target`)
: El que es consulta: una IP, un CIDR o un nom de host.

**CIDR**
: Notació d'un rang d'adreces, com `192.0.2.0/24`. El número després de la barra diu quants
  bits fixa el prefix: /24 són 256 adreces; /16, 65.536.

**Cicle d'escaneig**
: Cada passada completa d'HORIZON pels rangs del compte; a la pràctica, setmanal.

**CPE**
: Identificador normalitzat d'un producte de programari i la seva versió
  (`cpe:/a:apache:http_server:2.4.52`). HORIZON el detecta i el fa servir per inferir CVE.

**CVE**
: Identificador públic d'una vulnerabilitat coneguda (`CVE-2022-31813`).

**CVSS**
: Puntuació de 0 a 10 de la gravetat d'una CVE. 7.0 a 8.9 és alta; 9.0 o més, crítica.

**Nuclei**
: Eina de plantilles amb què HORIZON detecta troballes web (panells, mala configuració,
  fuites).

**Panell** (`panel`)
: Severitat pròpia d'HORIZON: una pàgina d'inici de sessió exposada a Internet.

**Fi de vida** (EOL)
: Programari que ja no rep manteniment del fabricant.

**Virtual host per defecte**
: El lloc web que un servidor serveix quan se li demana per IP, sense nom. És el que veu
  HORIZON.

**Loopback**
: Adreces que només són accessibles des de la mateixa màquina (`127.0.0.1`, `::1`,
  `localhost`).

**Token Bearer**
: Secret que un client envia a la capçalera `Authorization: Bearer <token>` per
  identificar-se davant del servei HTTP.

**Proxy invers**
: Servidor (Caddy, nginx, Traefik) que rep les connexions de fora, hi posa TLS i les
  reenvia al servei intern.

**`.env`**
: Fitxer de variables d'entorn a l'arrel del projecte, ignorat pel git, on viu la clau.

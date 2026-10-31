# Les dades d'HORIZON

Fets sobre les dades, descoberts empíricament: la documentació de l'API no descriu els camps
de resposta.

## Cicle i frescor

- El cicle d'escaneig és, a la pràctica, **setmanal**.
- **Cada índex té la seva cadència**: ports, HTTP, CVE, troballes web i TLS no s'actualitzen
  el mateix dia. Per això les dates difereixen entre fonts.
- `last_seen` indica la frescor d'un registre; `new` / `new_only` vol dir «vist per primer
  cop a l'últim cicle», no «des de la vostra última consulta».
- HORIZON **no reporta el que desapareix**: un servei que ja no hi és simplement deixa
  d'actualitzar `last_seen`.

## Inventari

- Els comptes provisionats per RedIRIS contenen **només rangs IP**, per contracte. Els
  endpoints per domini (DNS, *typosquatting*, correu…) retornen buit i per això no s'exposen
  com a eines.

## Identificadors de programari (CPE)

- Els CPE arriben en format **2.2** (`cpe:/a:vendor:product:version`) a ports, CVE i fi de
  vida, i en **2.3** (`cpe:2.3:a:vendor:product:version:…`) a HTTP i TLS. Es retornen tal
  com vénen.
- `-` a la versió vol dir desconeguda.
- Els CPE de la fitxa HTTP es construeixen a partir dels noms de tecnologies i poden no
  existir al diccionari de NVD.

## CVE

- Inferides del CPE (producte i versió), **no verificades**. Vegeu
  [Interpretar les CVE](../guies/interpretar-cve.md).

## Troballes web

- Els noms són **traduccions al castellà** dels títols de les plantilles Nuclei; l'API no
  dóna l'identificador de plantilla ni CVE/CVSS per a aquestes.
- HORIZON repeteix la mateixa troballa una vegada per variant d'URL; el servidor les agrupa.
- La severitat `panel` (pàgina d'inici de sessió exposada) és una categoria pròpia d'HORIZON.

## HTTP i TLS

- **HORIZON connecta per IP**, sense SNI ni capçalera `Host` del nom real: els títols i
  tecnologies són els del *virtual host* per defecte, i el certificat mai no coincideix amb
  el nom (per això no es reporta cap `name_mismatch`). El lloc real darrere d'un nom pot ser
  un altre.

## Fi de vida

- `/eol` **no porta el port**: un host amb diversos serveis del mateix producte apareix una
  vegada per servei sense dir quin port.
- Dades tipus endoflife.date: el programari mantingut per la distribució pot aparèixer com a
  EOL encara que rebi pedaços.

## API

- Autenticació per capçalera `x-api-key`.
- Pàgines de 1.000 files amb `scroll_id`; el servidor segueix la paginació sol.
- Darrere de Cloudflare: el *User-Agent* per defecte de les biblioteques HTTP rep un 403 en
  HTML (error 1010).

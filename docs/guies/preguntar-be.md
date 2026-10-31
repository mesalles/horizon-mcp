# Preguntar bé

El model tria l'eina a partir de la pregunta i de les instruccions que el servidor li dóna.
Saber quina eina hi ha darrere de cada tipus de pregunta ajuda a formular-la perquè la
resposta sigui útil a la primera.

## Quina eina per a què

| Pregunta | Eina que cridarà | Consell |
|---|---|---|
| Quins rangs tenim? | `inventory` | Demana-ho primer si no coneixes els rangs. |
| Què exposa el host X? | `exposure_summary(host)` | Un sol host (IP o nom) per crida. Ja inclou ports, HTTP, CVE, troballes web i certificats: no cal demanar res més del mateix host. |
| Què hi ha de nou al rang? | `recent_changes(target)` | «Nou» = vist per primer cop a l'últim cicle d'HORIZON, no des de la teva última consulta. |
| Quins ports té obert el rang? | `open_ports(target)` | Afegeix «només els nous» per a `new_only`. |
| Quines CVE greus hi ha? | `cves(target, min_cvss)` | Digues el llindar: «CVSS 9 o més». |
| Quins panells o mala configuració web? | `web_findings(target)` | La severitat `panel` és una pàgina d'inici de sessió exposada. |
| Quins certificats caduquen? | `tls_certificates(target)` | Mira `days_to_expiry`. |
| Quin programari obsolet hi ha? | `end_of_life(target)` | HORIZON no diu el port en aquestes files. |
| Quina web hi ha darrere d'una IP? | `http_services(target)` | Títol i tecnologies del *virtual host* per defecte. |

## Com indicar l'objectiu

`target` accepta tres formes:

- Una **IP**: `192.0.2.41`.
- Un **CIDR** de /16 o més estret: `192.0.2.0/24`. Un /8 es rebutja per evitar consultes
  enormes.
- Un **nom de host**: `www.example.edu`. HORIZON només entén IP: el nom el resol la màquina
  on corre el servidor (fins a 4 adreces) i la resposta inclou `resolved_ips`. Si el nom
  resol a més de 4 adreces, cal consultar-les d'una en una.

## Consells

- **Una pregunta, un objectiu.** «Què exposa 192.0.2.41?» va millor que «què exposen
  aquests cinc hosts?»: el model farà cinc crides i perdrà context.
- **Digues els llindars.** «CVE amb CVSS 7 o més» evita que el model t'ensenyi cent CVE
  mitjanes.
- **Demana el context temporal.** «Quan es va veure per última vegada?» fa que el model miri
  `last_seen` i `observed_in_latest_cycle` en lloc de donar-ho tot per actual.
- **Les llistes es tallen.** Les eines de llista retornen com a màxim 200 files per defecte
  (`limit` fins a 1.000); `total` diu quantes n'hi ha en realitat. Si `returned` < `total`,
  estreny l'objectiu o demana un `limit` més alt.
- **Per a tendències, compara.** HORIZON no reporta serveis que han desaparegut; demana
  `open_ports` ara i compara'l amb una consulta anterior.

## Com saber que ha funcionat

- La resposta cita l'eina usada (o es veu al registre d'eines del client) i inclou dates
  (`last_seen`) i comptes (`total`, `returned`).

## Si falla

- **El model no crida cap eina**: anomena-la («fes servir `exposure_summary`») o comprova
  `/mcp`.
- **`… is not an IP address or CIDR`**: l'objectiu té un format que no és IP, CIDR ni nom
  vàlid.
- **`prefix /8 is too wide`**: usa /16 o més estret.
- **`does not resolve`**: el nom no resol des de la màquina del servidor (DNS intern,
  nom mal escrit).

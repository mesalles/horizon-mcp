# Eines

Nou eines, totes de **només lectura** i idempotents (declarades així al protocol). Els noms
i els paràmetres són els que veu el model. `target` admet una IP, un CIDR (/16 o més
estret) o un nom de host (resolt pel servidor; la resposta porta `resolved_ips`). `limit`
val 200 per defecte i 1.000 com a màxim. Els camps de cada fila es descriuen a
[Camps de resposta](camps.md).

## `inventory()`

Rangs IP i dominis arrel que HORIZON vigila per al compte. Crida-la primer si no coneixes
els rangs. Als comptes provisionats per RedIRIS els dominis arrel són normalment buits.

Retorna: `account_ids`, `ranges[]` (`cidr`, `netname`, `description`), `root_domains[]`.

## `open_ports(target, limit?, new_only?)`

Ports i serveis oberts (estil Nmap) vistos des d'Internet.

- `new_only`: només serveis vistos per primer cop a l'últim cicle.

Retorna: `target` (o `resolved_ips`), `total`, `returned`, `summary` (hosts, ports oberts i
serveis per IP), `ports[]`.

## `cves(target, min_cvss?, limit?, new_only?)`

CVE que HORIZON atribueix als serveis, **agrupades per servei** (IP, port, CPE) i ordenades
pel CVSS màxim.

- `min_cvss`: descarta les CVE per sota d'aquest valor (7.0 = altes i crítiques).
- `limit`: files de CVE en brut a llegir abans d'agrupar.

Retorna: `total_cve_rows`, `fetched_cve_rows`, `services_affected`, `services[]`.

## `web_findings(target, limit?, new_only?)`

Troballes de plantilles Nuclei: panells d'administració exposats, mala configuració, fuites
d'informació, redireccions obertes, problemes de TLS. Agrupades per (IP, port, nom), amb
totes les URL coincidents juntes.

Retorna: `total_rows`, `fetched_rows`, `findings[]`.

## `tls_certificates(target, limit?)`

Certificat i connexió TLS dels serveis HTTPS: noms (CN i SAN), emissor, validesa, versió del
protocol i xifratge. Útil per trobar els noms darrere d'una IP i els certificats que
caduquen.

Retorna: `total`, `returned`, `certificates[]`.

## `http_services(target, limit?)`

Fitxa HTTP dels serveis web: codi d'estat, títol de la pàgina, tecnologies detectades
(`nom:versió`) i CPE derivats. Els CPE d'aquí poden no existir a NVD; per a CVE, millor els
d'`open_ports`.

Retorna: `total`, `returned`, `services[]`.

## `end_of_life(target, limit?)`

Serveis amb programari en fi de vida. HORIZON no retorna el port en aquestes files. El
programari mantingut per la distribució pot aparèixer com a EOL encara que rebi pedaços.

Retorna: `total`, `returned`, `hosts[]`.

## `exposure_summary(host, min_cvss?)`

Resum d'**un sol host** (IP o nom) en una crida: ports i serveis, fitxa HTTP de cada servei
web, grups de CVE (10 CVE per grup com a màxim, `cve_count` dóna el total), troballes web,
certificats i frescor de cada font. Tot el que HORIZON sap del host, sense truncar. Si el nom
resol a diverses IP, es resumeix la primera IPv4 i la resta van a `other_resolved_ips`.

Retorna: `host`, `resolved_from`, `other_resolved_ips`, `hostnames_from_certificates`,
`data_freshness` (data més recent per font i nota), `open_ports`, `services[]`,
`http_services[]`, `cve_rows`, `max_cvss`, `cves_by_service[]`, `web_findings[]`,
`web_findings_not_reobserved`, `tls_certificates[]`, `last_seen`.

## `recent_changes(target, limit?)`

Novetats de l'últim cicle d'escaneig en una crida: serveis nous (amb la fitxa HTTP dels que
són web), CVE noves per servei i troballes web noves. «Nou» és relatiu al cicle d'HORIZON,
no a la teva última consulta. HORIZON no reporta serveis desapareguts.

Retorna: `cycle_date`, `counts` (`new_services`, `new_cve_rows`, `new_web_findings`),
`totals`, `new_services[]`, `new_cves_by_service[]`, `new_web_findings[]`.

## Errors

Qualsevol eina pot retornar `{"error": "<missatge>"}` en lloc del resultat. Els missatges
són a [Diagnosticar problemes](../guies/diagnosticar.md).

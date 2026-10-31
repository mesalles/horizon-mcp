# Camps de resposta

Els resultats són versions compactes de les files d'HORIZON: s'eliminen `geoip`, `asn`,
`account_ids`, `ip_origins` i els banners en brut. Les dates són `AAAA-MM-DD` (UTC). Els
exemples usen adreces de documentació (`192.0.2.0/24`).

## Servei (`open_ports`, `services[]` d'`exposure_summary`, `new_services[]`)

| Camp | Significat |
|---|---|
| `ip`, `port`, `transport` | Adreça, port i protocol (`TCP`). |
| `service` | Nom del servei detectat per Nmap (`http`, `ssh`…). |
| `product` | Producte detectat (`Apache httpd`, `OpenSSH`); pot faltar. |
| `tls` | `true` si el servei parla TLS. |
| `cpes[]` | CPE en format 2.2 tal com els dóna HORIZON; `-` a la versió vol dir desconeguda. |
| `first_seen`, `last_seen` | Primera i última observació. |
| `days_since_last_seen` | Dies des de l'última observació. |
| `new` | Vist per primer cop a l'últim cicle. |
| `http` (només a `recent_changes`) | `http_status`, `title`, `tech`, `last_seen` del servei web nou, o `null`. |

`summary` (a `open_ports`): `hosts`, `open_ports` i `by_host[]` (`ip`, `ports[]`,
`services[]`).

## Grup de CVE (`cves`, `cves_by_service[]`, `new_cves_by_service[]`)

| Camp | Significat |
|---|---|
| `ip`, `port`, `cpe` | El servei afectat. |
| `cve_count` | Nombre total de CVE del grup. |
| `max_cvss`, `severity` | CVSS més alt i la seva severitat. |
| `cves[]` | `cve`, `cvss`, `severity`, ordenades per CVSS descendent. A `exposure_summary`, com a màxim 10; `cves_truncated` diu quantes falten. |
| `first_seen`, `last_seen`, `days_since_last_seen` | Observacions del grup. |
| `new_cves` | CVE vistes per primer cop a l'últim cicle. |
| `observed_in_latest_cycle` (només a `exposure_summary`) | `true`/`false`/`null`: si el grup s'ha tornat a veure al darrer cicle de serveis del host. |

## Troballa web (`web_findings`, `web_findings[]`, `new_web_findings[]`)

| Camp | Significat |
|---|---|
| `ip`, `port`, `name` | El servei i el nom de la troballa (traducció al castellà del títol de la plantilla Nuclei). |
| `severity` | `info`, `low`, `medium`, `high`, `critical` o `panel` (pàgina d'inici de sessió exposada). |
| `urls[]` | Totes les URL on s'ha vist la mateixa troballa. |
| `first_seen`, `last_seen`, `days_since_last_seen`, `new` | Observacions. |
| `observed_in_latest_cycle` (només a `exposure_summary`) | Com als grups de CVE. |

Ordenades per severitat: `critical`, `high`, `medium`, `low`, `panel`, `info`.

## Certificat (`tls_certificates`, `tls_certificates[]`)

| Camp | Significat |
|---|---|
| `ip`, `port`, `url`, `http_status` | On s'ha observat. |
| `tls_version`, `cipher` | Protocol i xifratge negociats. |
| `subject_cn`, `subject_alt_names[]` | Noms del certificat. |
| `issuer` | Organització emissora (o el CN de l'emissor). |
| `not_before`, `not_after`, `days_to_expiry` | Validesa; `days_to_expiry` negatiu si ja ha caducat. |
| `sha256` | Empremta del certificat. |
| `cpes[]` | CPE en format 2.3. |
| `last_seen`, `days_since_last_seen` | Observació. |

No hi ha cap camp de «nom no coincident»: HORIZON connecta per IP, així que mai no coincideix.

## Servei HTTP (`http_services`, `http_services[]`)

| Camp | Significat |
|---|---|
| `ip`, `port`, `url`, `http_status` | On i amb quin codi respon. |
| `title` | Títol de la pàgina del *virtual host* per defecte. |
| `tech[]` | Tecnologies detectades, `nom:versió`. |
| `cpes[]` | CPE 2.3 derivats de les tecnologies (poden no existir a NVD). |
| `last_seen`, `days_since_last_seen` | Observació. |

## Fi de vida (`end_of_life`)

| Camp | Significat |
|---|---|
| `ip` | Host. `port` és sempre `null`: HORIZON no el dóna. |
| `tls`, `cpes[]` | Del servei. |
| `eol_components[]` | Per CPE: `release_cycle`, `eol_date`, `latest_in_cycle`, `is_eol`. |

## Inventari (`inventory`)

`account_ids[]`, `ranges[]` (`cidr`, `netname`, `description`), `root_domains[]`.

## Frescor (`exposure_summary`)

`data_freshness`: `services`, `http`, `cves`, `web_findings`, `tls` (data més recent de cada
font) i `note`. `last_seen` és la data del cicle de serveis, que fa de rellotge de referència.

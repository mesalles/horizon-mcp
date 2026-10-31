# Campos de respuesta

Los resultados son versiones compactas de las filas de HORIZON: se eliminan `geoip`, `asn`,
`account_ids`, `ip_origins` y los banners en bruto. Las fechas son `AAAA-MM-DD` (UTC). Los
ejemplos usan direcciones de documentación (`192.0.2.0/24`).

## Servicio (`open_ports`, `services[]` de `exposure_summary`, `new_services[]`)

| Campo | Significado |
|---|---|
| `ip`, `port`, `transport` | Dirección, puerto y protocolo (`TCP`). |
| `service` | Nombre del servicio detectado por Nmap (`http`, `ssh`…). |
| `product` | Producto detectado (`Apache httpd`, `OpenSSH`); puede faltar. |
| `tls` | `true` si el servicio habla TLS. |
| `cpes[]` | CPE en formato 2.2 tal como los da HORIZON; `-` en la versión significa desconocida. |
| `first_seen`, `last_seen` | Primera y última observación. |
| `days_since_last_seen` | Días desde la última observación. |
| `new` | Visto por primera vez en el último ciclo. |
| `http` (solo en `recent_changes`) | `http_status`, `title`, `tech`, `last_seen` del servicio web nuevo, o `null`. |

`summary` (en `open_ports`): `hosts`, `open_ports` y `by_host[]` (`ip`, `ports[]`,
`services[]`).

## Grupo de CVE (`cves`, `cves_by_service[]`, `new_cves_by_service[]`)

| Campo | Significado |
|---|---|
| `ip`, `port`, `cpe` | El servicio afectado. |
| `cve_count` | Número total de CVE del grupo. |
| `max_cvss`, `severity` | CVSS más alto y su severidad. |
| `cves[]` | `cve`, `cvss`, `severity`, ordenadas por CVSS descendente. En `exposure_summary`, como máximo 10; `cves_truncated` dice cuántas faltan. |
| `first_seen`, `last_seen`, `days_since_last_seen` | Observaciones del grupo. |
| `new_cves` | CVE vistas por primera vez en el último ciclo. |
| `observed_in_latest_cycle` (solo en `exposure_summary`) | `true`/`false`/`null`: si el grupo se ha vuelto a ver en el último ciclo de servicios del host. |

## Hallazgo web (`web_findings`, `web_findings[]`, `new_web_findings[]`)

| Campo | Significado |
|---|---|
| `ip`, `port`, `name` | El servicio y el nombre del hallazgo (traducción al castellano del título de la plantilla Nuclei). |
| `severity` | `info`, `low`, `medium`, `high`, `critical` o `panel` (página de inicio de sesión expuesta). |
| `urls[]` | Todas las URL donde se ha visto el mismo hallazgo. |
| `first_seen`, `last_seen`, `days_since_last_seen`, `new` | Observaciones. |
| `observed_in_latest_cycle` (solo en `exposure_summary`) | Como en los grupos de CVE. |

Ordenados por severidad: `critical`, `high`, `medium`, `low`, `panel`, `info`.

## Certificado (`tls_certificates`, `tls_certificates[]`)

| Campo | Significado |
|---|---|
| `ip`, `port`, `url`, `http_status` | Dónde se ha observado. |
| `tls_version`, `cipher` | Protocolo y cifrado negociados. |
| `subject_cn`, `subject_alt_names[]` | Nombres del certificado. |
| `issuer` | Organización emisora (o el CN del emisor). |
| `not_before`, `not_after`, `days_to_expiry` | Validez; `days_to_expiry` negativo si ya ha caducado. |
| `sha256` | Huella del certificado. |
| `cpes[]` | CPE en formato 2.3. |
| `last_seen`, `days_since_last_seen` | Observación. |

No hay ningún campo de «nombre no coincidente»: HORIZON conecta por IP, así que nunca
coincide.

## Servicio HTTP (`http_services`, `http_services[]`)

| Campo | Significado |
|---|---|
| `ip`, `port`, `url`, `http_status` | Dónde y con qué código responde. |
| `title` | Título de la página del *virtual host* por defecto. |
| `tech[]` | Tecnologías detectadas, `nombre:versión`. |
| `cpes[]` | CPE 2.3 derivados de las tecnologías (pueden no existir en NVD). |
| `last_seen`, `days_since_last_seen` | Observación. |

## Fin de vida (`end_of_life`)

| Campo | Significado |
|---|---|
| `ip` | Host. `port` es siempre `null`: HORIZON no lo da. |
| `tls`, `cpes[]` | Del servicio. |
| `eol_components[]` | Por CPE: `release_cycle`, `eol_date`, `latest_in_cycle`, `is_eol`. |

## Inventario (`inventory`)

`account_ids[]`, `ranges[]` (`cidr`, `netname`, `description`), `root_domains[]`.

## Frescura (`exposure_summary`)

`data_freshness`: `services`, `http`, `cves`, `web_findings`, `tls` (fecha más reciente de
cada fuente) y `note`. `last_seen` es la fecha del ciclo de servicios, que hace de reloj de
referencia.

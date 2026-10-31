# Herramientas

Nueve herramientas, todas de **solo lectura** e idempotentes (declaradas así en el
protocolo). Los nombres y los parámetros son los que ve el modelo. `target` admite una IP,
un CIDR (/16 o más estrecho) o un nombre de host (resuelto por el servidor; la respuesta
lleva `resolved_ips`). `limit` vale 200 por defecto y 1.000 como máximo. Los campos de cada
fila se describen en [Campos de respuesta](camps.md).

## `inventory()`

Rangos IP y dominios raíz que HORIZON vigila para la cuenta. Llámala primero si no conoces
los rangos. En las cuentas provisionadas por RedIRIS los dominios raíz suelen estar vacíos.

Devuelve: `account_ids`, `ranges[]` (`cidr`, `netname`, `description`), `root_domains[]`.

## `open_ports(target, limit?, new_only?)`

Puertos y servicios abiertos (estilo Nmap) vistos desde Internet.

- `new_only`: solo servicios vistos por primera vez en el último ciclo.

Devuelve: `target` (o `resolved_ips`), `total`, `returned`, `summary` (hosts, puertos
abiertos y servicios por IP), `ports[]`.

## `cves(target, min_cvss?, limit?, new_only?)`

CVE que HORIZON atribuye a los servicios, **agrupadas por servicio** (IP, puerto, CPE) y
ordenadas por el CVSS máximo.

- `min_cvss`: descarta las CVE por debajo de este valor (7.0 = altas y críticas).
- `limit`: filas de CVE en bruto a leer antes de agrupar.

Devuelve: `total_cve_rows`, `fetched_cve_rows`, `services_affected`, `services[]`.

## `web_findings(target, limit?, new_only?)`

Hallazgos de plantillas Nuclei: paneles de administración expuestos, mala configuración,
fugas de información, redirecciones abiertas, problemas de TLS. Agrupados por (IP, puerto,
nombre), con todas las URL coincidentes juntas.

Devuelve: `total_rows`, `fetched_rows`, `findings[]`.

## `tls_certificates(target, limit?)`

Certificado y conexión TLS de los servicios HTTPS: nombres (CN y SAN), emisor, validez,
versión del protocolo y cifrado. Útil para encontrar los nombres detrás de una IP y los
certificados que caducan.

Devuelve: `total`, `returned`, `certificates[]`.

## `http_services(target, limit?)`

Ficha HTTP de los servicios web: código de estado, título de la página, tecnologías
detectadas (`nombre:versión`) y CPE derivados. Los CPE de aquí pueden no existir en NVD;
para CVE, mejor los de `open_ports`.

Devuelve: `total`, `returned`, `services[]`.

## `end_of_life(target, limit?)`

Servicios con software en fin de vida. HORIZON no devuelve el puerto en estas filas. El
software mantenido por la distribución puede aparecer como EOL aunque reciba parches.

Devuelve: `total`, `returned`, `hosts[]`.

## `exposure_summary(host, min_cvss?)`

Resumen de **un solo host** (IP o nombre) en una llamada: puertos y servicios, ficha HTTP
de cada servicio web, grupos de CVE (10 CVE por grupo como máximo, `cve_count` da el total),
hallazgos web, certificados y frescura de cada fuente. Todo lo que HORIZON sabe del host, sin
truncar. Si el nombre resuelve a varias IP, se resume la primera IPv4 y el resto van a
`other_resolved_ips`.

Devuelve: `host`, `resolved_from`, `other_resolved_ips`, `hostnames_from_certificates`,
`data_freshness` (fecha más reciente por fuente y nota), `open_ports`, `services[]`,
`http_services[]`, `cve_rows`, `max_cvss`, `cves_by_service[]`, `web_findings[]`,
`web_findings_not_reobserved`, `tls_certificates[]`, `last_seen`.

## `recent_changes(target, limit?)`

Novedades del último ciclo de escaneo en una llamada: servicios nuevos (con la ficha HTTP de
los que son web), CVE nuevas por servicio y hallazgos web nuevos. «Nuevo» es relativo al
ciclo de HORIZON, no a tu última consulta. HORIZON no reporta servicios desaparecidos.

Devuelve: `cycle_date`, `counts` (`new_services`, `new_cve_rows`, `new_web_findings`),
`totals`, `new_services[]`, `new_cves_by_service[]`, `new_web_findings[]`.

## Errores

Cualquier herramienta puede devolver `{"error": "<mensaje>"}` en lugar del resultado. Los
mensajes están en [Diagnosticar problemas](../guies/diagnosticar.md).

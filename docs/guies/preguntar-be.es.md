# Preguntar bien

El modelo elige la herramienta a partir de la pregunta y de las instrucciones que le da el
servidor. Saber qué herramienta hay detrás de cada tipo de pregunta ayuda a formularla para
que la respuesta sea útil a la primera.

## Qué herramienta para qué

| Pregunta | Herramienta que llamará | Consejo |
|---|---|---|
| ¿Qué rangos tenemos? | `inventory` | Pídelo primero si no conoces los rangos. |
| ¿Qué expone el host X? | `exposure_summary(host)` | Un solo host (IP o nombre) por llamada. Ya incluye puertos, HTTP, CVE, hallazgos web y certificados: no hace falta pedir nada más del mismo host. |
| ¿Qué hay de nuevo en el rango? | `recent_changes(target)` | «Nuevo» = visto por primera vez en el último ciclo de HORIZON, no desde tu última consulta. |
| ¿Qué puertos tiene abiertos el rango? | `open_ports(target)` | Añade «solo los nuevos» para `new_only`. |
| ¿Qué CVE graves hay? | `cves(target, min_cvss)` | Di el umbral: «CVSS 9 o más». |
| ¿Qué paneles o mala configuración web? | `web_findings(target)` | La severidad `panel` es una página de inicio de sesión expuesta. |
| ¿Qué certificados caducan? | `tls_certificates(target)` | Mira `days_to_expiry`. |
| ¿Qué software obsoleto hay? | `end_of_life(target)` | HORIZON no dice el puerto en estas filas. |
| ¿Qué web hay detrás de una IP? | `http_services(target)` | Título y tecnologías del *virtual host* por defecto. |

## Cómo indicar el objetivo

`target` acepta tres formas:

- Una **IP**: `192.0.2.41`.
- Un **CIDR** de /16 o más estrecho: `192.0.2.0/24`. Un /8 se rechaza para evitar consultas
  enormes.
- Un **nombre de host**: `www.example.edu`. HORIZON solo entiende IP: el nombre lo resuelve
  la máquina donde corre el servidor (hasta 4 direcciones) y la respuesta incluye
  `resolved_ips`. Si el nombre resuelve a más de 4 direcciones, hay que consultarlas de una
  en una.

## Consejos

- **Una pregunta, un objetivo.** «¿Qué expone 192.0.2.41?» funciona mejor que «¿qué
  exponen estos cinco hosts?»: el modelo hará cinco llamadas y perderá contexto.
- **Di los umbrales.** «CVE con CVSS 7 o más» evita que el modelo te enseñe cien CVE medias.
- **Pide el contexto temporal.** «¿Cuándo se vio por última vez?» hace que el modelo mire
  `last_seen` y `observed_in_latest_cycle` en lugar de darlo todo por actual.
- **Las listas se cortan.** Las herramientas de lista devuelven como máximo 200 filas por
  defecto (`limit` hasta 1.000); `total` dice cuántas hay en realidad. Si `returned` <
  `total`, estrecha el objetivo o pide un `limit` mayor.
- **Para tendencias, compara.** HORIZON no reporta servicios que han desaparecido; pide
  `open_ports` ahora y compáralo con una consulta anterior.

## Cómo saber que ha funcionado

- La respuesta cita la herramienta usada (o se ve en el registro de herramientas del cliente)
  e incluye fechas (`last_seen`) y recuentos (`total`, `returned`).

## Si falla

- **El modelo no llama a ninguna herramienta**: nómbrala («usa `exposure_summary`») o
  comprueba `/mcp`.
- **`… is not an IP address or CIDR`**: el objetivo tiene un formato que no es IP, CIDR ni
  nombre válido.
- **`prefix /8 is too wide`**: usa /16 o más estrecho.
- **`does not resolve`**: el nombre no resuelve desde la máquina del servidor (DNS interno,
  nombre mal escrito).

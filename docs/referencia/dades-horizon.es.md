# Los datos de HORIZON

Hechos sobre los datos, descubiertos empíricamente: la documentación de la API no describe
los campos de respuesta.

## Ciclo y frescura

- El ciclo de escaneo es, en la práctica, **semanal**.
- **Cada índice tiene su cadencia**: puertos, HTTP, CVE, hallazgos web y TLS no se actualizan
  el mismo día. Por eso las fechas difieren entre fuentes.
- `last_seen` indica la frescura de un registro; `new` / `new_only` significa «visto por
  primera vez en el último ciclo», no «desde vuestra última consulta».
- HORIZON **no reporta lo que desaparece**: un servicio que ya no está simplemente deja de
  actualizar `last_seen`.

## Inventario

- Las cuentas provisionadas por RedIRIS contienen **solo rangos IP**, por contrato. Los
  endpoints por dominio (DNS, *typosquatting*, correo…) devuelven vacío y por eso no se
  exponen como herramientas.

## Identificadores de software (CPE)

- Los CPE llegan en formato **2.2** (`cpe:/a:vendor:product:version`) en puertos, CVE y fin
  de vida, y en **2.3** (`cpe:2.3:a:vendor:product:version:…`) en HTTP y TLS. Se devuelven
  tal como vienen.
- `-` en la versión significa desconocida.
- Los CPE de la ficha HTTP se construyen a partir de los nombres de tecnologías y pueden no
  existir en el diccionario de NVD.

## CVE

- Inferidas del CPE (producto y versión), **no verificadas**. Véase
  [Interpretar las CVE](../guies/interpretar-cve.md).

## Hallazgos web

- Los nombres son **traducciones al castellano** de los títulos de las plantillas Nuclei; la
  API no da el identificador de plantilla ni CVE/CVSS para estos.
- HORIZON repite el mismo hallazgo una vez por variante de URL; el servidor los agrupa.
- La severidad `panel` (página de inicio de sesión expuesta) es una categoría propia de
  HORIZON.

## HTTP y TLS

- **HORIZON conecta por IP**, sin SNI ni cabecera `Host` del nombre real: los títulos y
  tecnologías son los del *virtual host* por defecto, y el certificado nunca coincide con el
  nombre (por eso no se reporta ningún `name_mismatch`). El sitio real detrás de un nombre
  puede ser otro.

## Fin de vida

- `/eol` **no lleva el puerto**: un host con varios servicios del mismo producto aparece una
  vez por servicio sin decir qué puerto.
- Datos tipo endoflife.date: el software mantenido por la distribución puede aparecer como
  EOL aunque reciba parches.

## API

- Autenticación por cabecera `x-api-key`.
- Páginas de 1.000 filas con `scroll_id`; el servidor sigue la paginación solo.
- Detrás de Cloudflare: el *User-Agent* por defecto de las bibliotecas HTTP recibe un 403 en
  HTML (error 1010).

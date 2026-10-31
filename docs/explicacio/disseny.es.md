# Diseño del servidor

Cuatro reglas guían el código; entenderlas explica por qué las herramientas son como son.

## Pocas herramientas, en el vocabulario del analista

HORIZON tiene 24 endpoints. El servidor expone **nueve herramientas**, y dos de ellas
(`exposure_summary`, `recent_changes`) son resúmenes que combinan varias consultas. No es un
espejo de la API: cada herramienta responde a una pregunta que alguien haría de verdad
(«¿qué expone este host?», «¿qué ha aparecido de nuevo?»). Menos herramientas significa
menos errores del modelo al elegir una.

## Solo lectura

Todas las herramientas son consultas GET y se declaran en el protocolo como *read-only* e
idempotentes. El servidor no puede escribir, lanzar escaneos ni modificar el inventario,
aunque el modelo se equivoque o el usuario lo pida.

## Resultados recortados y agregados

Una fila de HORIZON lleva cerca de un 40 % de ruido para este uso: geolocalización, datos
de AS, identificadores de cuenta, banners en bruto. El servidor:

- elimina esos campos;
- convierte las fechas de milisegundos a `AAAA-MM-DD` y añade `days_since_last_seen`;
- **agrupa** las CVE por servicio (IP, puerto, CPE) y los hallazgos web por (IP, puerto,
  nombre), en lugar de devolver una fila por CVE o por variante de URL;
- **corta** las listas (200 filas por defecto, 1.000 como máximo) y dice siempre `total` y
  `returned` para que el modelo sepa si falta algo.

El objetivo es que el resultado quepa en el contexto del modelo y que el modelo no tenga
que hacer el trabajo de agregar.

## Nada específico de ninguna institución

En el código no hay rangos, cuentas ni dominios. Todo sale de la clave de API: la cuenta,
sus rangos y sus datos. Por eso el mismo repositorio sirve para cualquier universidad.

## Otras decisiones

- **Paginación y ritmo internos.** El servidor sigue la paginación de HORIZON (páginas de
  1.000 filas) y espera un mínimo de 0,5 s entre peticiones. El analista no lo ve.
- **Nombres de host resueltos en el servidor.** HORIZON solo entiende IP; el servidor
  resuelve los nombres (hasta 4 direcciones) y lo dice en la respuesta (`resolved_ips`). La
  resolución es la de la máquina donde corre, no la de Internet.
- **Errores como datos.** Una herramienta que falla devuelve `{"error": "…"}` en lugar de
  romper el turno, para que el modelo pueda explicar qué ha pasado.
- **Tests sin HORIZON.** Los tests usan muestras con la forma exacta de las respuestas reales
  y direcciones de documentación (`192.0.2.0/24`).

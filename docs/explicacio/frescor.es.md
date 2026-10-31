# Frescura de los datos

La pregunta que más errores provoca no es «¿qué hay?» sino «¿**sigue** ahí?». HORIZON
escanea por ciclos, cada índice a su ritmo, y no reporta lo que desaparece. El servidor
añade tres señales para responderla.

## `last_seen` y `days_since_last_seen`

Cada fila lleva la fecha de la última observación y los días transcurridos. Un hallazgo con
`days_since_last_seen: 90` en un host cuyos servicios se vieron hace 5 días probablemente ya
no está.

## `observed_in_latest_cycle`

En `exposure_summary`, el servidor toma la fecha más reciente del índice de **servicios** del
host como reloj de referencia (`last_seen` del resumen) y marca cada grupo de CVE y cada
hallazgo web:

- `true`: visto en ese ciclo (con un día de tolerancia);
- `false`: **no** se ha vuelto a observar; seguramente es histórico (corregido o
  desaparecido);
- `null`: no se puede saber (falta alguna fecha).

`web_findings_not_reobserved` cuenta cuántos hallazgos están a `false`.

## `data_freshness`

También en `exposure_summary`: la fecha más reciente de cada fuente (`services`, `http`,
`cves`, `web_findings`, `tls`). Si `cves` es de hace tres semanas y `services` de ayer, el
índice de CVE simplemente no se ha vuelto a ejecutar: no significa que las CVE hayan
desaparecido.

## «Nuevo» significa nuevo para HORIZON

`new`, `new_only` y todo `recent_changes` se refieren a «visto por primera vez en el último
ciclo de HORIZON» (`first_seen == last_seen == fecha del ciclo`). No es «nuevo desde que
pregunté la semana pasada». Para saber qué ha cambiado entre dos consultas tuyas, hay que
compararlas.

## Cómo reportarlo

- Actual: «el host expone X (observado el `<last_seen>`)».
- Histórico: «HORIZON vio X por última vez el `<last_seen>`; no se ha vuelto a observar».
- Nunca «el host es vulnerable a X» a partir solo de una CVE inferida
  (véase [Interpretar las CVE](../guies/interpretar-cve.md)).

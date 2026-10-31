# Frescor de les dades

La pregunta que més errors provoca no és «què hi ha?» sinó «**encara** hi és?». HORIZON
escaneja per cicles, cada índex al seu ritme, i no reporta el que desapareix. El servidor
afegeix tres senyals per respondre-la.

## `last_seen` i `days_since_last_seen`

Cada fila porta la data de l'última observació i els dies transcorreguts. Una troballa
amb `days_since_last_seen: 90` en un host els serveis del qual es van veure fa 5 dies
probablement ja no hi és.

## `observed_in_latest_cycle`

A `exposure_summary`, el servidor pren la data més recent de l'índex de **serveis** del host
com a rellotge de referència (`last_seen` del resum) i marca cada grup de CVE i cada
troballa web:

- `true`: vist en aquell cicle (amb un dia de tolerància);
- `false`: **no** s'ha tornat a observar; segurament és històric (corregit o desaparegut);
- `null`: no es pot saber (falta alguna data).

`web_findings_not_reobserved` compta quantes troballes estan a `false`.

## `data_freshness`

També a `exposure_summary`: la data més recent de cada font (`services`, `http`, `cves`,
`web_findings`, `tls`). Si `cves` és de fa tres setmanes i `services` d'ahir, l'índex de CVE
simplement no s'ha tornat a executar: no vol dir que les CVE hagin desaparegut.

## «Nou» vol dir nou per a HORIZON

`new`, `new_only` i tot `recent_changes` es refereixen a «vist per primer cop a l'últim
cicle d'HORIZON» (`first_seen == last_seen == data del cicle`). No és «nou des que vaig
preguntar la setmana passada». Per saber què ha canviat entre dues consultes teves, cal
comparar-les.

## Com reportar-ho

- Actual: «el host exposa X (observat el `<last_seen>`)».
- Històric: «HORIZON va veure X per última vegada el `<last_seen>`; no s'ha tornat a
  observar».
- Mai «el host és vulnerable a X» a partir només d'una CVE inferida
  (vegeu [Interpretar les CVE](../guies/interpretar-cve.md)).

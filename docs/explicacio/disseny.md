# Disseny del servidor

Quatre regles guien el codi; entendre-les explica per què les eines són com són.

## Poques eines, en el vocabulari de l'analista

HORIZON té 24 endpoints. El servidor n'exposa **nou eines**, i dues d'elles
(`exposure_summary`, `recent_changes`) són resums que combinen diverses consultes. No és
un mirall de l'API: cada eina respon a una pregunta que algú faria de veritat («què exposa
aquest host?», «què ha aparegut de nou?»). Menys eines vol dir menys errors del model en
triar-ne una.

## Només lectura

Totes les eines són consultes GET i es declaren al protocol com a *read-only* i
idempotents. El servidor no pot escriure, llançar escanejos ni modificar l'inventari, encara
que el model s'equivoqui o l'usuari ho demani.

## Resultats retallats i agregats

Una fila d'HORIZON porta prop d'un 40 % de soroll per a aquest ús: geolocalització, dades
d'AS, identificadors de compte, banners en brut. El servidor:

- elimina aquests camps;
- converteix les dates de mil·lisegons a `AAAA-MM-DD` i afegeix `days_since_last_seen`;
- **agrupa** les CVE per servei (IP, port, CPE) i les troballes web per (IP, port, nom), en
  lloc de retornar una fila per CVE o per variant d'URL;
- **talla** les llistes (200 files per defecte, 1.000 com a màxim) i diu sempre `total` i
  `returned` perquè el model sàpiga si falta alguna cosa.

L'objectiu és que el resultat càpiga al context del model i que el model no hagi de fer la
feina d'agregar.

## Res d'específic de cap institució

Al codi no hi ha rangs, comptes ni dominis. Tot surt de la clau d'API: el compte, els seus
rangs i les seves dades. Per això el mateix repositori serveix per a qualsevol universitat.

## Altres decisions

- **Paginació i ritme interns.** El servidor segueix la paginació d'HORIZON (pàgines de
  1.000 files) i espera un mínim de 0,5 s entre peticions. L'analista no ho veu.
- **Noms de host resolts al servidor.** HORIZON només entén IP; el servidor resol els noms
  (fins a 4 adreces) i ho diu a la resposta (`resolved_ips`). La resolució és la de la
  màquina on corre, no la d'Internet.
- **Errors com a dades.** Una eina que falla retorna `{"error": "…"}` en lloc de trencar el
  torn, perquè el model pugui explicar què ha passat.
- **Tests sense HORIZON.** Els tests fan servir mostres amb la forma exacta de les respostes
  reals i adreces de documentació (`192.0.2.0/24`).

# Seguretat

## El que protegeix el servidor

- **La clau d'API no surt mai.** Només viu a l'entorn del procés i a la capçalera de les
  peticions a HORIZON. No apareix al model, als registres (ni amb `DEBUG`), als errors ni a
  les sortides de `--check` i `--ping`.
- **Només lectura.** Cap eina pot modificar res a HORIZON.
- **Objectius acotats.** Es rebutgen els CIDR més amples que /16 i els noms que resolen a
  més de 4 adreces, per evitar consultes desmesurades.

## El que has de protegir tu

**El `.env`.** Qui el llegeix té la clau de la institució. Permisos de fitxer restrictius,
mai al git, mai en captures de pantalla.

**El port, en mode HTTP.** Qui arriba al port veu tot el que veu la clau. El servidor
imposa un mínim: es nega a escoltar en una adreça que no sigui loopback sense un token de
clients (`HORIZON_MCP_BEARER_TOKEN`). La resta és feina del desplegament: proxy invers amb
TLS, exposar només `/mcp`, i autenticació per persona al proxy si cal. El token és un únic
secret compartit, sense usuaris ni permisos.

**On van els resultats.** Això és el que cap avís del servidor et pot estalviar: els
resultats de les consultes (ports, serveis, CVE, troballes) els rep el **model**, i el model
corre on corri el client. Amb Claude Desktop o Claude Code, les dades d'exposició de la
institució viatgen al proveïdor del model com a part de la conversa. És una decisió de la
institució si això és acceptable, amb quin proveïdor i sota quin contracte; el servidor no
hi posa cap límit perquè no pot saber quin client hi ha darrere.

## Condicions d'ús d'HORIZON

Les condicions del portal prohibeixen «cualquier tipo de automatización» pensant en la
interfície web. Aquest servidor fa servir l'**API oficial** que IRISCERT ha activat per a les
institucions, només en lectura i amb ritme limitat (0,5 s entre peticions). Si el
desplegueu com a servei compartit, és recomanable informar-ne IRISCERT.

## Què no fa

- No autentica persones (en `stdio`, qui llança el procés és qui l'usa).
- No xifra: en mode HTTP, el TLS és del proxy.
- No registra qui ha preguntat què; si cal una pista d'auditoria per persona, l'ha de donar el
  client o el proxy.

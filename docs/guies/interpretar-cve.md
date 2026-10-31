# Interpretar les CVE

HORIZON **infereix** les CVE: detecta un producte i una versió (un CPE) en un servei i
busca les CVE que afecten aquesta versió. No verifica res per explotació. Les eines `cves`,
`exposure_summary` i `recent_changes` t'ho recorden, i el servidor també ho recorda al model.

## D'on surten els falsos positius

- **Backports de distribució.** Ubuntu o Debian mantenen versions antigues amb pedaços de
  seguretat sense canviar el número de versió. Un `nginx 1.18.0` d'Ubuntu pot tenir
  corregida una CVE que NVD atribueix a «1.18.0».
- **Rangs de versió oberts a NVD.** Algunes CVE afecten «fins a la versió X» sense límit
  inferior clar, i s'assignen a versions que no hi tenen res a veure.
- **CPE sense versió.** Un CPE acabat en `-` vol dir «versió desconeguda»; les CVE
  assignades són encara menys fiables.
- **CPE sintetitzats.** Els CPE de la fitxa HTTP (`http_services`) es construeixen a partir
  de noms de tecnologies i poden no existir al diccionari de NVD. Per a CVE, fes servir els
  CPE d'`open_ports`.

## Com llegir un grup de CVE

Les CVE arriben **agrupades per servei** (IP, port, CPE), ordenades pel CVSS màxim:

```json
{
  "ip": "192.0.2.41", "port": 80, "cpe": "cpe:/a:apache:http_server:2.4.52",
  "cve_count": 3, "max_cvss": 9.8, "severity": "critical",
  "cves": [{"cve": "CVE-2022-31813", "cvss": 9.8, "severity": "critical"}, "…"],
  "first_seen": "2026-08-06", "last_seen": "2026-09-15",
  "days_since_last_seen": 5, "new_cves": 0
}
```

- `cve_count` és el nombre real; a `exposure_summary` la llista `cves` es talla a les 10 de
  CVSS més alt (`cves_truncated` diu quantes falten).
- `new_cves`: quantes s'han vist per primer cop a l'últim cicle.
- `observed_in_latest_cycle` (a `exposure_summary`): `false` vol dir que el grup no s'ha
  tornat a observar al darrer cicle de serveis del host; probablement és històric.

## Procediment abans de reportar

1. Confirma que el servei encara hi és: `last_seen` recent i `observed_in_latest_cycle`
   no és `false`.
2. Comprova la versió real al host (gestor de paquets, capçaleres) i si la distribució ha
   aplicat el pedaç (`apt changelog`, avisos de seguretat de la distribució).
3. Dóna prioritat a `max_cvss` i a la severitat, però llegeix la CVE concreta: una 9.8 en un
   mòdul que no feu servir no és una urgència.
4. Reporta-ho com a «potencialment afectat per…», no com a «vulnerable a…».

## Com saber que ha funcionat

- El teu informe cita la data d'observació, la versió detectada (CPE) i la verificació feta
  al host.

## Si falla

- **Massa CVE per processar**: passa `min_cvss` (per exemple 7.0) o estreny l'objectiu.
- **El mateix servei surt diverses vegades**: pot tenir més d'un CPE (producte i sistema
  operatiu); cada CPE és un grup.
- **La CVE no apareix a NVD amb aquesta versió**: és un cas de rang obert o de CPE
  sintetitzat; descarta-la amb la comprovació al host.

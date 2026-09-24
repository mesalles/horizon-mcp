[Català](README.md) · [Castellano](README.es.md)

# horizon-mcp

Servidor **MCP** ([Model Context Protocol](https://modelcontextprotocol.io)) de **només lectura** sobre l'API
d'**HORIZON**, la plataforma de monitoratge de superfície d'exposició externa de Delta90 que RedIRIS
posa a disposició de les universitats públiques (i que el CCN-CERT ofereix, en versió reduïda, com a **ELSA**).

Permet que un assistent d'IA compatible amb MCP (Claude Desktop, Claude Code, o qualsevol altre client)
respongui preguntes d'un analista del SOC com:

- «Què exposa a Internet el host 192.0.2.41?»
- «Quins serveis del rang 192.0.2.0/24 tenen CVE amb CVSS ≥ 9?»
- «Quins panells d'administració tenim exposats?»
- «Quins serveis nous han aparegut a l'últim cicle d'escaneig?»

Pensat per ser **compartit entre universitats**: cada institució n'executa la seva còpia amb la seva
pròpia clau d'API. Al codi no hi ha res específic de cap institució; els rangs i el compte surten de l'API.

## Què fa i què no fa

- **Només lectura.** Totes les eines són consultes GET a HORIZON, declarades com a `readOnly` al protocol.
- **Poques eines d'alt nivell**, no un mirall dels 24 endpoints de l'API. Els resultats es **retallen i
  agreguen** al servidor (fora `geoip`, `asn`, banners en brut; CVE agrupades per servei; troballes web
  agrupades per URL) perquè càpiguen al context del model.
- **Paginació i ritme** gestionats internament (pàgines de 1.000 files, espaiat mínim entre peticions).
- **La clau d'API no surt mai** del servidor: ni al model, ni als registres, ni als errors.
- No escriu res, no llança escaneigs, no modifica l'inventari d'HORIZON.

## Eines

| Eina | Què retorna |
|---|---|
| `inventory()` | Rangs IP i dominis arrel del compte. Crideu-la primer si no coneixeu els rangs. |
| `open_ports(target, limit?, new_only?)` | Ports i serveis oberts (estil Nmap) per IP o CIDR, amb resum per host. |
| `cves(target, min_cvss?, limit?, new_only?)` | CVE inferides del CPE, **agrupades per servei** (IP, port, CPE), ordenades per CVSS màxim. |
| `web_findings(target, limit?, new_only?)` | Troballes de plantilles Nuclei (panells, mala configuració, fuites d'informació…), agrupades per (IP, port, nom). |
| `tls_certificates(target, limit?)` | Certificats i connexió TLS dels serveis HTTPS: CN, SAN, emissor, caducitat, versió i xifratge. |
| `http_services(target, limit?)` | Fingerprint HTTP: codi, títol, tecnologies detectades, CPE derivats. |
| `end_of_life(target, limit?)` | Serveis amb programari en fi de vida (dades tipus endoflife.date). |
| `exposure_summary(host, min_cvss?)` | Resum en una crida de tot el que HORIZON sap d'un únic host (IP o nom): serveis, fitxa HTTP, CVE per servei (top 10 per CVSS, amb el recompte total), troballes web, certificats i frescor de cada font. |
| `recent_changes(target, limit?)` | Novetats de l'últim cicle d'escaneig en una crida: serveis nous (amb la fitxa HTTP dels que són web), CVE noves per servei i troballes web noves, amb la data del cicle. |

`target` pot ser una **IP, un CIDR** (/16 o més estret) **o un nom de host**. HORIZON només entén IP, així
que els noms els resol el propi servidor (A i AAAA, fins a 4 adreces) i la resposta inclou `resolved_ips`;
tingueu en compte que la resolució la fa la màquina on corre el servidor, no Internet. Les llistes retornen
`total` i `returned` perquè el model sàpiga si s'han truncat.

> **Interpreteu les CVE amb cura.** HORIZON les infereix del producte i la versió detectats (CPE), no
> les verifica. Hi ha falsos positius habituals per *backports* de distribució (Ubuntu, Debian) i rangs
> de versió oberts a NVD. Les instruccions del servidor ja ho recorden al model.

## Requisits

- Python ≥ 3.13 i [uv](https://docs.astral.sh/uv/).
- Una clau d'API d'HORIZON. Es troba a la interfície web: menú d'usuari (a dalt a la dreta) → **Mi perfil** → **Información**.

## Instal·lació

```bash
git clone https://github.com/mesalles/horizon-mcp.git
cd horizon-mcp
uv sync
cp .env.example .env        # i poseu-hi HORIZON_API_KEY
uv run horizon-mcp --ping   # comprova clau, connectivitat i inventari sense arrencar el servidor
```

El fitxer `.env` és al `.gitignore`. Alternativament, la clau es pot passar com a variable d'entorn
des de la configuració del client MCP; el `.env` té l'avantatge que la configuració del client no
conté cap secret.

## Ús amb Claude Desktop

Editeu `claude_desktop_config.json` (Windows: `%APPDATA%\Claude\`; macOS:
`~/Library/Application Support/Claude/`) i afegiu-hi:

```json
{
  "mcpServers": {
    "horizon": {
      "command": "uv",
      "args": ["run", "--directory", "/ruta/absoluta/a/horizon-mcp", "horizon-mcp"]
    }
  }
}
```

A Windows, `command` ha de ser la ruta absoluta d'`uv.exe` (l'aplicació d'escriptori no té el PATH de
la consola) i les barres de la ruta, dobles (`C:\\Users\\...`). Reinicieu Claude Desktop: les eines
apareixen al selector d'eines del xat.

## Ús amb Claude Code

```bash
claude mcp add --transport stdio --scope user horizon -- uv run --directory /ruta/absoluta/a/horizon-mcp horizon-mcp
```

Dins de Claude Code, `/mcp` mostra l'estat del servidor i les eines carregades.

## Provar-lo sense cap client

```bash
uv run horizon-mcp --check                     # valida la configuració i surt
uv run horizon-mcp --ping                      # crida real a HORIZON: API, compte, rangs
uv run mcp dev inspector.py                    # MCP Inspector (requereix Node: fa servir npx)
```

L'**MCP Inspector** s'obre al navegador (cal obrir la URL **amb el token** que imprimeix): botó *Connect*,
pestanya *Tools* → *List Tools*, tria una eina, omple els paràmetres i *Run Tool*. `inspector.py` és només un
punt d'entrada que importa el servidor com a paquet; `mcp dev` no pot carregar `server.py` directament. Amb `--log-level DEBUG` el servidor també mostra cada petició HTTP a HORIZON per stderr.

## Servei compartit (HTTP)

El mateix codi pot córrer com a servei per a tot un equip. Com que el servidor parla amb HORIZON amb la
clau de la institució, **qui arriba al port veu tot el que veu la clau**: per això en mode HTTP demana un
secret compartit als clients i es nega a obrir un port accessible sense cap autenticació.

```bash
# 1) Genereu un secret i poseu-lo a .env com a HORIZON_MCP_BEARER_TOKEN
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 2) Arrenqueu-lo (darrere d'un proxy invers amb TLS: Caddy, nginx, Traefik…; exposeu només /mcp)
uv run horizon-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

| Transport | `--host` | `HORIZON_MCP_BEARER_TOKEN` | Resultat |
|---|---|---|---|
| stdio | — | — | Arrenca; no s'aplica cap autenticació (qui llança el procés és qui l'usa). |
| HTTP | loopback (`127.0.0.1`, `::1`, `localhost`) | qualsevol | Arrenca. Sense token, només hi arriba qui ja és a la màquina (o el proxy). |
| HTTP | altre (`0.0.0.0`, una IP…) | definit | Arrenca; cada petició ha de portar `Authorization: Bearer <token>`, si no rep `401`. |
| HTTP | altre | no definit | **Es nega a arrencar** amb un missatge clar. `--allow-unauthenticated` ho força, per a qui ja autentica al proxy i n'assumeix el risc. |

Els clients passen el token com a capçalera:

```bash
claude mcp add --transport http horizon https://el-vostre-host/mcp --header "Authorization: Bearer <token>"
```

`--check` i `--ping` indiquen si el token de clients està configurat (mai en mostren el valor). El token
és un únic secret per instància, comparat en temps constant; l'autenticació per usuari, si algun dia cal,
és feina del proxy.

## Configuració

| Variable | Per defecte | Descripció |
|---|---|---|
| `HORIZON_API_KEY` | — | **Obligatòria.** Clau d'API del compte. |
| `HORIZON_API_URL` | `https://api.horizon.delta90.com` | URL base de l'API. |
| `HORIZON_TIMEOUT` | `60` | Segons per petició. |
| `HORIZON_MIN_INTERVAL` | `0.5` | Segons mínims entre dues peticions a HORIZON. |
| `HORIZON_MAX_ROWS` | `200` | Límit per defecte de files de les eines de llista (màxim absolut 1.000). |
| `HORIZON_MCP_BEARER_TOKEN` | — | Només en mode `streamable-http`: secret que els clients MCP han d'enviar com a `Authorization: Bearer …`. Sense ell, el servidor no escolta en adreces que no siguin loopback (vegeu *Servei compartit*). |
| `HORIZON_USER_AGENT` | `horizon-mcp/<versió> (+URL del repo)` | HORIZON és darrere de Cloudflare, que bloqueja el User-Agent per defecte de les biblioteques HTTP (error 1010). El valor per defecte, que identifica aquest projecte, està verificat; un UA de navegador també passa. |

## Coses a saber sobre les dades d'HORIZON

Descobertes empíricament: la documentació de l'API no descriu els camps de resposta.

- El cicle d'escaneig és, en la pràctica, **setmanal**. `last_seen` indica la frescor d'un registre;
  `new` / `new_only` vol dir «vist per primer cop a l'últim cicle», no «des de la vostra última consulta».
- L'inventari dels comptes provisionats per RedIRIS conté **només rangs IP**, per contracte. Els
  endpoints per domini (DNS, typosquatting, correu…) tornen buit i per això no s'exposen com a eines.
- Els CPE arriben en format **2.2** a `/ports`, `/cves` i `/eol`, i en **2.3** a `/httpinfo` i `/tls`.
  Es retornen tal com venen; hi ha un conversor a `normalize.cpe22_to_23` si el necessiteu.
- Els noms de les troballes web són **traduccions al castellà** dels títols de plantilla de Nuclei; l'API no
  dona l'identificador de plantilla ni CVE/CVSS per a aquestes.
- `/eol` **no porta el port**.
- La severitat `panel` (pàgina d'inici de sessió exposada) és una categoria pròpia d'HORIZON.
- **HORIZON connecta per IP**, sense SNI ni capçalera `Host` del nom real: els títols i tecnologies HTTP són
  els del *virtual host* per defecte, i el certificat mai no coincideix amb el nom (per això no es reporta
  cap `name_mismatch`). El lloc real que hi ha darrere d'un nom pot ser un altre.
- **Cada índex té la seva cadència.** Totes les files porten `last_seen` i `days_since_last_seen`; el resum
  d'un host inclou `data_freshness` (darrera observació per font) i marca cada troballa web i grup de CVE amb
  `observed_in_latest_cycle`. Una troballa amb `false` no s'ha tornat a veure al darrer cicle dels serveis
  del host i probablement és històrica.

## Desenvolupament

```bash
uv sync
uv run pytest
```

Els tests no toquen HORIZON: fan servir mostres amb la forma exacta de les respostes reals i adreces
de documentació (192.0.2.0/24).

## Condicions d'ús d'HORIZON

Les condicions del portal prohibeixen «cualquier tipo de automatización» pensant en la interfície web.
Aquest servidor fa servir l'**API oficial** que IRISCERT ha activat per a les institucions, només en
lectura i amb ritme limitat. Tot i això, si el desplegueu com a servei compartit, és recomanable
informar-ne IRISCERT.

## Llicència

MIT. Vegeu [LICENSE](LICENSE).

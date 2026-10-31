[Català](README.md) · [Castellano](README.es.md) · **Manual: [català](https://mesalles.github.io/horizon-mcp/) · [castellano](https://mesalles.github.io/horizon-mcp/es/)**

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
  agreguen** al servidor perquè càpiguen al context del model.
- **Paginació i ritme** gestionats internament.
- **La clau d'API no surt mai** del servidor: ni al model, ni als registres, ni als errors.
- No escriu res, no llança escaneigs, no modifica l'inventari d'HORIZON.

## Eines

| Eina | Què retorna |
|---|---|
| `inventory()` | Rangs IP i dominis arrel del compte. |
| `open_ports(target, limit?, new_only?)` | Ports i serveis oberts (estil Nmap), amb resum per host. |
| `cves(target, min_cvss?, limit?, new_only?)` | CVE inferides del CPE, agrupades per servei, ordenades per CVSS màxim. |
| `web_findings(target, limit?, new_only?)` | Troballes de plantilles Nuclei, agrupades per (IP, port, nom). |
| `tls_certificates(target, limit?)` | Certificats i connexió TLS dels serveis HTTPS. |
| `http_services(target, limit?)` | Fingerprint HTTP: codi, títol, tecnologies, CPE derivats. |
| `end_of_life(target, limit?)` | Serveis amb programari en fi de vida. |
| `exposure_summary(host, min_cvss?)` | Tot el que HORIZON sap d'un únic host, en una crida. |
| `recent_changes(target, limit?)` | Novetats de l'últim cicle d'escaneig, en una crida. |

`target` pot ser una IP, un CIDR (/16 o més estret) o un nom de host (resolt pel servidor). Detalls,
paràmetres i camps de resposta: [Eines](https://mesalles.github.io/horizon-mcp/referencia/eines/) i
[Camps de resposta](https://mesalles.github.io/horizon-mcp/referencia/camps/) al manual.

> **Interpreteu les CVE amb cura.** HORIZON les infereix del producte i la versió detectats (CPE), no
> les verifica. Vegeu [Interpretar les CVE](https://mesalles.github.io/horizon-mcp/guies/interpretar-cve/).

## Instal·lació ràpida

Requisits: Python ≥ 3.13, [uv](https://docs.astral.sh/uv/) i una clau d'API d'HORIZON (interfície web:
menú d'usuari → **Mi perfil** → **Información**).

```bash
git clone https://github.com/mesalles/horizon-mcp.git
cd horizon-mcp
uv sync
cp .env.example .env        # i poseu-hi HORIZON_API_KEY
uv run horizon-mcp --ping   # comprova clau, connectivitat i inventari sense arrencar el servidor
```

Després, al manual:

- [Primer ús](https://mesalles.github.io/horizon-mcp/tutorials/primer-us/) (pas a pas fins a la primera pregunta)
- [Connectar Claude Desktop](https://mesalles.github.io/horizon-mcp/guies/claude-desktop/) ·
  [Connectar Claude Code](https://mesalles.github.io/horizon-mcp/guies/claude-code/) ·
  [Provar sense cap client](https://mesalles.github.io/horizon-mcp/guies/provar-sense-client/)
- [Servei compartit (HTTP)](https://mesalles.github.io/horizon-mcp/guies/servei-compartit/) amb token per als clients
- [Configuració](https://mesalles.github.io/horizon-mcp/referencia/configuracio/) ·
  [Línia d'ordres](https://mesalles.github.io/horizon-mcp/referencia/cli/) ·
  [Les dades d'HORIZON](https://mesalles.github.io/horizon-mcp/referencia/dades-horizon/) ·
  [Seguretat](https://mesalles.github.io/horizon-mcp/explicacio/seguretat/)

## Desenvolupament

```bash
uv sync
uv run pytest
```

Els tests no toquen HORIZON: fan servir mostres amb la forma exacta de les respostes reals i adreces
de documentació (192.0.2.0/24). El manual és a `docs/` (MkDocs Material, català i castellà) i es
publica a GitHub Pages en fusionar a `main`; `mkdocs build --strict` es comprova a cada PR.

## Condicions d'ús d'HORIZON

Les condicions del portal prohibeixen «cualquier tipo de automatización» pensant en la interfície web.
Aquest servidor fa servir l'**API oficial** que IRISCERT ha activat per a les institucions, només en
lectura i amb ritme limitat. Tot i això, si el desplegueu com a servei compartit, és recomanable
informar-ne IRISCERT.

## Llicència

MIT. Vegeu [LICENSE](LICENSE).

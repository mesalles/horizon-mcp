# horizon-mcp · Manual d'usuari

**horizon-mcp** és un servidor [MCP](explicacio/que-es-mcp.md) de **només lectura** sobre
l'API d'**HORIZON**, la plataforma de monitoratge de la superfície d'exposició externa que
RedIRIS posa a disposició de les universitats públiques. Permet que un assistent d'IA (Claude
Desktop, Claude Code o qualsevol client MCP) respongui preguntes d'un analista del SOC:

- «Què exposa a Internet el host 192.0.2.41?»
- «Quins serveis del rang 192.0.2.0/24 tenen CVE amb CVSS ≥ 9?»
- «Quins panells d'administració tenim exposats?»
- «Què ha aparegut de nou a l'últim cicle d'escaneig?»

Cada institució n'executa la seva còpia amb la seva pròpia clau d'API. Al codi no hi ha res
d'específic de cap institució.

## Per on començar

| Vols… | Vés a |
|---|---|
| Instal·lar-lo i fer la primera pregunta | [Primer ús](tutorials/primer-us.md) |
| Connectar-lo a un client, muntar-lo com a servei, preguntar millor | [Guies pràctiques](guies/instal-lar.md) |
| Saber exactament què retorna cada eina i què vol dir cada camp | [Referència](referencia/eines.md) |
| Entendre per què està fet així i què implica per a la seguretat | [Explicació](explicacio/que-es-mcp.md) |

## Tres coses a saber abans

- **No escriu res.** Totes les eines són consultes de lectura a HORIZON. No llança escanejos
  ni modifica l'inventari.
- **La clau d'API no surt mai del servidor**: ni al model, ni als registres, ni als errors.
- **Les CVE són inferides**, no verificades: HORIZON les dedueix del producte i la versió
  detectats. Vegeu [Interpretar les CVE](guies/interpretar-cve.md).

Els termes fixos del manual són al [Glossari](referencia/glossari.md).

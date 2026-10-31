# Primer ús

En un quart d'hora: instal·lar horizon-mcp, posar-hi la clau d'API, comprovar que parla amb
HORIZON, connectar-lo a Claude Code i fer la primera pregunta.

## Abans de començar

- Python 3.13 o superior i [uv](https://docs.astral.sh/uv/) instal·lats.
- La clau d'API del compte d'HORIZON de la teva institució. És a la interfície web
  d'HORIZON: menú d'usuari (a dalt a la dreta) → **Mi perfil** → **Información**.
- Claude Code instal·lat (per al pas 4). Si fas servir Claude Desktop, segueix
  [Connectar Claude Desktop](../guies/claude-desktop.md) en lloc del pas 4.

## 1. Instal·la

```bash
git clone https://github.com/mesalles/horizon-mcp.git
cd horizon-mcp
uv sync
```

`uv sync` crea un entorn virtual dins del projecte amb les dependències exactes.

## 2. Posa la clau

```bash
cp .env.example .env
```

Obre `.env` amb un editor i escriu la clau a la línia `HORIZON_API_KEY=`. El fitxer `.env`
és al `.gitignore`: no es pujarà mai al repositori.

## 3. Comprova la connexió

```bash
uv run horizon-mcp --ping
```

Fa tres crides reals a HORIZON (versió de l'API, compte, inventari) i surt. Si tot va bé
mostra una cosa així:

```text
API: horizon-api 2.5.3 status=ok
Account(s): 00000000-0000-4000-8000-000000000001
Ranges: 192.0.2.0/24
Root domains: (none)
User-Agent accepted: 'horizon-mcp/0.2.0 (+https://github.com/mesalles/horizon-mcp)'
Client bearer token (streamable-http): not set
```

`Ranges` són els rangs IP que HORIZON vigila per al teu compte. `Root domains` és normalment
buit als comptes provisionats per RedIRIS.

## 4. Connecta'l a Claude Code

```bash
claude mcp add --transport stdio --scope user horizon -- uv run --directory /ruta/absoluta/a/horizon-mcp horizon-mcp
```

Substitueix `/ruta/absoluta/a/horizon-mcp` per la carpeta on l'has clonat. Obre Claude Code i
escriu `/mcp`: ha de llistar el servidor `horizon` amb les seves eines.

## 5. Fes la primera pregunta

Dins de Claude Code, demana:

> Quins rangs vigila HORIZON per a la nostra institució?

El model cridarà l'eina `inventory` i et respondrà amb els rangs. Després, amb una adreça
d'un dels rangs:

> Què exposa a Internet el host 192.0.2.41?

Ara cridarà `exposure_summary` i et farà un resum: ports i serveis, fitxa HTTP, CVE per servei,
troballes web i certificats.

## Com saber que ha funcionat

- `--ping` ha mostrat `status=ok` i almenys un rang.
- `/mcp` a Claude Code mostra `horizon` connectat.
- La resposta a la pregunta del host cita ports i serveis concrets, i una data d'última
  observació.

## Si falla

- **`HORIZON_API_KEY is not set`**: el `.env` no és a l'arrel del projecte o la línia és
  buida.
- **`HORIZON rejected the API key (HTTP 401)`**: la clau és incorrecta o ha caducat. Torna-la a
  copiar d'HORIZON.
- **`HORIZON's WAF (Cloudflare) blocked the request`**: el tallafoc d'HORIZON rebutja el
  *User-Agent*. Vegeu [Diagnosticar problemes](../guies/diagnosticar.md).
- **`/mcp` no mostra `horizon`**: la ruta de `--directory` no és absoluta o no és correcta.
  Torna a executar `claude mcp add` amb la ruta bona.
- A Windows, si `uv` no es troba des del client, posa la ruta completa de `uv.exe`
  (vegeu [Connectar Claude Desktop](../guies/claude-desktop.md)).

## Següents passos

- [Preguntar bé](../guies/preguntar-be.md): quina eina fa servir el model per a cada pregunta.
- [Interpretar les CVE](../guies/interpretar-cve.md): abans de reportar res.
- [Seguretat](../explicacio/seguretat.md): on van les dades que consultes.

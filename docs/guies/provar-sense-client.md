# Provar sense cap client

Tres maneres de comprovar el servidor sense Claude Desktop ni Claude Code, de menys a més
completa.

## 1. Validar la configuració (`--check`)

```bash
uv run horizon-mcp --check
```

Llegeix el `.env` i l'entorn, comprova que la clau hi és i els valors són vàlids, i surt
sense fer cap crida. Mostra l'URL de l'API i si hi ha token de clients configurat (mai el
valor).

## 2. Crida real a HORIZON (`--ping`)

```bash
uv run horizon-mcp --ping
```

Crida l'arrel de l'API, el compte i l'inventari (rangs i dominis arrel) i els imprimeix.
És la prova de connectivitat, clau i *User-Agent* en una sola ordre.

## 3. Executar eines a mà (MCP Inspector)

L'[MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) és una interfície web
per cridar eines d'un servidor MCP sense cap model. Requereix Node.js (fa servir `npx`).

```bash
uv run mcp dev inspector.py
```

1. La consola imprimeix una URL **amb un token**: obre-la sencera al navegador.
2. Prem **Connect**.
3. Pestanya **Tools** → **List Tools**: apareixen les nou eines.
4. Tria'n una (per exemple `open_ports`), omple `target` amb una IP o un CIDR del teu
   inventari i prem **Run Tool**. El resultat és el JSON exacte que rebria el model.

`inspector.py` només importa el servidor com a paquet: `mcp dev` no pot carregar `server.py`
directament.

Amb `--log-level DEBUG`, el servidor mostra per `stderr` cada petició HTTP que fa a HORIZON:

```bash
uv run horizon-mcp --log-level DEBUG --ping
```

## Com saber que ha funcionat

- `--check`: `configuration OK`.
- `--ping`: `status=ok`, un compte i almenys un rang.
- Inspector: `List Tools` mostra nou eines i `Run Tool` d'`inventory` retorna els rangs.

## Si falla

- **`--ping` dóna 401**: clau incorrecta.
- **`--ping` dóna 403 amb HTML**: el tallafoc d'HORIZON rebutja el *User-Agent*; vegeu
  [Diagnosticar problemes](diagnosticar.md).
- **`mcp dev` diu que falta `npx`**: instal·la Node.js.
- **L'Inspector no connecta**: has obert la URL sense el token, o has tancat la consola que
  l'executa.

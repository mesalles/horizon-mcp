# Servei compartit (HTTP)

El mateix servidor pot córrer com a servei per a tot un equip, amb el transport
`streamable-http`. Com que parla amb HORIZON amb la clau de la institució, **qui arriba al
port veu tot el que veu la clau**: per això demana un secret compartit als clients i es nega
a obrir un port accessible sense cap autenticació.

## Com decideix si arrenca

| `--host` | `HORIZON_MCP_BEARER_TOKEN` | Resultat |
|---|---|---|
| loopback (`127.0.0.1`, `::1`, `localhost`) | qualsevol | Arrenca. Sense token, només hi arriba qui ja és a la màquina (o el proxy). |
| una altra adreça (`0.0.0.0`, una IP) | definit | Arrenca; cada petició ha de portar `Authorization: Bearer <token>`, si no rep `401`. |
| una altra adreça | no definit | **Es nega a arrencar** amb un missatge clar. `--allow-unauthenticated` ho força, per a qui ja autentica al proxy i n'assumeix el risc. |

En `stdio` no s'aplica cap autenticació: qui llança el procés és qui l'usa.

## Passos

1. Genera un secret i posa'l al `.env`:

    ```bash
    python -c "import secrets; print(secrets.token_urlsafe(32))"
    ```

    ```text
    HORIZON_MCP_BEARER_TOKEN=<el valor generat>
    ```

2. Arrenca'l escoltant només a la màquina, darrere d'un proxy invers amb TLS (Caddy, nginx,
   Traefik…) que exposi només `/mcp`:

    ```bash
    uv run horizon-mcp --transport streamable-http --host 127.0.0.1 --port 8000
    ```

    El TLS és feina del proxy; el servidor no en fa.

3. Registra el servei als clients amb el token a la capçalera:

    ```bash
    claude mcp add --transport http horizon https://el-vostre-host/mcp --header "Authorization: Bearer <token>"
    ```

## Com saber que ha funcionat

- El registre d'arrencada diu `streamable-http on 127.0.0.1:8000/mcp, clients must send a
  Bearer token`.
- Una petició sense capçalera rep `401` amb `WWW-Authenticate: Bearer realm="horizon-mcp"`.
- `/mcp` a Claude Code mostra el servidor connectat per HTTP.

## Si falla

- **`refusing to listen on … without client authentication`**: has posat un `--host` que no
  és loopback sense token. Defineix `HORIZON_MCP_BEARER_TOKEN` o escolta a `127.0.0.1`.
- **El registre diu `WITHOUT client authentication`**: no hi ha token; només és acceptable
  a loopback darrere d'un proxy que autentiqui.
- **Els clients reben `401 Invalid token`**: el token del client i el del servidor no
  coincideixen (espais al final, cometes).
- **Les respostes s'aturen a mitges darrere del proxy**: el proxy ha de permetre respostes
  en flux (*server-sent events*) sense emmagatzemar-les.

!!! warning "Un sol secret per instància"
    El token és un únic secret compartit, comparat en temps constant; no hi ha usuaris ni
    permisos. L'autenticació per persona, si un dia cal, és feina del proxy. Si el desplegueu
    com a servei compartit, és recomanable informar-ne IRISCERT.

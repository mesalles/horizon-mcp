# Servicio compartido (HTTP)

El mismo servidor puede correr como servicio para todo un equipo, con el transporte
`streamable-http`. Como habla con HORIZON con la clave de la institución, **quien llega al
puerto ve todo lo que ve la clave**: por eso pide un secreto compartido a los clientes y se
niega a abrir un puerto accesible sin ninguna autenticación.

## Cómo decide si arranca

| `--host` | `HORIZON_MCP_BEARER_TOKEN` | Resultado |
|---|---|---|
| loopback (`127.0.0.1`, `::1`, `localhost`) | cualquiera | Arranca. Sin token, solo llega quien ya está en la máquina (o el proxy). |
| otra dirección (`0.0.0.0`, una IP) | definido | Arranca; cada petición debe llevar `Authorization: Bearer <token>`, si no recibe `401`. |
| otra dirección | no definido | **Se niega a arrancar** con un mensaje claro. `--allow-unauthenticated` lo fuerza, para quien ya autentica en el proxy y asume el riesgo. |

En `stdio` no se aplica ninguna autenticación: quien lanza el proceso es quien lo usa.

## Pasos

1. Genera un secreto y ponlo en el `.env`:

    ```bash
    python -c "import secrets; print(secrets.token_urlsafe(32))"
    ```

    ```text
    HORIZON_MCP_BEARER_TOKEN=<el valor generado>
    ```

2. Arráncalo escuchando solo en la máquina, detrás de un proxy inverso con TLS (Caddy,
   nginx, Traefik…) que exponga solo `/mcp`:

    ```bash
    uv run horizon-mcp --transport streamable-http --host 127.0.0.1 --port 8000
    ```

    El TLS es trabajo del proxy; el servidor no lo hace.

3. Registra el servicio en los clientes con el token en la cabecera:

    ```bash
    claude mcp add --transport http horizon https://vuestro-host/mcp --header "Authorization: Bearer <token>"
    ```

## Cómo saber que ha funcionado

- El registro de arranque dice `streamable-http on 127.0.0.1:8000/mcp, clients must send a
  Bearer token`.
- Una petición sin cabecera recibe `401` con `WWW-Authenticate: Bearer realm="horizon-mcp"`.
- `/mcp` en Claude Code muestra el servidor conectado por HTTP.

## Si falla

- **`refusing to listen on … without client authentication`**: has puesto un `--host` que no
  es loopback sin token. Define `HORIZON_MCP_BEARER_TOKEN` o escucha en `127.0.0.1`.
- **El registro dice `WITHOUT client authentication`**: no hay token; solo es aceptable en
  loopback detrás de un proxy que autentique.
- **Los clientes reciben `401 Invalid token`**: el token del cliente y el del servidor no
  coinciden (espacios al final, comillas).
- **Las respuestas se cortan a medias detrás del proxy**: el proxy debe permitir respuestas
  en flujo (*server-sent events*) sin almacenarlas.

!!! warning "Un solo secreto por instancia"
    El token es un único secreto compartido, comparado en tiempo constante; no hay usuarios ni
    permisos. La autenticación por persona, si algún día hace falta, es trabajo del proxy. Si
    lo desplegáis como servicio compartido, es recomendable informar a IRISCERT.

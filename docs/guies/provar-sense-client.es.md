# Probar sin ningún cliente

Tres maneras de comprobar el servidor sin Claude Desktop ni Claude Code, de menos a más
completa.

## 1. Validar la configuración (`--check`)

```bash
uv run horizon-mcp --check
```

Lee el `.env` y el entorno, comprueba que la clave está y los valores son válidos, y sale sin
hacer ninguna llamada. Muestra la URL de la API y si hay token de clientes configurado (nunca
el valor).

## 2. Llamada real a HORIZON (`--ping`)

```bash
uv run horizon-mcp --ping
```

Llama a la raíz de la API, la cuenta y el inventario (rangos y dominios raíz) y los imprime.
Es la prueba de conectividad, clave y *User-Agent* en un solo comando.

## 3. Ejecutar herramientas a mano (MCP Inspector)

El [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) es una interfaz web
para llamar a herramientas de un servidor MCP sin ningún modelo. Requiere Node.js (usa
`npx`).

```bash
uv run mcp dev inspector.py
```

1. La consola imprime una URL **con un token**: ábrela entera en el navegador.
2. Pulsa **Connect**.
3. Pestaña **Tools** → **List Tools**: aparecen las nueve herramientas.
4. Elige una (por ejemplo `open_ports`), rellena `target` con una IP o un CIDR de tu
   inventario y pulsa **Run Tool**. El resultado es el JSON exacto que recibiría el modelo.

`inspector.py` solo importa el servidor como paquete: `mcp dev` no puede cargar `server.py`
directamente.

Con `--log-level DEBUG`, el servidor muestra por `stderr` cada petición HTTP que hace a
HORIZON:

```bash
uv run horizon-mcp --log-level DEBUG --ping
```

## Cómo saber que ha funcionado

- `--check`: `configuration OK`.
- `--ping`: `status=ok`, una cuenta y al menos un rango.
- Inspector: `List Tools` muestra nueve herramientas y `Run Tool` de `inventory` devuelve los
  rangos.

## Si falla

- **`--ping` da 401**: clave incorrecta.
- **`--ping` da 403 con HTML**: el cortafuegos de HORIZON rechaza el *User-Agent*; véase
  [Diagnosticar problemas](diagnosticar.md).
- **`mcp dev` dice que falta `npx`**: instala Node.js.
- **El Inspector no conecta**: has abierto la URL sin el token, o has cerrado la consola que
  lo ejecuta.

# Seguridad

## Lo que protege el servidor

- **La clave de API nunca sale.** Solo vive en el entorno del proceso y en la cabecera de las
  peticiones a HORIZON. No aparece en el modelo, en los registros (ni con `DEBUG`), en los
  errores ni en las salidas de `--check` y `--ping`.
- **Solo lectura.** Ninguna herramienta puede modificar nada en HORIZON.
- **Objetivos acotados.** Se rechazan los CIDR más anchos que /16 y los nombres que resuelven
  a más de 4 direcciones, para evitar consultas desmesuradas.

## Lo que debes proteger tú

**El `.env`.** Quien lo lee tiene la clave de la institución. Permisos de archivo
restrictivos, nunca en git, nunca en capturas de pantalla.

**El puerto, en modo HTTP.** Quien llega al puerto ve todo lo que ve la clave. El servidor
impone un mínimo: se niega a escuchar en una dirección que no sea loopback sin un token de
clientes (`HORIZON_MCP_BEARER_TOKEN`). El resto es trabajo del despliegue: proxy inverso con
TLS, exponer solo `/mcp`, y autenticación por persona en el proxy si hace falta. El token es
un único secreto compartido, sin usuarios ni permisos.

**Adónde van los resultados.** Esto es lo que ningún aviso del servidor te puede ahorrar: los
resultados de las consultas (puertos, servicios, CVE, hallazgos) los recibe el **modelo**, y
el modelo corre donde corra el cliente. Con Claude Desktop o Claude Code, los datos de
exposición de la institución viajan al proveedor del modelo como parte de la conversación.
Es una decisión de la institución si eso es aceptable, con qué proveedor y bajo qué contrato;
el servidor no pone ningún límite porque no puede saber qué cliente hay detrás.

## Condiciones de uso de HORIZON

Las condiciones del portal prohíben «cualquier tipo de automatización» pensando en la
interfaz web. Este servidor usa la **API oficial** que IRISCERT ha activado para las
instituciones, solo en lectura y con ritmo limitado (0,5 s entre peticiones). Si lo
desplegáis como servicio compartido, es recomendable informar a IRISCERT.

## Qué no hace

- No autentica personas (en `stdio`, quien lanza el proceso es quien lo usa).
- No cifra: en modo HTTP, el TLS es del proxy.
- No registra quién ha preguntado qué; si hace falta una pista de auditoría por persona, la
  debe dar el cliente o el proxy.

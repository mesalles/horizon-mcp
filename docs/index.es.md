# horizon-mcp · Manual de usuario

**horizon-mcp** es un servidor [MCP](explicacio/que-es-mcp.md) de **solo lectura** sobre la
API de **HORIZON**, la plataforma de monitorización de la superficie de exposición externa
que RedIRIS pone a disposición de las universidades públicas. Permite que un asistente de IA
(Claude Desktop, Claude Code o cualquier cliente MCP) responda preguntas de un analista del
SOC:

- «¿Qué expone a Internet el host 192.0.2.41?»
- «¿Qué servicios del rango 192.0.2.0/24 tienen CVE con CVSS ≥ 9?»
- «¿Qué paneles de administración tenemos expuestos?»
- «¿Qué ha aparecido de nuevo en el último ciclo de escaneo?»

Cada institución ejecuta su propia copia con su propia clave de API. En el código no hay
nada específico de ninguna institución.

## Por dónde empezar

| Quieres… | Ve a |
|---|---|
| Instalarlo y hacer la primera pregunta | [Primer uso](tutorials/primer-us.md) |
| Conectarlo a un cliente, montarlo como servicio, preguntar mejor | [Guías prácticas](guies/instal-lar.md) |
| Saber exactamente qué devuelve cada herramienta y qué significa cada campo | [Referencia](referencia/eines.md) |
| Entender por qué está hecho así y qué implica para la seguridad | [Explicación](explicacio/que-es-mcp.md) |

## Tres cosas que conviene saber antes

- **No escribe nada.** Todas las herramientas son consultas de lectura a HORIZON. No lanza
  escaneos ni modifica el inventario.
- **La clave de API nunca sale del servidor**: ni al modelo, ni a los registros, ni a los
  errores.
- **Las CVE son inferidas**, no verificadas: HORIZON las deduce del producto y la versión
  detectados. Véase [Interpretar las CVE](guies/interpretar-cve.md).

Los términos fijos del manual están en el [Glosario](referencia/glossari.md).

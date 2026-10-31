# Interpretar las CVE

HORIZON **infiere** las CVE: detecta un producto y una versión (un CPE) en un servicio y
busca las CVE que afectan a esa versión. No verifica nada por explotación. Las herramientas
`cves`, `exposure_summary` y `recent_changes` te lo recuerdan, y el servidor también se lo
recuerda al modelo.

## De dónde salen los falsos positivos

- **Backports de distribución.** Ubuntu o Debian mantienen versiones antiguas con parches de
  seguridad sin cambiar el número de versión. Un `nginx 1.18.0` de Ubuntu puede tener
  corregida una CVE que NVD atribuye a «1.18.0».
- **Rangos de versión abiertos en NVD.** Algunas CVE afectan «hasta la versión X» sin límite
  inferior claro, y se asignan a versiones que no tienen nada que ver.
- **CPE sin versión.** Un CPE acabado en `-` significa «versión desconocida»; las CVE
  asignadas son aún menos fiables.
- **CPE sintetizados.** Los CPE de la ficha HTTP (`http_services`) se construyen a partir de
  nombres de tecnologías y pueden no existir en el diccionario de NVD. Para CVE, usa los CPE
  de `open_ports`.

## Cómo leer un grupo de CVE

Las CVE llegan **agrupadas por servicio** (IP, puerto, CPE), ordenadas por el CVSS máximo:

```json
{
  "ip": "192.0.2.41", "port": 80, "cpe": "cpe:/a:apache:http_server:2.4.52",
  "cve_count": 3, "max_cvss": 9.8, "severity": "critical",
  "cves": [{"cve": "CVE-2022-31813", "cvss": 9.8, "severity": "critical"}, "…"],
  "first_seen": "2026-08-06", "last_seen": "2026-09-15",
  "days_since_last_seen": 5, "new_cves": 0
}
```

- `cve_count` es el número real; en `exposure_summary` la lista `cves` se corta a las 10 de
  CVSS más alto (`cves_truncated` dice cuántas faltan).
- `new_cves`: cuántas se han visto por primera vez en el último ciclo.
- `observed_in_latest_cycle` (en `exposure_summary`): `false` significa que el grupo no se ha
  vuelto a observar en el último ciclo de servicios del host; probablemente es histórico.

## Procedimiento antes de reportar

1. Confirma que el servicio sigue ahí: `last_seen` reciente y `observed_in_latest_cycle` no
   es `false`.
2. Comprueba la versión real en el host (gestor de paquetes, cabeceras) y si la distribución
   ha aplicado el parche (`apt changelog`, avisos de seguridad de la distribución).
3. Da prioridad a `max_cvss` y a la severidad, pero lee la CVE concreta: una 9.8 en un
   módulo que no usáis no es una urgencia.
4. Repórtalo como «potencialmente afectado por…», no como «vulnerable a…».

## Cómo saber que ha funcionado

- Tu informe cita la fecha de observación, la versión detectada (CPE) y la verificación
  hecha en el host.

## Si falla

- **Demasiadas CVE para procesar**: pasa `min_cvss` (por ejemplo 7.0) o estrecha el objetivo.
- **El mismo servicio sale varias veces**: puede tener más de un CPE (producto y sistema
  operativo); cada CPE es un grupo.
- **La CVE no aparece en NVD con esa versión**: es un caso de rango abierto o de CPE
  sintetizado; descártala con la comprobación en el host.

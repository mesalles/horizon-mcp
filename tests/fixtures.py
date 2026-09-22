"""Sample HORIZON rows, shaped exactly like the real API (horizon-api 2.5.3) but with
TEST-NET addresses and generic hostnames."""

ACCOUNT = "00000000-0000-4000-8000-000000000001"
CYCLE_MS = 1789439036475  # 2026-09-15 UTC, a real cycle timestamp shape
OLDER_MS = 1785982834323

GEO = {
    "region_iso_code": "ES-CS", "continent_name": "Europe", "city_name": "Somewhere",
    "country_iso_code": "ES", "country_name": "Spain", "region_name": "Region",
    "location": {"lat": 40.0, "lon": 0.0},
}


def asn(ip: str) -> dict:
    return {"ip": ip, "organization_name": "Example NREN", "asn": 64496, "network": "192.0.2.0/24"}


def envelope(data: list, *, hits: int | None = None, scroll_id: str | None = "v1.scroll") -> dict:
    return {"ok": True, "error": "", "hits": hits if hits is not None else len(data),
            "size": len(data), "data": data, "scroll_id": scroll_id}


def port(ip: str, port: int, service: str, product: str | None, cpes: list[str], *,
         ssl: bool = False, new: bool = False) -> dict:
    row = {
        "extended_domain": [], "first_seen": OLDER_MS, "account_ids": [ACCOUNT],
        "data": "HTTP/1.1 200 OK\\r\\nServer: x\\r\\n\\r\\n", "last_seen": CYCLE_MS,
        "ip": ip, "transport": "TCP", "ssl": ssl, "port": port, "cpes": cpes,
        "service": service, "geoip": GEO, "asn": asn(ip), "ip_origins": ["192.0.2.0/24"],
        "is_new": new,
    }
    if product is not None:  # vendorproduct is optional in the real API
        row["vendorproduct"] = product
    return row


def cve(ip: str, port: int, cve_id: str, cvss: float, severity: str, cpe: str, *,
        new: bool = False) -> dict:
    return {
        "severity": severity, "extended_domain": [], "cve": cve_id, "account_ids": [ACCOUNT],
        "first_seen": CYCLE_MS if new else OLDER_MS, "last_seen": CYCLE_MS, "port": port,
        "ip": ip, "matched_cpe": [cpe], "cvss": cvss, "geoip": GEO, "asn": asn(ip),
        "ip_origins": ["192.0.2.0/24"], "is_new": new,
    }


def web(ip: str, url: str, name: str, severity: str, *, new: bool = False) -> dict:
    return {
        "severity": severity, "extended_domain": [], "account_ids": [ACCOUNT],
        "first_seen": OLDER_MS, "last_seen": OLDER_MS, "ssl": False, "url": url,
        "name": name, "timestamp": CYCLE_MS, "geoip": GEO, "asn": asn(ip),
        "ip_origins": ["192.0.2.0/24"], "is_new": new,
    }


def tls(ip: str, port: int, cn: str, sans: list[str], *, mismatched: bool = True) -> dict:
    return {
        "extended_domain": [], "status_code": 200, "account_ids": [ACCOUNT],
        "first_seen": OLDER_MS, "scheme": "https", "last_seen": CYCLE_MS, "ip": ip,
        "url": f"https://{ip}:{port}", "port": port,
        "cpes": ["cpe:2.3:a:apache:http_server:2.4.18:*:*:*:*:*:*:*"],
        "raw_header": "HTTP/1.1 200 OK\r\n\r\n",
        "tls": {
            "cipher": "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
            "issuer_dn": "CN=R11, O=Let's Encrypt, C=US", "issuer_cn": "R11",
            "not_before": "2026-09-10T13:44:05Z", "tls_version": "tls12",
            "subject_an": sans, "probe_status": True, "not_after": "2026-12-09T13:44:04Z",
            "subject_cn": cn, "mismatched": mismatched, "subject_dn": f"CN={cn}",
            "issuer_org": ["Let's Encrypt"], "tls_connection": "ctls", "port": str(port),
            "serial": "06:B0:18", "host": ip,
            "fingerprint_hash": {"sha1": "a" * 40, "sha256": "b" * 64, "md5": "c" * 32},
        },
        "is_new": False,
    }


def http(ip: str, port: int, scheme: str, status: int, title: str, tech: list[str] | None,
         cpes: list[str]) -> dict:
    row = {
        "extended_domain": [], "status_code": status, "account_ids": [ACCOUNT],
        "first_seen": OLDER_MS, "scheme": scheme, "last_seen": CYCLE_MS, "title": title,
        "content_type": "text/html", "content_length": 1234, "ip": ip,
        "url": f"{scheme}://{ip}:{port}", "port": port, "cpes": cpes,
        "raw_header": "HTTP/1.1 200 OK\r\n\r\n", "geoip": GEO, "asn": asn(ip),
        "ip_origins": ["192.0.2.0/24"], "is_new": False,
    }
    if tech is not None:  # tech is optional in the real API
        row["tech"] = tech
    return row


def eol(ip: str, cpes: list[str], eol_map: dict) -> dict:
    return {
        "extended_domain": [], "account_ids": [ACCOUNT], "data": "HTTP/1.1 200 OK",
        "ssl": False, "cpes": cpes, "geoip": GEO, "asn": asn(ip), "eol": eol_map,
    }


# --- A small, realistic /24 --------------------------------------------------------

PORTS = [
    port("192.0.2.41", 80, "http", "Apache httpd",
         ["cpe:/a:apache:http_server:2.4.52", "cpe:/o:canonical:ubuntu_linux:-"]),
    port("192.0.2.41", 22, "ssh", "OpenSSH",
         ["cpe:/a:openbsd:openssh:8.9p1", "cpe:/o:canonical:ubuntu_linux", "cpe:/o:linux:linux_kernel"]),
    port("192.0.2.41", 8080, "http", "nginx", ["cpe:/a:f5:nginx:1.18.0", "cpe:/o:canonical:ubuntu_linux:-"]),
    port("192.0.2.53", 443, "http", "Apache httpd", ["cpe:/a:apache:http_server:2.4.68"], ssl=True),
    port("192.0.2.53", 8888, "http", None, []),
    port("192.0.2.34", 2200, "ssh", "OpenSSH", ["cpe:/a:openbsd:openssh:10.4"], new=True),
]

CVES = [
    cve("192.0.2.41", 80, "CVE-2006-20001", 7.5, "high", "cpe:/a:apache:http_server:2.4.52"),
    cve("192.0.2.41", 80, "CVE-2022-31813", 9.8, "critical", "cpe:/a:apache:http_server:2.4.52"),
    cve("192.0.2.41", 80, "CVE-2023-25690", 9.8, "critical", "cpe:/a:apache:http_server:2.4.52"),
    cve("192.0.2.41", 8080, "CVE-2021-23017", 7.7, "high", "cpe:/a:f5:nginx:1.18.0"),
    cve("192.0.2.34", 2200, "CVE-2007-2768", 4.3, "medium", "cpe:/a:openbsd:openssh:10.4", new=True),
    cve("192.0.2.34", 2200, "CVE-2023-51767", 7.0, "high", "cpe:/a:openbsd:openssh:10.4", new=True),
]

WEB = [
    web("192.0.2.36", "http://192.0.2.36:80/.oast.me", "Aplicación web con vulnerabilidad de redirección abierta", "medium"),
    web("192.0.2.36", "http://192.0.2.36:80////oast.me", "Aplicación web con vulnerabilidad de redirección abierta", "medium"),
    web("192.0.2.36", "http://192.0.2.36:80/////oast.me@//", "Aplicación web con vulnerabilidad de redirección abierta", "medium"),
    web("192.0.2.46", "https://192.0.2.46:9090/", "Panel de Inicio de Sesión de Cockpit Expuesto", "panel"),
    web("192.0.2.41", "http://192.0.2.41:80", "Servidor web con listado de directorios habilitado", "info"),
    web("192.0.2.33", "https://192.0.2.33/time.php", "Exposición de información sensible mediante página PHPinfo", "low"),
]

TLS = [tls("192.0.2.136", 443, "web.example.edu", ["web.example.edu", "www.example.edu"])]

HTTP = [
    http("192.0.2.41", 80, "http", 200, "Index of /", ["Apache HTTP Server:2.4.52", "Ubuntu"],
         ["cpe:2.3:a:apache:http_server:2.4.52:*:*:*:*:*:*:*"]),
    http("192.0.2.41", 8080, "http", 200, "Labelling app", None,
         ["cpe:2.3:a:f5:nginx:1.18.0:*:*:*:*:*:*:*"]),
    http("192.0.2.53", 443, "https", 200, "Welcome", ["Apache HTTP Server:2.4.68"],
         ["cpe:2.3:a:apache:http_server:2.4.68:*:*:*:*:*:*:*"]),
]

EOL = [
    eol("192.0.2.41", ["cpe:/a:f5:nginx:1.18.0", "cpe:/o:canonical:ubuntu_linux:-"], {
        "cpe:/a:f5:nginx:1.18.0": {
            "release_cycle": "1.18", "release_date": "2020-04-21", "eol_date": "2021-04-20",
            "latest": "1.18.0", "latest_release_date": "2020-04-21", "is_eol": True,
        }
    }),
]

"""Turn raw HORIZON rows into compact, model-friendly records.

Raw rows carry ~40 % noise for our purpose (``geoip``, ``asn``, ``account_ids``,
``ip_origins``, raw banners). Everything here is pure and synchronous so it is
trivially unit-testable with captured fixtures.
"""

from __future__ import annotations

import ipaddress
from collections import defaultdict
from datetime import UTC, date, datetime
from typing import Any
from urllib.parse import urlsplit


class TargetError(ValueError):
    """The target is not an IPv4/IPv6 address or CIDR we are willing to query."""


# ----------------------------------------------------------------------------- targets


def validate_target(target: str, *, min_prefix_len: int = 16) -> str:
    """Return a canonical IP or CIDR string, or raise :class:`TargetError`.

    HORIZON's ``ip`` filter accepts a single address or a CIDR. We refuse
    hostnames (the API would 422 anyway) and prefixes wider than *min_prefix_len*
    to avoid accidentally asking for half the Internet.
    """
    value = (target or "").strip()
    if not value:
        raise TargetError("target is empty; pass an IP address or a CIDR such as 192.0.2.0/24")
    try:
        if "/" in value:
            net = ipaddress.ip_network(value, strict=False)
            if net.version == 4 and net.prefixlen < min_prefix_len:
                raise TargetError(
                    f"prefix /{net.prefixlen} is too wide; use /{min_prefix_len} or narrower"
                )
            return str(net)
        return str(ipaddress.ip_address(value))
    except ValueError as exc:
        raise TargetError(
            f"{value!r} is not an IP address or CIDR. HORIZON is queried by address range, "
            "not by hostname: resolve the name first."
        ) from exc


# ----------------------------------------------------------------------------- helpers


def ms_to_date(value: Any) -> str | None:
    """Epoch milliseconds -> ``YYYY-MM-DD`` (UTC). Returns None when missing."""
    if value in (None, "", 0):
        return None
    try:
        return datetime.fromtimestamp(int(value) / 1000, tz=UTC).strftime("%Y-%m-%d")
    except (TypeError, ValueError, OSError):
        return None


def today() -> date:
    """Current UTC date. Kept as a function so tests can monkeypatch it."""
    return datetime.now(tz=UTC).date()


def days_since(date_str: str | None) -> int | None:
    """Whole days between a ``YYYY-MM-DD`` string and today (UTC). None when missing."""
    if not date_str:
        return None
    try:
        return (today() - date.fromisoformat(date_str)).days
    except ValueError:
        return None


def mark_latest_cycle(items: list[dict[str, Any]], cycle_date: str | None,
                      *, tolerance_days: int = 1) -> list[dict[str, Any]]:
    """Set ``observed_in_latest_cycle`` on each item by comparing its ``last_seen`` with
    *cycle_date* (the date of the latest scan cycle for the host, taken from ``/ports``).

    HORIZON's indices have different cadences, so a finding whose ``last_seen`` is
    months older than the host's services was most likely not re-observed and may be
    gone. Items are mutated in place and returned for convenience.
    """
    ref = date.fromisoformat(cycle_date) if cycle_date else None
    for item in items:
        seen = item.get("last_seen")
        if ref is None or not seen:
            item["observed_in_latest_cycle"] = None
            continue
        try:
            item["observed_in_latest_cycle"] = (ref - date.fromisoformat(seen)).days <= tolerance_days
        except ValueError:
            item["observed_in_latest_cycle"] = None
    return items


def cpe22_to_23(cpe: str) -> str:
    """Convert a CPE 2.2 URI (``cpe:/a:vendor:product:version``) to 2.3 formatted string.

    HORIZON mixes both formats (2.2 on /ports, /cves, /eol; 2.3 on /httpinfo, /tls).
    Already-2.3 strings are returned unchanged. ``-`` (unknown version) is kept as
    is: in 2.3 it means "no value", which is the closest meaning.
    """
    if not cpe or not cpe.startswith("cpe:/"):
        return cpe
    parts = cpe[len("cpe:/"):].split(":")
    parts += [""] * (7 - len(parts))
    part, vendor, product, version, update, edition, language = parts[:7]
    fields = [part, vendor, product, version, update, edition, language]
    fields = [f if f else "*" for f in fields]
    # 2.3 has four extra fields (sw_edition, target_sw, target_hw, other)
    return "cpe:2.3:" + ":".join(fields) + ":*:*:*:*"


def _port_from_url(url: str) -> tuple[str | None, int | None]:
    """Extract (host, port) from a URL, defaulting the port by scheme."""
    if not url:
        return None, None
    try:
        parts = urlsplit(url)
    except ValueError:
        return None, None
    port = parts.port
    if port is None:
        port = 443 if parts.scheme == "https" else 80 if parts.scheme == "http" else None
    return parts.hostname, port


# ----------------------------------------------------------------------------- rows


def port_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Compact view of one ``/ports`` row (Nmap-derived service)."""
    return {
        "ip": raw.get("ip"),
        "port": raw.get("port"),
        "transport": raw.get("transport"),
        "service": raw.get("service"),
        "product": raw.get("vendorproduct"),
        "tls": bool(raw.get("ssl")),
        "cpes": list(raw.get("cpes") or []),
        "first_seen": ms_to_date(raw.get("first_seen")),
        "last_seen": ms_to_date(raw.get("last_seen")),
        "days_since_last_seen": days_since(ms_to_date(raw.get("last_seen"))),
        "new": bool(raw.get("is_new")),
    }


def aggregate_cves(
    rows: list[dict[str, Any]],
    *,
    min_cvss: float = 0.0,
    max_cves_per_group: int | None = None,
) -> list[dict[str, Any]]:
    """Group ``/cves`` rows (one per CVE) into one record per (ip, port, CPE).

    Mirrors how a vulnerability manager would store it: the affected service with
    its list of CVEs, the highest CVSS, and the counts. Sorted by max CVSS desc.
    With *max_cves_per_group*, each group keeps only its top-N CVEs by CVSS while
    ``cve_count`` still reports the full number (``cves_truncated`` says how many).
    """
    groups: dict[tuple[str, int, str], dict[str, Any]] = {}
    for raw in rows:
        cvss = float(raw.get("cvss") or 0.0)
        if cvss < min_cvss:
            continue
        ip = raw.get("ip") or ""
        port = int(raw.get("port") or 0)
        cpes = raw.get("matched_cpe") or [None]
        for cpe in cpes:
            key = (ip, port, cpe or "")
            grp = groups.get(key)
            if grp is None:
                grp = groups[key] = {
                    "ip": ip,
                    "port": port,
                    "cpe": cpe,
                    "cve_count": 0,
                    "max_cvss": 0.0,
                    "severity": None,
                    "cves": [],
                    "first_seen": None,
                    "last_seen": None,
                    "new_cves": 0,
                }
            grp["cve_count"] += 1
            grp["cves"].append({"cve": raw.get("cve"), "cvss": cvss, "severity": raw.get("severity")})
            if cvss >= grp["max_cvss"]:
                grp["max_cvss"] = cvss
                grp["severity"] = raw.get("severity")
            fs, ls = ms_to_date(raw.get("first_seen")), ms_to_date(raw.get("last_seen"))
            grp["first_seen"] = min(filter(None, [grp["first_seen"], fs]), default=None)
            grp["last_seen"] = max(filter(None, [grp["last_seen"], ls]), default=None)
            if raw.get("is_new"):
                grp["new_cves"] += 1

    for grp in groups.values():
        grp["cves"].sort(key=lambda c: c["cvss"], reverse=True)
        grp["days_since_last_seen"] = days_since(grp["last_seen"])
        if max_cves_per_group is not None and len(grp["cves"]) > max_cves_per_group:
            grp["cves_truncated"] = len(grp["cves"]) - max_cves_per_group
            grp["cves"] = grp["cves"][:max_cves_per_group]
    return sorted(groups.values(), key=lambda g: (g["max_cvss"], g["cve_count"]), reverse=True)


def aggregate_web_findings(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group ``/vulns_web`` rows (Nuclei templates) by (ip, port, name).

    HORIZON repeats the same finding once per matched URL variant (an open redirect
    shows up four times with different paths). We keep the distinct URLs together.
    The IP is only present inside ``asn.ip`` and the port only inside the URL.
    """
    groups: dict[tuple[str, int, str], dict[str, Any]] = {}
    for raw in rows:
        host, port = _port_from_url(raw.get("url") or "")
        ip = (raw.get("asn") or {}).get("ip") or host or ""
        name = raw.get("name") or ""
        key = (ip, int(port or 0), name)
        grp = groups.get(key)
        if grp is None:
            grp = groups[key] = {
                "ip": ip,
                "port": port,
                "name": name,
                "severity": raw.get("severity"),
                "urls": [],
                "first_seen": None,
                "last_seen": None,
                "new": False,
            }
        url = raw.get("url")
        if url and url not in grp["urls"]:
            grp["urls"].append(url)
        fs, ls = ms_to_date(raw.get("first_seen")), ms_to_date(raw.get("last_seen"))
        grp["first_seen"] = min(filter(None, [grp["first_seen"], fs]), default=None)
        grp["last_seen"] = max(filter(None, [grp["last_seen"], ls]), default=None)
        grp["new"] = grp["new"] or bool(raw.get("is_new"))

    for grp in groups.values():
        grp["days_since_last_seen"] = days_since(grp["last_seen"])
    order = {"critical": 5, "high": 4, "medium": 3, "low": 2, "panel": 1, "info": 0}
    return sorted(groups.values(), key=lambda g: order.get(g["severity"] or "", -1), reverse=True)


def tls_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Compact view of one ``/tls`` row (httpx TLS probe).

    HORIZON connects by IP address, so the certificate never matches the connected
    name: the API's ``mismatched`` flag is always true and is deliberately dropped.
    """
    tls = raw.get("tls") or {}
    return {
        "ip": raw.get("ip"),
        "port": raw.get("port"),
        "url": raw.get("url"),
        "http_status": raw.get("status_code"),
        "tls_version": tls.get("tls_version"),
        "cipher": tls.get("cipher"),
        "subject_cn": tls.get("subject_cn"),
        "subject_alt_names": list(tls.get("subject_an") or []),
        "issuer": tls.get("issuer_org")[0] if tls.get("issuer_org") else tls.get("issuer_cn"),
        "not_before": (tls.get("not_before") or "")[:10] or None,
        "not_after": (tls.get("not_after") or "")[:10] or None,
        "days_to_expiry": _days_until((tls.get("not_after") or "")[:10]),
        "sha256": (tls.get("fingerprint_hash") or {}).get("sha256"),
        "cpes": list(raw.get("cpes") or []),
        "last_seen": ms_to_date(raw.get("last_seen")),
        "days_since_last_seen": days_since(ms_to_date(raw.get("last_seen"))),
    }


def _days_until(date_str: str | None) -> int | None:
    """Days from today until a ``YYYY-MM-DD`` date (negative if already past)."""
    d = days_since(date_str)
    return -d if d is not None else None


def http_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Compact view of one ``/httpinfo`` row (httpx fingerprint)."""
    return {
        "ip": raw.get("ip"),
        "port": raw.get("port"),
        "url": raw.get("url"),
        "http_status": raw.get("status_code"),
        "title": raw.get("title"),
        "tech": list(raw.get("tech") or []),
        "cpes": list(raw.get("cpes") or []),
        "last_seen": ms_to_date(raw.get("last_seen")),
        "days_since_last_seen": days_since(ms_to_date(raw.get("last_seen"))),
    }


def eol_row(raw: dict[str, Any]) -> dict[str, Any]:
    """Compact view of one ``/eol`` row. Note: HORIZON omits the port here."""
    eol = raw.get("eol") or {}
    components = [
        {
            "cpe": cpe,
            "release_cycle": info.get("release_cycle"),
            "eol_date": info.get("eol_date"),
            "latest_in_cycle": info.get("latest"),
            "is_eol": bool(info.get("is_eol")),
        }
        for cpe, info in eol.items()
        if isinstance(info, dict)
    ]
    return {
        "ip": (raw.get("asn") or {}).get("ip"),
        "port": None,  # not provided by the API
        "tls": bool(raw.get("ssl")),
        "cpes": list(raw.get("cpes") or []),
        "eol_components": components,
    }


def hosts_summary(port_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate compact port rows per host: how many ports, which services."""
    per_host: dict[str, dict[str, Any]] = defaultdict(lambda: {"ports": [], "services": set()})
    for row in port_rows:
        entry = per_host[row["ip"]]
        entry["ports"].append(row["port"])
        if row.get("service"):
            entry["services"].add(row["service"])
    return {
        "hosts": len(per_host),
        "open_ports": len(port_rows),
        "by_host": [
            {"ip": ip, "ports": sorted(v["ports"]), "services": sorted(v["services"])}
            for ip, v in sorted(per_host.items(), key=lambda kv: ipaddress.ip_address(kv[0]))
        ],
    }

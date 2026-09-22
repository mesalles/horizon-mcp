"""MCP server definition: a handful of read-only, high-level tools over HORIZON.

Design rules:
* Few tools, phrased in the analyst's vocabulary, not a mirror of the 24 endpoints.
* Every tool is read-only and idempotent (declared via annotations).
* Results are trimmed and aggregated server-side so they fit a model's context.
* Nothing institution-specific: ranges and account come from the API/key.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any

from mcp.server import MCPServer
from mcp.server.mcpserver.context import Context
from mcp.types import ToolAnnotations

from . import __version__
from .client import HorizonClient, HorizonError
from .config import Settings, load_settings
from .normalize import (
    TargetError,
    aggregate_cves,
    aggregate_web_findings,
    eol_row,
    hosts_summary,
    http_row,
    port_row,
    tls_row,
    validate_target,
)

log = logging.getLogger(__name__)

INSTRUCTIONS = """\
HORIZON (Delta90) is an external attack-surface monitoring service. This server gives
read-only access to what HORIZON sees, from the Internet, about the institution's own
IP ranges. Use it to answer questions such as "what does host X expose?", "which services
in this /24 have known CVEs?", or "what changed since the last scan cycle?".

Facts to keep in mind when interpreting results:
- Targets are IP addresses or CIDR ranges, never hostnames. Call `inventory` first if you
  do not know the institution's ranges.
- Data comes from HORIZON's own scan cycle (typically weekly). `last_seen` tells you how
  fresh a record is; `new=true` means first seen in the latest cycle.
- Ports/services are Nmap-derived. CVEs are inferred from the detected CPE (product +
  version), NOT verified by exploitation: expect false positives from distribution
  backports and open-ended NVD version ranges. Say so when reporting CVEs.
- Web findings come from Nuclei templates; `severity` may be `panel` (an exposed admin
  login page), which HORIZON treats as its own category.
- Lists are capped (`returned` vs `total`): if truncated, narrow the target or raise `limit`.
"""

READ_ONLY = ToolAnnotations(read_only_hint=True, destructive_hint=False, idempotent_hint=True,
                            open_world_hint=True)


@dataclass
class AppContext:
    settings: Settings
    client: HorizonClient


@asynccontextmanager
async def _lifespan(_server: MCPServer) -> AsyncIterator[AppContext]:
    settings = load_settings()
    client = HorizonClient(settings)
    try:
        yield AppContext(settings=settings, client=client)
    finally:
        await client.aclose()


mcp = MCPServer(
    "horizon",
    title="HORIZON external attack surface",
    instructions=INSTRUCTIONS,
    version=__version__,
    lifespan=_lifespan,
)


def _app(ctx: Context) -> AppContext:
    return ctx.request_context.lifespan_context  # type: ignore[return-value]


def _limit(app: AppContext, limit: int | None) -> int:
    if limit is None or limit <= 0:
        return app.settings.default_max_rows
    return min(limit, app.settings.hard_max_rows)


def _target(app: AppContext, target: str) -> str:
    return validate_target(target, min_prefix_len=app.settings.min_prefix_len)


def _error(exc: Exception) -> dict[str, Any]:
    """Return errors as data so the model can explain them instead of crashing the turn."""
    return {"error": str(exc)}


# --------------------------------------------------------------------------- tools


@mcp.tool(annotations=READ_ONLY)
async def inventory(ctx: Context) -> dict[str, Any]:
    """List the IP ranges (and root domains, if any) HORIZON monitors for this account.

    Call this first when you need to know which addresses belong to the institution.
    Most accounts provisioned through RedIRIS contain IP ranges only; root domains
    are usually empty, which means domain-based lookups are not available.
    """
    app = _app(ctx)
    try:
        account = await app.client.account()
        nets = await app.client.inventory_nets()
        fqdns = await app.client.inventory_fqdns()
    except HorizonError as exc:
        return _error(exc)
    accounts = account.get("data") or []
    return {
        "account_ids": [a.get("account_id") for a in accounts if isinstance(a, dict)],
        "ranges": [
            {"cidr": n.get("net"), "netname": n.get("netname"), "description": n.get("description")}
            for n in nets
        ],
        "root_domains": [f.get("fqdn") for f in fqdns if isinstance(f, dict)],
    }


@mcp.tool(annotations=READ_ONLY)
async def open_ports(
    ctx: Context,
    target: str,
    limit: int | None = None,
    new_only: bool = False,
) -> dict[str, Any]:
    """Open ports and detected services (Nmap-style) for an IP or CIDR, as seen from the Internet.

    Args:
        target: an IPv4/IPv6 address or CIDR, e.g. "192.0.2.10" or "192.0.2.0/24".
        limit: max rows to return (default 200, hard cap 1000). `total` always reports
            the full count so you can tell when the list is truncated.
        new_only: only services first seen in HORIZON's latest scan cycle.

    Each row: ip, port, transport, service, product, tls, cpes (CPE 2.2 as HORIZON
    returns them; "-" means unknown version), first_seen, last_seen, new.
    A per-host summary (ports and services per IP) is included for ranges.
    """
    app = _app(ctx)
    try:
        cidr = _target(app, target)
        rows, total = await app.client.ports(cidr, max_rows=_limit(app, limit), new_only=new_only)
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    compact = [port_row(r) for r in rows]
    return {
        "target": cidr,
        "total": total,
        "returned": len(compact),
        "summary": hosts_summary(compact),
        "ports": compact,
    }


@mcp.tool(annotations=READ_ONLY)
async def cves(
    ctx: Context,
    target: str,
    min_cvss: float = 0.0,
    limit: int | None = None,
    new_only: bool = False,
) -> dict[str, Any]:
    """Known CVEs HORIZON attributes to services on an IP or CIDR, grouped per service.

    HORIZON infers CVEs from the detected CPE (product and version); nothing is
    verified by exploitation. Treat results as "potentially affected", and expect false
    positives on distribution-patched software (e.g. Ubuntu/Debian backports).

    Args:
        target: IPv4/IPv6 address or CIDR.
        min_cvss: drop CVEs below this CVSS score (e.g. 7.0 for high+critical only).
        limit: max raw CVE rows to fetch before grouping (default 200, hard cap 1000).
        new_only: only CVEs first seen in the latest scan cycle.

    Each group: ip, port, cpe, cve_count, max_cvss, severity, cves[] (cve, cvss,
    severity), first_seen, last_seen, new_cves. Sorted by max_cvss descending.
    """
    app = _app(ctx)
    try:
        cidr = _target(app, target)
        rows, total = await app.client.cves(cidr, max_rows=_limit(app, limit), new_only=new_only)
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    groups = aggregate_cves(rows, min_cvss=min_cvss)
    return {
        "target": cidr,
        "total_cve_rows": total,
        "fetched_cve_rows": len(rows),
        "services_affected": len(groups),
        "services": groups,
    }


@mcp.tool(annotations=READ_ONLY)
async def web_findings(
    ctx: Context,
    target: str,
    limit: int | None = None,
    new_only: bool = False,
) -> dict[str, Any]:
    """Web findings from HORIZON's Nuclei templates on an IP or CIDR: exposed admin panels,
    misconfigurations, information disclosure, open redirects, TLS issues.

    Args:
        target: IPv4/IPv6 address or CIDR.
        limit: max raw rows to fetch (default 200, hard cap 1000).
        new_only: only findings first seen in the latest scan cycle.

    Findings are grouped by (ip, port, name) with all matched URLs together, because
    HORIZON repeats a finding once per URL variant. `severity` is one of info, low,
    medium, high, critical or `panel` (exposed login page). No CVE/CVSS is provided
    for these; the name is HORIZON's Spanish translation of the Nuclei template title.
    """
    app = _app(ctx)
    try:
        cidr = _target(app, target)
        rows, total = await app.client.vulns_web(cidr, max_rows=_limit(app, limit), new_only=new_only)
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    groups = aggregate_web_findings(rows)
    return {
        "target": cidr,
        "total_rows": total,
        "fetched_rows": len(rows),
        "findings": groups,
    }


@mcp.tool(annotations=READ_ONLY)
async def tls_certificates(
    ctx: Context,
    target: str,
    limit: int | None = None,
) -> dict[str, Any]:
    """TLS certificate and connection details for HTTPS services on an IP or CIDR.

    Useful to find the hostnames behind an IP (subject CN and SANs), expiring
    certificates (not_after), name mismatches, and the negotiated protocol/cipher.
    HORIZON does not grade TLS strength here; it only reports what it observed.
    """
    app = _app(ctx)
    try:
        cidr = _target(app, target)
        rows, total = await app.client.tls(cidr, max_rows=_limit(app, limit))
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    return {"target": cidr, "total": total, "returned": len(rows), "certificates": [tls_row(r) for r in rows]}


@mcp.tool(annotations=READ_ONLY)
async def http_services(
    ctx: Context,
    target: str,
    limit: int | None = None,
) -> dict[str, Any]:
    """HTTP fingerprint of web services on an IP or CIDR: status code, page title,
    detected technologies (Wappalyzer-style "name:version") and derived CPEs.

    Note that CPEs here are partly synthesised from technology names and may not
    exist in the NVD dictionary; prefer the CPEs from `open_ports` for CVE work.
    """
    app = _app(ctx)
    try:
        cidr = _target(app, target)
        rows, total = await app.client.httpinfo(cidr, max_rows=_limit(app, limit))
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    return {"target": cidr, "total": total, "returned": len(rows), "services": [http_row(r) for r in rows]}


@mcp.tool(annotations=READ_ONLY)
async def end_of_life(
    ctx: Context,
    target: str,
    limit: int | None = None,
) -> dict[str, Any]:
    """Services running software past its end-of-life date (per endoflife.date-style data).

    HORIZON does not return the port for these rows, so a host with several services
    on the same product will appear once per service without saying which port.
    Distribution-maintained packages (e.g. nginx 1.18 on Ubuntu) may be flagged as
    EOL upstream while still receiving security patches from the distribution.
    """
    app = _app(ctx)
    try:
        cidr = _target(app, target)
        rows, total = await app.client.eol(cidr, max_rows=_limit(app, limit))
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    return {"target": cidr, "total": total, "returned": len(rows), "hosts": [eol_row(r) for r in rows]}


@mcp.tool(annotations=READ_ONLY)
async def exposure_summary(ctx: Context, host: str) -> dict[str, Any]:
    """One-call overview of a single host's external exposure: open ports and services,
    the HTTP fingerprint of each web service (status, page title, technologies), CVE
    groups per service (highest CVSS first), web findings, and TLS certificates.

    Use this when an analyst asks "what does <IP> expose?" Pass a single IP address;
    for ranges use the individual tools. Everything HORIZON knows about the host is
    fetched (no truncation), so keep it to one host at a time. There is no need to
    call `http_services`, `cves`, `web_findings` or `tls_certificates` afterwards for
    the same host: their data is already included.
    """
    app = _app(ctx)
    try:
        ip = _target(app, host)
        if "/" in ip:
            raise TargetError("exposure_summary takes a single IP address, not a range")
        ports, _ = await app.client.ports(ip)
        http_rows, _ = await app.client.httpinfo(ip)
        cve_rows, _ = await app.client.cves(ip)
        web_rows, _ = await app.client.vulns_web(ip)
        tls_rows, _ = await app.client.tls(ip)
    except (TargetError, HorizonError) as exc:
        return _error(exc)

    compact_ports = [port_row(r) for r in ports]
    http = [http_row(r) for r in http_rows]
    cve_groups = aggregate_cves(cve_rows)
    web = aggregate_web_findings(web_rows)
    certs = [tls_row(r) for r in tls_rows]
    hostnames = sorted(
        {c["subject_cn"] for c in certs if c.get("subject_cn")}
        | {san for c in certs for san in c.get("subject_alt_names") or []}
    )
    return {
        "host": ip,
        "hostnames_from_certificates": hostnames,
        "open_ports": len(compact_ports),
        "services": compact_ports,
        "http_services": http,
        "cve_rows": len(cve_rows),
        "max_cvss": max((g["max_cvss"] for g in cve_groups), default=None),
        "cves_by_service": cve_groups,
        "web_findings": web,
        "tls_certificates": certs,
        "last_seen": max((p["last_seen"] for p in compact_ports if p.get("last_seen")), default=None),
    }

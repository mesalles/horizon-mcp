"""MCP server definition: a handful of read-only, high-level tools over HORIZON.

Design rules:
* Few tools, phrased in the analyst's vocabulary, not a mirror of the 24 endpoints.
* Every tool is read-only and idempotent (declared via annotations).
* Results are trimmed and aggregated server-side so they fit a model's context.
* Nothing institution-specific: ranges and account come from the API/key.
"""

from __future__ import annotations

import asyncio
import logging
import re
import socket
from collections.abc import AsyncIterator, Awaitable, Callable
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
    mark_latest_cycle,
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
- Targets are IP addresses, CIDR ranges or hostnames. Hostnames are resolved by this
  server (not by HORIZON) and the response echoes `resolved_ips`. Call `inventory` first
  if you do not know the institution's ranges.
- Data comes from HORIZON's own scan cycle (typically weekly), and each index (ports,
  HTTP, CVEs, web findings, TLS) runs on its own cadence, so dates differ between them.
  `last_seen` / `days_since_last_seen` tell you how fresh a record is; `new=true` means
  first seen in the latest cycle. A finding not re-observed for weeks while the host's
  services are current is probably historical: report it as "last seen on <date>".
- HTTP titles and technologies describe the *default virtual host*: HORIZON connects by
  IP address, without SNI or a Host header for the real name. The site actually served
  under a hostname may differ. For the same reason TLS name mismatches are meaningless
  and are not reported.
- Ports/services are Nmap-derived. CVEs are inferred from the detected CPE (product +
  version), NOT verified by exploitation: expect false positives from distribution
  backports and open-ended NVD version ranges. Say so when reporting CVEs.
- Web findings come from Nuclei templates; `severity` may be `panel` (an exposed admin
  login page), which HORIZON treats as its own category.
- For "what is new / what changed" questions use `recent_changes`; for "what does host X
  expose" use `exposure_summary`. Both are single-call summaries.
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


_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z][a-z0-9-]{0,62}$", re.I
)
MAX_RESOLVED_IPS = 4


def _getaddrinfo(host: str) -> list[tuple[Any, ...]]:
    """Thin wrapper so tests can monkeypatch DNS resolution."""
    return socket.getaddrinfo(host, None)


@dataclass
class Resolved:
    """What a user-supplied target turned into: one or more IPs/CIDRs to query."""

    targets: list[str]
    hostname: str | None = None

    def fields(self) -> dict[str, Any]:
        """Echo of the target for tool responses (`resolved_ips` when a name was given)."""
        if self.hostname:
            return {"target": self.hostname, "resolved_ips": list(self.targets)}
        return {"target": self.targets[0]}


async def _resolve(app: AppContext, value: str) -> Resolved:
    """Accept an IP, a CIDR or a hostname. Hostnames are resolved (A + AAAA) on the
    machine running this server, which may differ from the Internet's view if there
    is split-horizon DNS. HORIZON itself only understands IPs."""
    try:
        return Resolved([_target(app, value)])
    except TargetError:
        name = (value or "").strip().rstrip(".")
        if not _HOSTNAME_RE.match(name):
            raise
    loop = asyncio.get_running_loop()
    try:
        infos = await loop.run_in_executor(None, _getaddrinfo, name)
    except socket.gaierror as exc:
        raise TargetError(
            f"{name!r} does not resolve ({exc.strerror or exc}). Note that resolution happens on "
            "the machine running horizon-mcp, not on HORIZON."
        ) from exc
    seen: dict[str, None] = {}
    for _family, _type, _proto, _canon, sockaddr in infos:
        seen.setdefault(sockaddr[0], None)
    ips = sorted(seen, key=lambda ip: (":" in ip, ip))  # IPv4 first
    if not ips:
        raise TargetError(f"{name!r} resolved to no addresses")
    if len(ips) > MAX_RESOLVED_IPS:
        raise TargetError(
            f"{name!r} resolves to {len(ips)} addresses ({', '.join(ips)}); query one IP at a time"
        )
    return Resolved(ips, hostname=name)


async def _fetch(
    fn: Callable[..., Awaitable[tuple[list[dict[str, Any]], int]]],
    res: Resolved,
    **kwargs: Any,
) -> tuple[list[dict[str, Any]], int]:
    """Run a client query for every resolved target and merge rows and totals."""
    rows: list[dict[str, Any]] = []
    total = 0
    for target in res.targets:
        part, n = await fn(target, **kwargs)
        rows.extend(part)
        total += n
    return rows, total


def _is_web(svc: dict[str, Any]) -> bool:
    """Heuristic: an Nmap service that an HTTP fingerprint could exist for."""
    service = (svc.get("service") or "").lower()
    return service.startswith("http") or service in {"ssl", "ssl/http", "https-alt"} or bool(svc.get("tls"))


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
        target: IPv4/IPv6 address, CIDR or hostname, e.g. "192.0.2.10", "192.0.2.0/24"
            or "www.example.edu". Hostnames are resolved here (see `resolved_ips`).
        limit: max rows to return (default 200, hard cap 1000). `total` always reports
            the full count so you can tell when the list is truncated.
        new_only: only services first seen in HORIZON's latest scan cycle.

    Each row: ip, port, transport, service, product, tls, cpes (CPE 2.2 as HORIZON
    returns them; "-" means unknown version), first_seen, last_seen, new.
    A per-host summary (ports and services per IP) is included for ranges.
    """
    app = _app(ctx)
    try:
        res = await _resolve(app, target)
        rows, total = await _fetch(app.client.ports, res, max_rows=_limit(app, limit), new_only=new_only)
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    compact = [port_row(r) for r in rows]
    return {
        **res.fields(),
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
        target: IPv4/IPv6 address, CIDR or hostname (resolved here; see `resolved_ips`).
        min_cvss: drop CVEs below this CVSS score (e.g. 7.0 for high+critical only).
        limit: max raw CVE rows to fetch before grouping (default 200, hard cap 1000).
        new_only: only CVEs first seen in the latest scan cycle.

    Each group: ip, port, cpe, cve_count, max_cvss, severity, cves[] (cve, cvss,
    severity), first_seen, last_seen, new_cves. Sorted by max_cvss descending.
    """
    app = _app(ctx)
    try:
        res = await _resolve(app, target)
        rows, total = await _fetch(app.client.cves, res, max_rows=_limit(app, limit), new_only=new_only)
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    groups = aggregate_cves(rows, min_cvss=min_cvss)
    return {
        **res.fields(),
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
        target: IPv4/IPv6 address, CIDR or hostname (resolved here; see `resolved_ips`).
        limit: max raw rows to fetch (default 200, hard cap 1000).
        new_only: only findings first seen in the latest scan cycle.

    Findings are grouped by (ip, port, name) with all matched URLs together, because
    HORIZON repeats a finding once per URL variant. `severity` is one of info, low,
    medium, high, critical or `panel` (exposed login page). No CVE/CVSS is provided
    for these; the name is HORIZON's Spanish translation of the Nuclei template title.
    """
    app = _app(ctx)
    try:
        res = await _resolve(app, target)
        rows, total = await _fetch(app.client.vulns_web, res, max_rows=_limit(app, limit), new_only=new_only)
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    groups = aggregate_web_findings(rows)
    return {
        **res.fields(),
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
        res = await _resolve(app, target)
        rows, total = await _fetch(app.client.tls, res, max_rows=_limit(app, limit))
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    return {**res.fields(), "total": total, "returned": len(rows), "certificates": [tls_row(r) for r in rows]}


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
        res = await _resolve(app, target)
        rows, total = await _fetch(app.client.httpinfo, res, max_rows=_limit(app, limit))
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    return {**res.fields(), "total": total, "returned": len(rows), "services": [http_row(r) for r in rows]}


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
        res = await _resolve(app, target)
        rows, total = await _fetch(app.client.eol, res, max_rows=_limit(app, limit))
    except (TargetError, HorizonError) as exc:
        return _error(exc)
    return {**res.fields(), "total": total, "returned": len(rows), "hosts": [eol_row(r) for r in rows]}


@mcp.tool(annotations=READ_ONLY)
async def exposure_summary(ctx: Context, host: str, min_cvss: float = 0.0) -> dict[str, Any]:
    """One-call overview of a single host's external exposure: open ports and services,
    the HTTP fingerprint of each web service (status, page title, technologies), CVE
    groups per service (highest CVSS first), web findings, and TLS certificates.

    Use this when an analyst asks "what does <IP or hostname> expose?" Pass a single IP
    address or a hostname (resolved here; if it maps to several IPs the first IPv4 is
    summarised and the rest are listed in `other_resolved_ips`); for ranges use the
    individual tools. CVE groups keep their top 10 CVEs by CVSS (`cve_count` is the
    full number); pass `min_cvss` (e.g. 7.0) to drop low-scored CVEs entirely. Everything HORIZON knows about the host is
    fetched (no truncation), so keep it to one host at a time. There is no need to
    call `http_services`, `cves`, `web_findings` or `tls_certificates` afterwards for
    the same host: their data is already included.

    Freshness: `data_freshness` gives the latest observation date per source, because
    HORIZON's indices run on different cadences. Each web finding and CVE group carries
    `observed_in_latest_cycle`: false means it was NOT re-observed in the host's latest
    services cycle and may be historical (fixed or gone). Report those as "last seen on
    <date>", not as current.
    """
    app = _app(ctx)
    try:
        res = await _resolve(app, host)
        if any("/" in t for t in res.targets):
            raise TargetError("exposure_summary takes a single IP address or hostname, not a range")
        ip = res.targets[0]
        ports, _ = await app.client.ports(ip)
        http_rows, _ = await app.client.httpinfo(ip)
        cve_rows, _ = await app.client.cves(ip)
        web_rows, _ = await app.client.vulns_web(ip)
        tls_rows, _ = await app.client.tls(ip)
    except (TargetError, HorizonError) as exc:
        return _error(exc)

    compact_ports = [port_row(r) for r in ports]
    http = [http_row(r) for r in http_rows]
    cve_groups = aggregate_cves(cve_rows, min_cvss=min_cvss, max_cves_per_group=10)
    web = aggregate_web_findings(web_rows)
    certs = [tls_row(r) for r in tls_rows]
    hostnames = sorted(
        {c["subject_cn"] for c in certs if c.get("subject_cn")}
        | {san for c in certs for san in c.get("subject_alt_names") or []}
    )

    def _latest(rows: list[dict[str, Any]]) -> str | None:
        return max((r["last_seen"] for r in rows if r.get("last_seen")), default=None)

    # The services index is the reference clock for "is this still there?".
    cycle_date = _latest(compact_ports)
    mark_latest_cycle(web, cycle_date)
    mark_latest_cycle(cve_groups, cycle_date)

    return {
        "host": ip,
        "resolved_from": res.hostname,
        "other_resolved_ips": res.targets[1:],
        "hostnames_from_certificates": hostnames,
        "data_freshness": {
            "services": cycle_date,
            "http": _latest(http),
            "cves": _latest(cve_groups),
            "web_findings": _latest(web),
            "tls": _latest(certs),
            "note": "Each HORIZON index has its own scan cadence; dates differ by source.",
        },
        "open_ports": len(compact_ports),
        "services": compact_ports,
        "http_services": http,
        "cve_rows": len(cve_rows),
        "max_cvss": max((g["max_cvss"] for g in cve_groups), default=None),
        "cves_by_service": cve_groups,
        "web_findings": web,
        "web_findings_not_reobserved": sum(1 for f in web if f.get("observed_in_latest_cycle") is False),
        "tls_certificates": certs,
        "last_seen": cycle_date,
    }


@mcp.tool(annotations=READ_ONLY)
async def recent_changes(
    ctx: Context,
    target: str,
    limit: int | None = None,
) -> dict[str, Any]:
    """What HORIZON saw for the first time in its latest scan cycle within an IP or CIDR:
    new open services, new CVEs (grouped per service) and new web findings, in one call.

    "New" is relative to HORIZON's own scan cycle (typically weekly), not to the last
    time you asked. It means first_seen == last_seen == the cycle timestamp.
    `cycle_date` tells you which cycle that is. HORIZON does not report services that
    disappeared; compare with `open_ports` if you need that.

    New web services carry their HTTP fingerprint inline (`http`: status, title,
    technologies), so there is no need to call `http_services` afterwards for them.

    Args:
        target: IPv4/IPv6 address, CIDR or hostname (resolved here; see `resolved_ips`).
        limit: max raw rows to fetch per source (default 200, hard cap 1000).
    """
    app = _app(ctx)
    try:
        res = await _resolve(app, target)
        cap = _limit(app, limit)
        ports, ports_total = await _fetch(app.client.ports, res, max_rows=cap, new_only=True)
        cve_rows, cves_total = await _fetch(app.client.cves, res, max_rows=cap, new_only=True)
        web_rows, web_total = await _fetch(app.client.vulns_web, res, max_rows=cap, new_only=True)
        new_services = [port_row(r) for r in ports]
        # One extra request (not per service) to describe what the new web services serve.
        # The HTTP index has its own cadence, so it is queried without new_only and joined
        # on (ip, port).
        http_by_key: dict[tuple[str, int], dict[str, Any]] = {}
        if any(_is_web(p) for p in new_services):
            http_rows, _ = await _fetch(app.client.httpinfo, res, max_rows=app.settings.hard_max_rows)
            http_by_key = {(h["ip"], h["port"]): h for h in (http_row(r) for r in http_rows)}
    except (TargetError, HorizonError) as exc:
        return _error(exc)

    for svc in new_services:
        if _is_web(svc):
            hit = http_by_key.get((svc["ip"], svc["port"]))
            svc["http"] = (
                {k: hit[k] for k in ("http_status", "title", "tech", "last_seen")} if hit else None
            )
    new_cves = aggregate_cves(cve_rows)
    new_web = aggregate_web_findings(web_rows)
    cycle_dates = (
        [p["first_seen"] for p in new_services if p.get("first_seen")]
        + [g["first_seen"] for g in new_cves if g.get("first_seen")]
        + [f["first_seen"] for f in new_web if f.get("first_seen")]
    )
    return {
        **res.fields(),
        "cycle_date": max(cycle_dates, default=None),
        "counts": {
            "new_services": len(new_services),
            "new_cve_rows": len(cve_rows),
            "new_web_findings": len(new_web),
        },
        "totals": {"services": ports_total, "cve_rows": cves_total, "web_findings": web_total},
        "new_services": new_services,
        "new_cves_by_service": new_cves,
        "new_web_findings": new_web,
    }

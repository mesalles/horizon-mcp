"""Command-line entry point: ``horizon-mcp [--transport stdio|streamable-http] [--host] [--port]``.

stdio is the default and is what Claude Desktop / Claude Code launch locally.
streamable-http is for running it as a shared service. In that mode clients must
present ``Authorization: Bearer <HORIZON_MCP_BEARER_TOKEN>``; binding to a non-loopback
address without a token is refused unless ``--allow-unauthenticated`` is given (for
deployments where a reverse proxy already authenticates). TLS is the proxy's job.
"""

from __future__ import annotations

import argparse
import ipaddress
import logging
import sys

from . import __version__
from .config import ConfigError, load_settings

log = logging.getLogger(__name__)

LOOPBACK_NAMES = {"localhost", "ip6-localhost", "ip6-loopback"}


def _is_loopback(host: str) -> bool:
    """True for 127.x, ::1 and the usual loopback names. Anything else is 'reachable'."""
    host = host.strip().strip("[]").lower()
    if host in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _http_startup_check(host: str, token: str | None, allow_unauthenticated: bool) -> str | None:
    """Decide whether streamable-http may start. Returns an error message, or None to proceed.

    | bind host   | token | result                                              |
    |-------------|-------|-----------------------------------------------------|
    | loopback    | any   | start                                               |
    | other       | set   | start, clients authenticate                         |
    | other       | unset | refuse, unless --allow-unauthenticated               |
    """
    if token or _is_loopback(host) or allow_unauthenticated:
        return None
    return (
        f"refusing to listen on {host} without client authentication: the endpoint would "
        "expose this institution's HORIZON data to anyone who can reach the port. Set "
        "HORIZON_MCP_BEARER_TOKEN (clients send it as 'Authorization: Bearer <token>'), bind to "
        "127.0.0.1 behind a reverse proxy, or pass --allow-unauthenticated if the proxy "
        "already authenticates and you accept the risk."
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="horizon-mcp",
        description="Read-only MCP server over the HORIZON external attack-surface API.",
    )
    parser.add_argument(
        "--transport", choices=["stdio", "streamable-http"], default="stdio",
        help="stdio (default, for local clients) or streamable-http (shared service)",
    )
    parser.add_argument("--host", default="127.0.0.1", help="bind address for streamable-http")
    parser.add_argument("--port", type=int, default=8000, help="bind port for streamable-http")
    parser.add_argument(
        "--allow-unauthenticated", action="store_true",
        help="streamable-http only: start on a non-loopback address without "
             "HORIZON_MCP_BEARER_TOKEN (use only behind a proxy that authenticates)",
    )
    parser.add_argument("--log-level", default="INFO",
                        choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--check", action="store_true",
                        help="validate configuration and exit without starting the server")
    parser.add_argument("--ping", action="store_true",
                        help="call HORIZON (/ and /account) to verify key and connectivity, then exit")
    parser.add_argument("--version", action="version", version=f"horizon-mcp {__version__}")
    args = parser.parse_args(argv)

    # stdio carries the protocol on stdout: all logging MUST go to stderr.
    logging.basicConfig(
        level=args.log_level,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    # httpx logs every request at INFO; keep that for DEBUG runs only.
    if args.log_level != "DEBUG":
        logging.getLogger("httpx").setLevel(logging.WARNING)

    try:
        settings = load_settings()
    except ConfigError as exc:
        print(f"horizon-mcp: {exc}", file=sys.stderr)
        return 2

    client_auth = "configured" if settings.mcp_bearer_token else "not set"

    if args.check:
        print(f"horizon-mcp {__version__}: configuration OK (api_url={settings.api_url}, "
              f"client bearer token {client_auth})", file=sys.stderr)
        return 0

    if args.ping:
        return _ping(settings, client_auth)

    # Imported here so `--check` and `--version` work without building the server.
    from .server import mcp

    if args.transport == "stdio":
        mcp.run(transport="stdio")
        return 0

    error = _http_startup_check(args.host, settings.mcp_bearer_token, args.allow_unauthenticated)
    if error:
        print(f"horizon-mcp: {error}", file=sys.stderr)
        return 2
    _serve_http(mcp, settings.mcp_bearer_token, args.host, args.port, args.log_level)
    return 0


def _serve_http(mcp, token: str | None, host: str, port: int, log_level: str) -> None:
    """Run the SDK's streamable-http Starlette app under uvicorn, wrapped in Bearer auth.

    Mirrors ``MCPServer.run(transport="streamable-http")`` (which cannot wrap the app):
    the Starlette app carries its own lifespan (session manager) and the SDK enables
    DNS-rebinding protection by itself when *host* is loopback.
    """
    import uvicorn

    from .auth import BearerAuthMiddleware

    app = mcp.streamable_http_app(host=host)
    if token:
        app = BearerAuthMiddleware(app, token)
        log.info("streamable-http on %s:%d/mcp, clients must send a Bearer token", host, port)
    else:
        log.warning("streamable-http on %s:%d/mcp WITHOUT client authentication", host, port)
    uvicorn.run(app, host=host, port=port, log_level=log_level.lower())


def _ping(settings, client_auth: str = "not set") -> int:
    """Live connectivity check: API root, account and inventory. Never prints any secret."""
    import asyncio

    from .client import HorizonClient, HorizonError

    async def run() -> int:
        client = HorizonClient(settings)
        try:
            root = await client.root()
            print(f"API: {root.get('api')} {root.get('version')} status={root.get('status')}")
            account = await client.account()
            ids = [a.get("account_id") for a in (account.get("data") or []) if isinstance(a, dict)]
            print(f"Account(s): {', '.join(ids) or '(none)'}")
            nets = await client.inventory_nets()
            print("Ranges: " + (", ".join(n.get("net", "?") for n in nets) or "(none)"))
            fqdns = await client.inventory_fqdns()
            print("Root domains: " + (", ".join(f.get("fqdn", "?") for f in fqdns) or "(none)"))
            print(f"User-Agent accepted: {settings.user_agent!r}")
            print(f"Client bearer token (streamable-http): {client_auth}")
            return 0
        except HorizonError as exc:
            print(f"horizon-mcp: {exc}", file=sys.stderr)
            return 1
        finally:
            await client.aclose()

    return asyncio.run(run())


if __name__ == "__main__":
    sys.exit(main())

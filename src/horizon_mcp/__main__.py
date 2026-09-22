"""Command-line entry point: ``horizon-mcp [--transport stdio|streamable-http] [--host] [--port]``.

stdio is the default and is what Claude Desktop / Claude Code launch locally.
streamable-http is for running it as a shared service (put it behind a reverse
proxy with TLS and authentication; the server itself does not authenticate callers).
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import __version__
from .config import ConfigError, load_settings


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

    if args.check:
        print(f"horizon-mcp {__version__}: configuration OK (api_url={settings.api_url})",
              file=sys.stderr)
        return 0

    if args.ping:
        return _ping(settings)

    # Imported here so `--check` and `--version` work without building the server.
    from .server import mcp

    if args.transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    return 0


def _ping(settings) -> int:
    """Live connectivity check: API root, account and inventory. Never prints the key."""
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
            return 0
        except HorizonError as exc:
            print(f"horizon-mcp: {exc}", file=sys.stderr)
            return 1
        finally:
            await client.aclose()

    return asyncio.run(run())


if __name__ == "__main__":
    sys.exit(main())

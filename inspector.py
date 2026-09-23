"""Entry point for the MCP Inspector: `uv run mcp dev inspector.py`.

Imports the server through the package so it behaves exactly like `horizon-mcp`.
"""

from horizon_mcp.server import mcp  # noqa: F401

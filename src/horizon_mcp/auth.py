"""Optional Bearer-token authentication for the streamable-http transport.

A single shared secret (``HORIZON_MCP_BEARER_TOKEN``) protects the MCP endpoint when
the server is exposed over HTTP. It is deliberately minimal: one token per instance,
compared in constant time, no users or scopes. Per-user authentication belongs to a
reverse proxy or, later, to the SDK's OAuth ``token_verifier`` machinery.

Implemented as a pure ASGI middleware, not Starlette's ``BaseHTTPMiddleware``: the
latter buffers responses and would break the SSE stream MCP relies on.
"""

from __future__ import annotations

import json
import secrets

from starlette.types import ASGIApp, Receive, Scope, Send

REALM = "horizon-mcp"


def bearer_secret(scope: Scope) -> str:
    """Return the token from ``Authorization: Bearer <token>``, or "" if absent/other scheme."""
    for name, value in scope.get("headers") or []:
        if name.lower() == b"authorization":
            scheme, _, token = value.decode("latin-1").partition(" ")
            return token.strip() if scheme.lower() == "bearer" else ""
    return ""


async def _deny(send: Send, detail: str) -> None:
    body = json.dumps({"detail": detail}).encode()
    await send({
        "type": "http.response.start",
        "status": 401,
        "headers": [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode()),
            (b"www-authenticate", f'Bearer realm="{REALM}"'.encode()),
        ],
    })
    await send({"type": "http.response.body", "body": body})


class BearerAuthMiddleware:
    """Reject any HTTP request whose Bearer token does not match *token*.

    Non-HTTP scopes (lifespan, websocket) pass through untouched so the wrapped
    app's own startup/shutdown keeps working.
    """

    def __init__(self, app: ASGIApp, token: str):
        if not token:
            raise ValueError("BearerAuthMiddleware needs a non-empty token")
        self.app = app
        self._token = token

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        presented = bearer_secret(scope)
        if not presented:
            await _deny(send, "Not authenticated: send Authorization: Bearer <token>")
            return
        if not secrets.compare_digest(presented.encode(), self._token.encode()):
            await _deny(send, "Invalid token")
            return
        await self.app(scope, receive, send)

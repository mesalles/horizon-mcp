"""Bearer middleware for streamable-http and the start-up safety check (#16)."""

import httpx
import pytest

from horizon_mcp.__main__ import _http_startup_check, _is_loopback
from horizon_mcp.auth import BearerAuthMiddleware, bearer_secret

TOKEN = "s3cret-token-value"


async def _ok_app(scope, receive, send):
    """Minimal ASGI app: 200 for HTTP, completes the lifespan handshake otherwise."""
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            elif message["type"] == "lifespan.shutdown":
                await send({"type": "lifespan.shutdown.complete"})
                return
    await send({"type": "http.response.start", "status": 200,
                "headers": [(b"content-type", b"text/plain")]})
    await send({"type": "http.response.body", "body": b"ok"})


def _client(token: str = TOKEN) -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=BearerAuthMiddleware(_ok_app, token))
    return httpx.AsyncClient(transport=transport, base_url="http://mcp.test")


async def test_missing_header_is_401_with_challenge():
    async with _client() as c:
        r = await c.post("/mcp", json={})
    assert r.status_code == 401
    assert r.headers["www-authenticate"] == 'Bearer realm="horizon-mcp"'
    assert r.json()["detail"].startswith("Not authenticated")


@pytest.mark.parametrize("header", [
    "Bearer wrong-token",
    "Bearer s3cret-token-valu",        # prefix of the real one
    "Bearer s3cret-token-value-extra",  # real one plus a suffix
    "Basic czNjcmV0",                    # other scheme
    "s3cret-token-value",               # no scheme
])
async def test_wrong_or_malformed_token_is_401(header):
    async with _client() as c:
        r = await c.post("/mcp", json={}, headers={"Authorization": header})
    assert r.status_code == 401
    assert r.headers["www-authenticate"].startswith("Bearer")


async def test_correct_token_passes_through():
    async with _client() as c:
        r = await c.post("/mcp", json={}, headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200 and r.text == "ok"


async def test_scheme_is_case_insensitive_token_is_not():
    async with _client() as c:
        ok = await c.get("/mcp", headers={"Authorization": f"bearer {TOKEN}"})
        bad = await c.get("/mcp", headers={"Authorization": f"Bearer {TOKEN.upper()}"})
    assert ok.status_code == 200 and bad.status_code == 401


async def test_lifespan_scope_bypasses_auth():
    """uvicorn's lifespan events must reach the wrapped app so the SDK's session manager starts."""
    sent = []

    async def send(msg):
        sent.append(msg)

    messages = iter([{"type": "lifespan.startup"}, {"type": "lifespan.shutdown"}])

    async def receive():
        return next(messages)

    await BearerAuthMiddleware(_ok_app, TOKEN)({"type": "lifespan"}, receive, send)
    assert [m["type"] for m in sent] == ["lifespan.startup.complete", "lifespan.shutdown.complete"]


def test_empty_token_is_rejected_at_construction():
    with pytest.raises(ValueError):
        BearerAuthMiddleware(_ok_app, "")


def test_bearer_secret_parsing():
    assert bearer_secret({"headers": [(b"authorization", b"Bearer  abc ")]}) == "abc"
    assert bearer_secret({"headers": [(b"Authorization", b"BEARER abc")]}) == "abc"
    assert bearer_secret({"headers": [(b"authorization", b"Basic abc")]}) == ""
    assert bearer_secret({"headers": []}) == ""
    assert bearer_secret({}) == ""


@pytest.mark.parametrize("host,expected", [
    ("127.0.0.1", True), ("127.0.0.53", True), ("::1", True), ("[::1]", True),
    ("localhost", True), ("LOCALHOST", True),
    ("0.0.0.0", False), ("::", False), ("10.0.0.5", False), ("mcp.example.edu", False),
])
def test_is_loopback(host, expected):
    assert _is_loopback(host) is expected


@pytest.mark.parametrize("host,token,allow,starts", [
    ("127.0.0.1", None, False, True),    # loopback, no token: fine (proxy or local use)
    ("127.0.0.1", TOKEN, False, True),
    ("0.0.0.0", TOKEN, False, True),     # reachable, authenticated
    ("0.0.0.0", None, False, False),     # reachable, open: refused
    ("0.0.0.0", None, True, True),       # ... unless explicitly accepted
    ("mcp.example.edu", None, False, False),
])
def test_http_startup_check(host, token, allow, starts):
    error = _http_startup_check(host, token, allow)
    assert (error is None) is starts
    if error:
        assert "HORIZON_MCP_BEARER_TOKEN" in error and "--allow-unauthenticated" in error

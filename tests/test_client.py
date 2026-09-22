import httpx
import pytest

from horizon_mcp.client import HorizonClient, HorizonError
from horizon_mcp.config import Settings

from . import fixtures as fx

BASE = "https://horizon.test"


@pytest.fixture
def settings() -> Settings:
    return Settings(api_key="k" * 32, api_url=BASE, min_request_interval=0.0)


@pytest.fixture
async def client(settings):
    c = HorizonClient(settings)
    yield c
    await c.aclose()


async def test_sends_key_and_user_agent(client, httpx_mock):
    httpx_mock.add_response(url=f"{BASE}/", json={"status": "ok", "api": "horizon-api"})
    await client.root()
    request = httpx_mock.get_request()
    assert request.headers["x-api-key"] == "k" * 32
    assert request.headers["user-agent"].startswith("Mozilla/5.0")


async def test_missing_key_maps_to_helpful_error(client, httpx_mock):
    httpx_mock.add_response(url=f"{BASE}/account", status_code=401,
                            json={"status_code": 401, "message": "API key requerida"})
    with pytest.raises(HorizonError, match="API key"):
        await client.account()


async def test_cloudflare_html_403_is_explained(client, httpx_mock):
    httpx_mock.add_response(url=f"{BASE}/account", status_code=403,
                            headers={"content-type": "text/html; charset=UTF-8"},
                            text="<html><title>DELTA90 — Acceso Denegado</title>…1010…</html>")
    with pytest.raises(HorizonError, match="User-Agent"):
        await client.account()


async def test_pagination_follows_scroll_and_stops_at_hits(client, httpx_mock):
    page1 = [fx.port(f"192.0.2.{i}", 80, "http", "nginx", []) for i in range(3)]
    page2 = [fx.port("192.0.2.99", 22, "ssh", "OpenSSH", [])]
    httpx_mock.add_response(url=f"{BASE}/ports?ip=192.0.2.0%2F24",
                            json=fx.envelope(page1, hits=4, scroll_id="s1"))
    httpx_mock.add_response(url=f"{BASE}/ports?ip=192.0.2.0%2F24&scroll_id=s1",
                            json=fx.envelope(page2, hits=4, scroll_id="s2"))
    rows, total = await client.ports("192.0.2.0/24")
    assert total == 4
    assert [r["ip"] for r in rows] == ["192.0.2.0", "192.0.2.1", "192.0.2.2", "192.0.2.99"]
    # No third request: we stopped once `hits` rows were read, saving the empty page.
    assert len(httpx_mock.get_requests()) == 2


async def test_pagination_stops_on_empty_terminal_page(client, httpx_mock):
    # hits lies high (as if rows disappeared mid-scroll): the empty page must end it.
    httpx_mock.add_response(url=f"{BASE}/cves?ip=192.0.2.41",
                            json=fx.envelope(fx.CVES[:2], hits=10, scroll_id="s1"))
    httpx_mock.add_response(url=f"{BASE}/cves?ip=192.0.2.41&scroll_id=s1",
                            json={"ok": True, "error": "", "hits": 10, "size": 0, "data": [],
                                  "scroll_id": None})
    rows, total = await client.cves("192.0.2.41")
    assert len(rows) == 2 and total == 10


async def test_max_rows_caps_fetch_but_keeps_total(client, httpx_mock):
    httpx_mock.add_response(url=f"{BASE}/cves?ip=192.0.2.41",
                            json=fx.envelope(fx.CVES, hits=len(fx.CVES), scroll_id="s1"))
    rows, total = await client.cves("192.0.2.41", max_rows=2)
    assert len(rows) == 2 and total == len(fx.CVES)
    assert len(httpx_mock.get_requests()) == 1


async def test_new_only_is_passed_as_query_flag(client, httpx_mock):
    httpx_mock.add_response(url=f"{BASE}/ports?ip=192.0.2.41&new_only=true",
                            json=fx.envelope([], hits=0, scroll_id=None))
    rows, total = await client.ports("192.0.2.41", new_only=True)
    assert rows == [] and total == 0


async def test_api_level_error_envelope_raises(client, httpx_mock):
    httpx_mock.add_response(url=f"{BASE}/ports?ip=192.0.2.41",
                            json={"ok": False, "error": "account not authorised", "data": []})
    with pytest.raises(HorizonError, match="account not authorised"):
        await client.ports("192.0.2.41")


async def test_network_error_is_wrapped(client, httpx_mock):
    httpx_mock.add_exception(httpx.ConnectError("boom"), url=f"{BASE}/")
    with pytest.raises(HorizonError, match="network error"):
        await client.root()

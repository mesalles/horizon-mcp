"""End-to-end tests: an in-process MCP client talking to the real server object,
with HORIZON's HTTP API mocked."""

import json

import pytest
from mcp import Client

from . import fixtures as fx

BASE = "https://horizon.test"
EXPECTED_TOOLS = {
    "inventory", "open_ports", "cves", "web_findings", "tls_certificates",
    "http_services", "end_of_life", "exposure_summary", "recent_changes",
}


@pytest.fixture(autouse=True)
def _env(monkeypatch):
    monkeypatch.setenv("HORIZON_API_KEY", "t" * 32)
    monkeypatch.setenv("HORIZON_API_URL", BASE)
    monkeypatch.setenv("HORIZON_MIN_INTERVAL", "0")


@pytest.fixture
def server():
    from horizon_mcp.server import mcp
    return mcp


def _payload(result):
    """Tool results arrive as text content holding JSON (plus structuredContent)."""
    if result.structured_content is not None:
        return result.structured_content
    return json.loads(result.content[0].text)


async def test_tools_are_registered_read_only_and_hide_context(server):
    async with Client(server) as client:
        tools = {t.name: t for t in (await client.list_tools()).tools}
    assert set(tools) == EXPECTED_TOOLS
    for tool in tools.values():
        assert tool.annotations is not None and tool.annotations.read_only_hint is True
        assert "ctx" not in (tool.input_schema.get("properties") or {})
        assert tool.description  # the docstring is what the model reads
    assert tools["exposure_summary"].input_schema["required"] == ["host"]
    assert set(tools["cves"].input_schema["properties"]) == {"target", "min_cvss", "limit", "new_only"}


async def test_open_ports_round_trip(server, httpx_mock):
    httpx_mock.add_response(url=f"{BASE}/ports?ip=192.0.2.0%2F24",
                            json=fx.envelope(fx.PORTS, scroll_id="s1"))
    async with Client(server) as client:
        result = await client.call_tool("open_ports", {"target": "192.0.2.0/24"})
    data = _payload(result)
    assert data["target"] == "192.0.2.0/24"
    assert data["total"] == 6 and data["returned"] == 6
    assert data["summary"]["hosts"] == 3
    assert data["ports"][0]["ip"] == "192.0.2.41"
    assert "geoip" not in data["ports"][0]


async def test_hostname_target_returns_error_as_data(server):
    async with Client(server) as client:
        result = await client.call_tool("open_ports", {"target": "www.example.edu"})
    data = _payload(result)
    assert "error" in data and "not an IP address" in data["error"]


async def test_exposure_summary_combines_sources(server, httpx_mock):
    ip = "192.0.2.41"
    only = lambda rows: [r for r in rows if (r.get("ip") or r.get("asn", {}).get("ip")) == ip]  # noqa: E731
    httpx_mock.add_response(url=f"{BASE}/ports?ip={ip}", json=fx.envelope(only(fx.PORTS), scroll_id=None))
    httpx_mock.add_response(url=f"{BASE}/httpinfo?ip={ip}", json=fx.envelope(only(fx.HTTP), scroll_id=None))
    httpx_mock.add_response(url=f"{BASE}/cves?ip={ip}", json=fx.envelope(only(fx.CVES), scroll_id=None))
    httpx_mock.add_response(url=f"{BASE}/vulns_web?ip={ip}", json=fx.envelope(only(fx.WEB), scroll_id=None))
    httpx_mock.add_response(url=f"{BASE}/tls?ip={ip}", json=fx.envelope([], scroll_id=None))
    async with Client(server) as client:
        result = await client.call_tool("exposure_summary", {"host": ip})
    data = _payload(result)
    assert data["host"] == ip
    assert data["open_ports"] == 3
    assert [(h["port"], h["title"]) for h in data["http_services"]] == [(80, "Index of /"), (8080, "Labelling app")]
    assert data["http_services"][0]["tech"] == ["Apache HTTP Server:2.4.52", "Ubuntu"]
    assert data["http_services"][1]["tech"] == []  # optional field in the API
    assert data["max_cvss"] == 9.8
    assert [g["port"] for g in data["cves_by_service"]] == [80, 8080]
    by_name = {f["name"][:20]: f for f in data["web_findings"]}
    assert by_name["Servidor web con lis"]["observed_in_latest_cycle"] is False   # last seen 2026-08-06
    assert by_name["Exposición de inform"]["observed_in_latest_cycle"] is True    # last seen in cycle
    assert data["web_findings_not_reobserved"] == 1
    assert all(g["observed_in_latest_cycle"] is True for g in data["cves_by_service"])
    assert data["data_freshness"]["services"] == "2026-09-15"
    assert data["data_freshness"]["web_findings"] == "2026-09-15"
    assert "note" in data["data_freshness"]
    assert data["last_seen"] == "2026-09-15"


async def test_exposure_summary_rejects_ranges(server):
    async with Client(server) as client:
        result = await client.call_tool("exposure_summary", {"host": "192.0.2.0/24"})
    assert "single IP" in _payload(result)["error"]


async def test_horizon_auth_failure_is_reported_not_raised(server, httpx_mock):
    httpx_mock.add_response(url=f"{BASE}/account", status_code=401, json={"message": "API key requerida"})
    async with Client(server) as client:
        result = await client.call_tool("inventory", {})
    assert "API key" in _payload(result)["error"]


async def test_recent_changes_uses_new_only_and_groups(server, httpx_mock):
    cidr = "192.0.2.0/24"
    new_ports = [r for r in fx.PORTS if r["is_new"]]
    new_cves = [r for r in fx.CVES if r["is_new"]]
    httpx_mock.add_response(url=f"{BASE}/ports?ip=192.0.2.0%2F24&new_only=true",
                            json=fx.envelope(new_ports, scroll_id=None))
    httpx_mock.add_response(url=f"{BASE}/cves?ip=192.0.2.0%2F24&new_only=true",
                            json=fx.envelope(new_cves, scroll_id=None))
    httpx_mock.add_response(url=f"{BASE}/vulns_web?ip=192.0.2.0%2F24&new_only=true",
                            json=fx.envelope([], scroll_id=None))
    async with Client(server) as client:
        result = await client.call_tool("recent_changes", {"target": cidr})
    data = _payload(result)
    assert data["target"] == cidr
    assert data["cycle_date"] == "2026-09-15"
    assert data["counts"] == {"new_services": 1, "new_cve_rows": 2, "new_web_findings": 0}
    assert data["new_services"][0]["port"] == 2200 and data["new_services"][0]["new"] is True
    assert len(data["new_cves_by_service"]) == 1
    assert data["new_cves_by_service"][0]["new_cves"] == 2
    assert data["new_web_findings"] == []
    # exactly one request per source, all with new_only
    assert len(httpx_mock.get_requests()) == 3
    assert all(r.url.params.get("new_only") == "true" for r in httpx_mock.get_requests())

from datetime import date

import pytest

from horizon_mcp import normalize
from horizon_mcp.normalize import (
    TargetError,
    aggregate_cves,
    aggregate_web_findings,
    cpe22_to_23,
    days_since,
    mark_latest_cycle,
    eol_row,
    hosts_summary,
    ms_to_date,
    port_row,
    tls_row,
    validate_target,
)

from . import fixtures as fx


@pytest.fixture(autouse=True)
def _frozen_today(monkeypatch):
    monkeypatch.setattr(normalize, "today", lambda: date(2026, 9, 22))


# --- targets -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("192.0.2.10", "192.0.2.10"),
        (" 192.0.2.0/24 ", "192.0.2.0/24"),
        ("192.0.2.77/24", "192.0.2.0/24"),  # host bits are normalised away
        ("2001:db8::1", "2001:db8::1"),
    ],
)
def test_validate_target_accepts_ips_and_cidrs(raw, expected):
    assert validate_target(raw) == expected


@pytest.mark.parametrize("raw", ["", "example.edu", "192.0.2", "10.0.0.0/8", "not an ip"])
def test_validate_target_rejects_hostnames_and_wide_prefixes(raw):
    with pytest.raises(TargetError):
        validate_target(raw)


# --- helpers -------------------------------------------------------------------------


def test_days_since_and_latest_cycle_marking():
    assert days_since("2026-09-15") == 7
    assert days_since(None) is None and days_since("garbage") is None
    items = [{"last_seen": "2026-09-15"}, {"last_seen": "2026-09-14"}, {"last_seen": "2026-08-06"}, {"last_seen": None}]
    mark_latest_cycle(items, "2026-09-15")
    assert [i["observed_in_latest_cycle"] for i in items] == [True, True, False, None]
    mark_latest_cycle(items, None)
    assert all(i["observed_in_latest_cycle"] is None for i in items)


def test_rows_carry_days_since_last_seen():
    assert port_row(fx.PORTS[0])["days_since_last_seen"] == 7
    assert aggregate_cves(fx.CVES)[0]["days_since_last_seen"] == 7
    assert tls_row(fx.TLS[0])["days_since_last_seen"] == 7


def test_ms_to_date():
    assert ms_to_date(fx.CYCLE_MS) == "2026-09-15"
    assert ms_to_date(None) is None
    assert ms_to_date("garbage") is None


@pytest.mark.parametrize(
    ("cpe22", "cpe23"),
    [
        ("cpe:/a:apache:http_server:2.4.52", "cpe:2.3:a:apache:http_server:2.4.52:*:*:*:*:*:*:*"),
        ("cpe:/a:apache:http_server:-", "cpe:2.3:a:apache:http_server:-:*:*:*:*:*:*:*"),
        ("cpe:/o:canonical:ubuntu_linux", "cpe:2.3:o:canonical:ubuntu_linux:*:*:*:*:*:*:*:*"),
        ("cpe:2.3:a:f5:nginx:1.18.0:*:*:*:*:*:*:*", "cpe:2.3:a:f5:nginx:1.18.0:*:*:*:*:*:*:*"),
    ],
)
def test_cpe22_to_23(cpe22, cpe23):
    assert cpe22_to_23(cpe22) == cpe23


# --- rows ----------------------------------------------------------------------------


def test_port_row_trims_noise_and_handles_optional_product():
    row = port_row(fx.PORTS[0])
    assert row == {
        "ip": "192.0.2.41", "port": 80, "transport": "TCP", "service": "http",
        "product": "Apache httpd", "tls": False,
        "cpes": ["cpe:/a:apache:http_server:2.4.52", "cpe:/o:canonical:ubuntu_linux:-"],
        "first_seen": "2026-08-06", "last_seen": "2026-09-15", "days_since_last_seen": 7, "new": False,
    }
    assert "geoip" not in row and "asn" not in row
    assert port_row(fx.PORTS[4])["product"] is None  # vendorproduct missing


def test_hosts_summary_groups_per_ip_in_address_order():
    summary = hosts_summary([port_row(p) for p in fx.PORTS])
    assert summary["hosts"] == 3
    assert summary["open_ports"] == 6
    assert [h["ip"] for h in summary["by_host"]] == ["192.0.2.34", "192.0.2.41", "192.0.2.53"]
    assert summary["by_host"][1]["ports"] == [22, 80, 8080]
    assert summary["by_host"][1]["services"] == ["http", "ssh"]


def test_aggregate_cves_groups_by_service_and_sorts_by_max_cvss():
    groups = aggregate_cves(fx.CVES)
    assert [(g["ip"], g["port"]) for g in groups] == [
        ("192.0.2.41", 80), ("192.0.2.41", 8080), ("192.0.2.34", 2200),
    ]
    apache = groups[0]
    assert apache["cpe"] == "cpe:/a:apache:http_server:2.4.52"
    assert apache["cve_count"] == 3
    assert apache["max_cvss"] == 9.8
    assert apache["severity"] == "critical"
    assert [c["cve"] for c in apache["cves"]][:2] == ["CVE-2022-31813", "CVE-2023-25690"]
    assert apache["first_seen"] == "2026-08-06" and apache["last_seen"] == "2026-09-15"
    ssh = groups[2]
    assert ssh["new_cves"] == 2 and ssh["first_seen"] == "2026-09-15"


def test_aggregate_cves_min_cvss_filter():
    groups = aggregate_cves(fx.CVES, min_cvss=9.0)
    assert len(groups) == 1
    assert groups[0]["cve_count"] == 2
    assert all(c["cvss"] >= 9.0 for c in groups[0]["cves"])


def test_aggregate_web_findings_collapses_url_variants_and_extracts_ip_port():
    findings = aggregate_web_findings(fx.WEB)
    names = {(f["ip"], f["port"], f["name"]) for f in findings}
    assert len(findings) == 5
    redirect = next(f for f in findings if "redirección" in f["name"])
    assert redirect["ip"] == "192.0.2.36" and redirect["port"] == 80
    assert len(redirect["urls"]) == 3
    phpinfo = next(f for f in findings if "PHPinfo" in f["name"])
    assert phpinfo["port"] == 443  # defaulted from https scheme
    assert ("192.0.2.46", 9090, "Panel de Inicio de Sesión de Cockpit Expuesto") in names
    # severity order: medium > low > panel > info
    assert [f["severity"] for f in findings] == ["medium", "low", "panel", "info", "info"]


def test_tls_row_extracts_certificate_essentials():
    row = tls_row(fx.TLS[0])
    assert row["subject_cn"] == "web.example.edu"
    assert row["subject_alt_names"] == ["web.example.edu", "www.example.edu"]
    assert row["issuer"] == "Let's Encrypt"
    assert row["not_after"] == "2026-12-09"
    assert "name_mismatch" not in row  # always true when connecting by IP: dropped
    assert row["days_to_expiry"] == (date(2026, 12, 9) - date(2026, 9, 22)).days
    assert row["tls_version"] == "tls12"
    assert row["sha256"] == "b" * 64


def test_eol_row_flattens_components_and_has_no_port():
    row = eol_row(fx.EOL[0])
    assert row["ip"] == "192.0.2.41"
    assert row["port"] is None
    assert row["eol_components"] == [{
        "cpe": "cpe:/a:f5:nginx:1.18.0", "release_cycle": "1.18", "eol_date": "2021-04-20",
        "latest_in_cycle": "1.18.0", "is_eol": True,
    }]

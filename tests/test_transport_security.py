"""Eingehende Host/Origin-Pruefung des Streamable-HTTP-Transports (SEC-005).

Ausloeser war kein fehlender Schutz, sondern ein zu strenger an der falschen
Adresse. mcp 2.x aktiviert automatisch eine Allow-List auf ``127.0.0.1:*``, wenn
das ``host``-Argument der App loopback-artig aussieht — und
``streamable_http_app()`` defaultet genau darauf. Cloud-Deployments setzen
``MCP_HOST=0.0.0.0``, also bekam jede Anfrage unter einem echten Hostnamen
HTTP 421, waehrend ``/healthz`` weiter 200 lieferte und es verdeckte.

Vor der Migration auf mcp 2.x erreichte ``host`` den ``FastMCP``-Konstruktor, wo
dieselbe Logik den echten Bind sah und den Schutz korrekt ausliess.
"""

from __future__ import annotations

import pytest
from starlette.testclient import TestClient

from bag_epl_mcp.server import _build_http_app, build_transport_security, settings

_INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "1"},
    },
}
_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


@pytest.fixture(autouse=True)
def _clean_settings(monkeypatch):
    """`settings` ist modulglobal; Felder pro Test zuruecksetzen."""
    monkeypatch.setattr(settings, "allowed_hosts", [], raising=False)
    monkeypatch.setattr(settings, "cors_origins", ["https://claude.ai"], raising=False)
    yield


def test_loopback_bind_is_protected():
    sec = build_transport_security("127.0.0.1", 8000)
    assert sec is not None
    assert sec.enable_dns_rebinding_protection is True
    assert "127.0.0.1:8000" in sec.allowed_hosts


def test_wildcard_bind_without_allowlist_stays_off():
    """Der eigentliche Fix.

    Auf 0.0.0.0 ist der erreichbare Name hier unbekannt, und der
    SDK-Loopback-Default ist genau eine Vermutung — er reproduziert das 421.
    """
    assert build_transport_security("0.0.0.0", 8000) is None


def test_wildcard_bind_with_allowlist_is_protected(monkeypatch):
    monkeypatch.setattr(settings, "allowed_hosts", ["epl.example.ch"])
    sec = build_transport_security("0.0.0.0", 8000)
    assert sec is not None
    assert "epl.example.ch" in sec.allowed_hosts
    # Loopback bleibt drin, sonst brechen Container-Health-Checks.
    assert "127.0.0.1:8000" in sec.allowed_hosts


def test_the_documented_browser_origin_passes_the_transport_check():
    """claude.ai ist der dokumentierte Browser-Use-Case und CORS-Default.

    Ohne diesen Eintrag wuerde der Transport genau den Client abweisen, fuer den
    die CORS-Konfiguration existiert — ein Fehler, der sich erst im Browser
    zeigt, nie in einem Unit-Test.
    """
    sec = build_transport_security("127.0.0.1", 8000)
    assert "https://claude.ai" in sec.allowed_origins


def test_wildcard_cors_is_not_copied(monkeypatch):
    monkeypatch.setattr(settings, "cors_origins", ["*"])
    sec = build_transport_security("127.0.0.1", 8000)
    assert "*" not in sec.allowed_origins


@pytest.mark.parametrize("host", ["127.0.0.1", "localhost", "::1"])
def test_all_loopback_forms_count_as_local(host):
    assert build_transport_security(host, 8000) is not None


def _post(app, host_header: str) -> int:
    with TestClient(app) as client:
        return client.post(
            "/mcp", headers={"Host": host_header, **_HEADERS}, json=_INIT
        ).status_code


def test_a_public_bind_is_reachable_again():
    """Die Regression selbst, durch den echten ASGI-Stack.

    Ohne den ``host``-Kwarg ist das ein 421 — der Zustand, den dieser Commit
    behebt.
    """
    assert _post(_build_http_app("0.0.0.0", 8000), "epl.example.ch") == 200


def test_configured_host_is_served(monkeypatch):
    monkeypatch.setattr(settings, "allowed_hosts", ["epl.example.ch"])
    assert _post(_build_http_app("0.0.0.0", 8000), "epl.example.ch") == 200


def test_foreign_host_is_rejected(monkeypatch):
    monkeypatch.setattr(settings, "allowed_hosts", ["epl.example.ch"])
    assert _post(_build_http_app("0.0.0.0", 8000), "evil.example.com") == 421


def test_right_host_wrong_port_is_rejected(monkeypatch):
    """Der tragende Fall.

    ``evil.example.com`` allein beweist wenig: ein zurueckfallender
    Loopback-Default wuerde ihn ebenfalls abweisen. Nur „richtiger Hostname,
    falscher Port" unterscheidet eine portgenaue Allow-List von einer, die alles
    durchlaesst.
    """
    monkeypatch.setattr(settings, "allowed_hosts", ["epl.example.ch:8000"])
    assert _post(_build_http_app("0.0.0.0", 8000), "epl.example.ch:9999") == 421


def test_healthz_stays_reachable_under_any_host(monkeypatch):
    """Die Asymmetrie ist gewollt — und sie ist auch, was den Fehler verdeckte.

    Der Load-Balancer-Probe muss durchkommen, auch wenn MCP-Anfragen abgewiesen
    werden. Genau deshalb sah ein Deployment gesund aus, das keine einzige
    MCP-Anfrage bedienen konnte; der Test haelt beides zusammen fest.
    """
    monkeypatch.setattr(settings, "allowed_hosts", ["epl.example.ch"])
    app = _build_http_app("0.0.0.0", 8000)
    with TestClient(app) as client:
        assert client.get("/healthz", headers={"Host": "evil.example.com"}).status_code == 200

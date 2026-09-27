"""ARCH-012: die beiden Spec-Revisionen, gegen die dieser Server geprueft ist.

Das SDK bietet keinen setzbaren Pin — die Aushandlung liegt in der
Session-Schicht, weder `MCPServer.__init__` noch `Settings` nimmt den Parameter
entgegen. Ein Pin ist hier deshalb eine erklaerte Konstante plus eine
Zusicherung, die bricht, sobald ein SDK-Bump sie verschiebt. Bewusst CI-seitig
und nicht zur Laufzeit: brechen soll unser Build, nicht der Betrieb von
jemandem, der `mcp` weiter oben aktualisiert hat.

`mcp` 2.x bedient ZWEI Protokoll-Aeren ueber denselben Server; die erste
Anfrage einer Verbindung entscheidet, welche gilt:

* die **Legacy-Aera** mit `initialize`-Handshake — was heutige Clients
  sprechen. Sie deckelt bei `LATEST_HANDSHAKE_VERSION`.
* die **Modern-Aera** mit Pro-Request-Envelope, die `LATEST_MODERN_VERSION`
  erreicht.

**`LATEST_PROTOCOL_VERSION` ist ein Alias auf die MODERNE Version.** Wer nur
dagegen pinnt — die naheliegende Einzelzeile — sichert die Aera, in der heute
praktisch niemand spricht, und laesst die andere frei wandern. Beide stehen
deshalb getrennt hier.

Nachgemessen statt aus Konstantennamen geschlossen: die Aushandlung steht in
`mcp/server/runner.py::_negotiate_initialize` und lautet

    negotiated = requested if requested in HANDSHAKE_PROTOCOL_VERSIONS
                 else LATEST_HANDSHAKE_VERSION

— sie haengt an keinem Transport, gilt also fuer stdio ebenso wie fuer HTTP.

Hier stand, dieses Repo baue keine ASGI-App, durch die sich ein `initialize`
schicken liesse, weshalb nur SDK-Konstanten geprueft wuerden. Das stimmte nicht:
`_build_http_app` baut genau diese App. Die Konstanten-Tests bleiben als Pin;
darunter stehen jetzt gemessene Antworten beider Aeren durch den vollen Stack.
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest
from mcp.types.version import (
    LATEST_HANDSHAKE_VERSION,
    LATEST_MODERN_VERSION,
    LATEST_PROTOCOL_VERSION,
)

REPO = pathlib.Path(__file__).resolve().parents[1]

# Die Revisionen, die die READMEs nennen. Sie stehen hier und nicht im `src/`:
# das SDK bestimmt sie, der Server setzt sie nicht. Eine Konstante im
# Auslieferungspfad waere eine zweite Wahrheit, die driften kann — genau so kam
# `bag-epl-mcp` dazu, Aufrufern `2025-06-18` zu melden.
DOCUMENTED_HANDSHAKE_VERSION = "2025-11-25"
DOCUMENTED_MODERN_VERSION = "2026-07-28"

# Datei und Ueberschrift, unter der die beiden Revisionen dokumentiert stehen.
README_SECTIONS = (
    ("README.md", "## MCP Protocol Version"),
    ("README.de.md", "## MCP-Protokollversion"),
)


def test_die_handshake_aera_steht_wo_die_readme_sie_nennt() -> None:
    """Die Aera, die bestehende Clients sprechen — der lasttragende Pin."""
    assert LATEST_HANDSHAKE_VERSION == DOCUMENTED_HANDSHAKE_VERSION, (
        f"das SDK deckelt den Handshake jetzt bei {LATEST_HANDSHAKE_VERSION}, "
        f"die READMEs sagen {DOCUMENTED_HANDSHAKE_VERSION}. Nicht blind "
        "nachziehen: erst das Spec-Changelog zwischen den beiden Revisionen "
        "lesen, dann README.md, README.de.md und CHANGELOG.md zusammen mit "
        "dieser Konstante bewegen."
    )


def test_die_moderne_aera_steht_wo_die_readme_sie_nennt() -> None:
    assert LATEST_MODERN_VERSION == DOCUMENTED_MODERN_VERSION, (
        f"das SDK erreicht modern jetzt {LATEST_MODERN_VERSION}, die READMEs "
        f"sagen {DOCUMENTED_MODERN_VERSION}"
    )


def test_latest_protocol_version_ist_der_alias_auf_die_moderne_aera() -> None:
    """Die Falle, gegen die dieses Repo abgesichert wird, benannt.

    Ohne diese Zeile liest sich der naheliegende Einzeiler
    `PIN == LATEST_PROTOCOL_VERSION` wie eine vollstaendige Zusicherung. Sie
    ist es nicht, und man sieht es dem Namen nicht an. Faellt dieser Test, hat
    das SDK die Bedeutung des Alias geaendert — dann ist die Aufteilung oben
    neu zu bewerten, nicht nur eine Zahl.
    """
    assert LATEST_PROTOCOL_VERSION == LATEST_MODERN_VERSION
    assert LATEST_PROTOCOL_VERSION != LATEST_HANDSHAKE_VERSION


def test_die_beiden_aeren_sind_verschieden() -> None:
    """Sagt, wann die Aufteilung oben wieder verschwinden darf.

    Faellt das SDK die Aeren eines Tages auf eine Revision zusammen, ist die
    doppelte Zusicherung redundant und gehoert zurueckgebaut. Dieser Test ist
    die Stelle, an der das auffaellt.
    """
    assert LATEST_MODERN_VERSION > LATEST_HANDSHAKE_VERSION


def test_der_pin_ist_eine_datierte_revision_kein_bewegliches_ziel() -> None:
    """«latest» oder eine Spanne wuerde den Zweck des Pins aufheben."""
    for value in (DOCUMENTED_HANDSHAKE_VERSION, DOCUMENTED_MODERN_VERSION):
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), value


def test_beide_readmes_nennen_dieselben_beiden_revisionen() -> None:
    """Ein Pin, den die Doku anders angibt, ist kein Pin.

    Jede Sprache einzeln geprueft: im Portfolio sind EN und DE desselben Repos
    schon dreimal auseinandergelaufen, weil nur eine Fassung nachgezogen wurde
    und niemand die andere daneben gelegt hat.
    """
    for name, anchor in README_SECTIONS:
        text = (REPO / name).read_text(encoding="utf-8")
        parts = text.split(anchor, 1)
        assert len(parts) > 1, f"{name} hat keinen Abschnitt «{anchor}»"
        body = parts[1][:2500]
        for value in (DOCUMENTED_HANDSHAKE_VERSION, DOCUMENTED_MODERN_VERSION):
            assert value in body, f"{name} nennt {value} nicht im Abschnitt «{anchor}»"


@pytest.mark.parametrize(
    ("mode", "erwartet"),
    [
        ("legacy", LATEST_HANDSHAKE_VERSION),
        ("auto", LATEST_MODERN_VERSION),
        (LATEST_MODERN_VERSION, LATEST_MODERN_VERSION),
    ],
)
async def test_der_server_meldet_die_ausgehandelte_revision(mode: str, erwartet: str) -> None:
    """Was `epl_server_info` meldet, gegen das, was die Verbindung ausgehandelt hat.

    Hier stand eine Zusicherung auf `LATEST_HANDSHAKE_VERSION` — gefahren mit
    dem Default-Client, der seit `mcp` 2.x zuerst `server/discover` probt und
    `2026-07-28` spricht. Der Test hielt also genau die Falschmeldung fest:
    ein moderner Client bekam `2025-11-25` gemeldet. `auto` ist der Fall, den
    Clients ohne Einstellung bekommen, und darum der wichtigste.
    """
    from mcp import Client

    from bag_epl_mcp.server import mcp

    async with Client(mcp, mode=mode) as client:
        assert client.protocol_version == erwartet
        result = await client.call_tool("epl_server_info", {})

    assert result.structured_content["protocol_version"] == erwartet


# ─────────────── Gemessen: beide Aeren durch die zusammengebaute HTTP-App ───────

ACCEPT = "application/json, text/event-stream"


@pytest.fixture
def http(monkeypatch: pytest.MonkeyPatch):
    from starlette.testclient import TestClient

    from bag_epl_mcp.server import _build_http_app, settings

    monkeypatch.setattr(settings, "allowed_hosts", [])
    with TestClient(_build_http_app("127.0.0.1", 8000), base_url="http://127.0.0.1:8000") as c:
        yield c


def _modern(http, method: str, params: dict, name: str | None = None) -> dict:
    """Eine `2026-07-28`-Anfrage: kein Handshake, das Envelope in `_meta`."""
    headers = {
        "Accept": ACCEPT,
        "Mcp-Protocol-Version": LATEST_MODERN_VERSION,
        "Mcp-Method": method,
    }
    if name is not None:
        headers["Mcp-Name"] = name
    meta = {
        "io.modelcontextprotocol/protocolVersion": LATEST_MODERN_VERSION,
        "io.modelcontextprotocol/clientInfo": {"name": "gate", "version": "0"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": {**params, "_meta": meta}}
    response = http.post("/mcp", headers=headers, json=body)
    assert response.status_code == 200, response.text
    assert "mcp-session-id" not in response.headers, "die moderne Aera kennt keine Session"
    return response.json()["result"]


def _initialize(http, requested: str) -> dict:
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": requested,
            "capabilities": {},
            "clientInfo": {"name": "gate", "version": "0"},
        },
    }
    response = http.post("/mcp", headers={"Accept": ACCEPT}, json=body)
    assert response.status_code == 200, response.text
    text = response.text
    if response.headers["content-type"].startswith("text/event-stream"):
        text = next(line[5:] for line in text.splitlines() if line.startswith("data:"))
    return json.loads(text)["result"]


def test_http_discover_bietet_die_moderne_revision_an(http) -> None:
    from bag_epl_mcp import __version__

    result = _modern(http, "server/discover", {})

    assert LATEST_MODERN_VERSION in result["supportedVersions"]
    server_info = result["_meta"]["io.modelcontextprotocol/serverInfo"]
    assert server_info == {"name": "bag_epl_mcp", "version": __version__}, (
        "ohne `version=` am Konstruktor meldet das SDK hier einen Leerstring"
    )


def test_http_modern_tool_call_meldet_die_moderne_revision(http) -> None:
    result = _modern(
        http, "tools/call", {"name": "epl_server_info", "arguments": {}}, name="epl_server_info"
    )

    assert result["structuredContent"]["protocol_version"] == LATEST_MODERN_VERSION


@pytest.mark.parametrize(
    ("angefragt", "ausgehandelt"),
    [
        (LATEST_HANDSHAKE_VERSION, LATEST_HANDSHAKE_VERSION),
        # Wer ueber den Handshake die moderne Revision verlangt, bekommt die
        # Obergrenze — die moderne Aera erreicht man nur ueber das Envelope.
        (LATEST_MODERN_VERSION, LATEST_HANDSHAKE_VERSION),
    ],
)
def test_http_initialize_handelt_die_handshake_aera_aus(
    http, angefragt: str, ausgehandelt: str
) -> None:
    from bag_epl_mcp import __version__

    result = _initialize(http, angefragt)

    assert result["protocolVersion"] == ausgehandelt
    assert result["serverInfo"]["version"] == __version__

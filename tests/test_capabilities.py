"""Die Capabilities sagen nur zu, was der Server auch haelt.

Dieser Server veroeffentlicht nie ein Ereignis: Werkzeuge, Ressourcen und
Prompts werden beim Import registriert, die Ressourcen liefern Literale. Also
darf er weder `resources.subscribe` noch ein `listChanged` melden — in keiner
der beiden Aeren. Bis hierhin meldete die moderne Aera (`2026-07-28`) alle vier
als `true`, weil das SDK sie dort aus dem immer registrierten
`subscriptions/listen`-Handler ableitet.

Gemessen ueber echte Verbindungen, nicht durch Ruecklesen der Handler-Tabelle:
die Zusicherung gilt dem, was ein Client sieht.
"""

from __future__ import annotations

import pytest
from mcp import Client
from mcp.server.mcpserver import MCPServer
from mcp.types.version import LATEST_HANDSHAKE_VERSION, LATEST_MODERN_VERSION

from bag_epl_mcp.server import mcp


@pytest.mark.parametrize(
    ("mode", "revision"),
    [("legacy", LATEST_HANDSHAKE_VERSION), ("auto", LATEST_MODERN_VERSION)],
)
async def test_keine_aera_verspricht_abos_oder_listenaenderungen(mode: str, revision: str) -> None:
    async with Client(mcp, mode=mode) as client:
        assert client.protocol_version == revision
        caps = client.session.server_capabilities

    assert caps.resources is not None and caps.resources.subscribe is False
    assert caps.resources.list_changed is False
    assert caps.tools is not None and caps.tools.list_changed is False
    assert caps.prompts is not None and caps.prompts.list_changed is False


async def test_subscriptions_listen_wird_abgewiesen() -> None:
    """Capability und Verhalten muessen zusammenpassen: wer trotzdem lauscht,
    bekommt eine Absage statt eines Streams, auf dem nie etwas ankommt.

    Ueber die zusammengebaute HTTP-App, weil nur dort die Drahtform sichtbar
    ist. Die Zeitschranke ist Teil der Zusicherung: mit Handler bleibt die
    Antwort ein offener SSE-Stream, der Test wuerde sonst haengen statt fallen.
    """
    import anyio
    import httpx

    from bag_epl_mcp.server import _build_http_app

    app = _build_http_app("127.0.0.1", 8000)
    meta = {
        "io.modelcontextprotocol/protocolVersion": LATEST_MODERN_VERSION,
        "io.modelcontextprotocol/clientInfo": {"name": "gate", "version": "0"},
        "io.modelcontextprotocol/clientCapabilities": {},
    }
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "subscriptions/listen",
        "params": {"notifications": {"toolsListChanged": True}, "_meta": meta},
    }
    headers = {
        "Accept": "application/json, text/event-stream",
        "Mcp-Protocol-Version": LATEST_MODERN_VERSION,
        "Mcp-Method": "subscriptions/listen",
    }
    transport = httpx.ASGITransport(app=app)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:8000") as h:
            with anyio.fail_after(5):
                response = await h.post("/mcp", headers=headers, json=body)

    assert response.status_code == 404, response.text
    assert response.json()["error"]["code"] == -32601


async def test_ohne_eingriff_verspricht_das_sdk_abos() -> None:
    """Negativkontrolle: gleiches SDK, gleicher Client, ein nackter `MCPServer`.

    Wird dieser Test rot, meldet das SDK selbst nicht mehr `true` — dann ist
    der Eingriff in `server.py` ueberfluessig und gehoert zurueckgebaut.
    """
    kontrolle = MCPServer("kontrolle")

    @kontrolle.resource("kontrolle://x")
    def _x() -> str:
        return "x"

    async with Client(kontrolle) as client:
        assert client.protocol_version == LATEST_MODERN_VERSION
        caps = client.session.server_capabilities

    assert caps.resources is not None and caps.resources.subscribe is True

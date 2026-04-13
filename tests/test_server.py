"""
Tests fuer den BAG ePL MCP Server.

Mocked-Tests (kein Netzwerk erforderlich) + Live-Tests (opt-in).
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx

from bag_epl_mcp.server import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    SL_API_URL,
    GGSLAbfrageInput,
    MiGeLSucheInput,
    RechtskontextInput,
    ResponseFormat,
    SLSucheInput,
    _handle_error,
    _paginate,
    _sl_website_suche,
    epl_ggsl_abfrage,
    epl_gesuchseingaenge,
    epl_migel_suche,
    epl_rechtskontext,
    epl_server_info,
    epl_sl_suche,
)


# ─────────────────────────── Hilfsfunktionen ───────────────────────────────────

class TestPaginateHelper:
    """Tests fuer die Paginierungshilfe."""

    def test_erste_seite(self):
        result = _paginate(total=50, limit=10, offset=0)
        assert result["total"] == 50
        assert result["limit"] == 10
        assert result["offset"] == 0
        assert result["hat_mehr"] is True

    def test_letzte_seite(self):
        result = _paginate(total=50, limit=10, offset=40)
        assert result["hat_mehr"] is False

    def test_einzelnes_ergebnis(self):
        result = _paginate(total=1, limit=10, offset=0)
        assert result["hat_mehr"] is False

    def test_leere_ergebnisse(self):
        result = _paginate(total=0, limit=10, offset=0)
        assert result["hat_mehr"] is False


class TestHandleError:
    """Tests fuer die Fehlerbehandlung."""

    def test_timeout(self):
        err = httpx.TimeoutException("timeout")
        msg = _handle_error(err, "Test")
        assert "Zeitueberschreitung" in msg
        assert "Test" in msg

    def test_connect_error(self):
        err = httpx.ConnectError("conn failed")
        msg = _handle_error(err, "Test")
        assert "Verbindung fehlgeschlagen" in msg

    def test_http_404(self):
        resp = httpx.Response(404, request=httpx.Request("GET", "https://example.com"))
        err = httpx.HTTPStatusError("not found", request=resp.request, response=resp)
        msg = _handle_error(err)
        assert "404" in msg

    def test_http_429(self):
        resp = httpx.Response(429, request=httpx.Request("GET", "https://example.com"))
        err = httpx.HTTPStatusError("rate limit", request=resp.request, response=resp)
        msg = _handle_error(err)
        assert "429" in msg

    def test_http_503(self):
        resp = httpx.Response(503, request=httpx.Request("GET", "https://example.com"))
        err = httpx.HTTPStatusError("unavailable", request=resp.request, response=resp)
        msg = _handle_error(err)
        assert "503" in msg

    def test_generic_error(self):
        err = ValueError("something wrong")
        msg = _handle_error(err, "Kontext")
        assert "ValueError" in msg
        assert "Kontext" in msg


# ─────────────────────────── Input-Modelle ─────────────────────────────────────

class TestSLSucheInput:
    """Tests fuer SL-Suche-Eingabevalidierung."""

    def test_gueltige_eingabe(self):
        inp = SLSucheInput(suchbegriff="Aspirin")
        assert inp.suchbegriff == "Aspirin"
        assert inp.limit == DEFAULT_LIMIT

    def test_whitespace_stripping(self):
        inp = SLSucheInput(suchbegriff="  Aspirin  ")
        assert inp.suchbegriff == "Aspirin"

    def test_limit_bounds(self):
        inp = SLSucheInput(suchbegriff="Test", limit=50)
        assert inp.limit == 50

    def test_leerer_suchbegriff_rejected(self):
        with pytest.raises(Exception):
            SLSucheInput(suchbegriff="")

    def test_extra_fields_rejected(self):
        with pytest.raises(Exception):
            SLSucheInput(suchbegriff="Test", unbekannt="x")


class TestGGSLAbfrageInput:
    """Tests fuer GGSL-Eingabevalidierung."""

    def test_gueltige_eingabe(self):
        inp = GGSLAbfrageInput(geburtsgebrechen_nr="313")
        assert inp.geburtsgebrechen_nr == "313"

    def test_format_json(self):
        inp = GGSLAbfrageInput(geburtsgebrechen_nr="313", format=ResponseFormat.JSON)
        assert inp.format == ResponseFormat.JSON


class TestMiGeLSucheInput:
    """Tests fuer MiGeL-Eingabevalidierung."""

    def test_gueltige_eingabe(self):
        inp = MiGeLSucheInput(suchbegriff="Rollstuhl")
        assert inp.suchbegriff == "Rollstuhl"

    def test_limit_clamp(self):
        inp = MiGeLSucheInput(suchbegriff="Test", limit=MAX_LIMIT)
        assert inp.limit == MAX_LIMIT


# ─────────────────────────── SL-Suche (Mocked) ────────────────────────────────

class TestSLSucheMocked:
    """Mocked-Tests fuer die SL-Medikamentensuche."""

    @respx.mock
    @pytest.mark.asyncio
    async def test_sl_suche_fallback(self):
        """Phase 1: API nicht verfuegbar -> Fallback mit Info-Link."""
        respx.get(f"{SL_API_URL}/search").mock(side_effect=httpx.ConnectError("no api"))

        result = await _sl_website_suche("Aspirin")
        assert "hinweis" in result
        assert "direkt_link" in result
        assert "Aspirin" in result["direkt_link"]

    @respx.mock
    @pytest.mark.asyncio
    async def test_sl_suche_tool_markdown(self):
        """Tool-Aufruf liefert Markdown mit Fallback-Info."""
        respx.get(f"{SL_API_URL}/search").mock(side_effect=httpx.ConnectError("no api"))

        eingabe = SLSucheInput(suchbegriff="Methylphenidat")
        result = await epl_sl_suche(eingabe)
        assert "SL-Suche" in result
        assert "Methylphenidat" in result
        assert "sl.bag.admin.ch" in result

    @respx.mock
    @pytest.mark.asyncio
    async def test_sl_suche_tool_json(self):
        """Tool-Aufruf im JSON-Format."""
        respx.get(f"{SL_API_URL}/search").mock(side_effect=httpx.ConnectError("no api"))

        eingabe = SLSucheInput(suchbegriff="Aspirin", format=ResponseFormat.JSON)
        result = await epl_sl_suche(eingabe)
        data = json.loads(result)
        assert "hinweis" in data
        assert "direkt_link" in data

    @respx.mock
    @pytest.mark.asyncio
    async def test_sl_suche_api_success(self):
        """Phase 2 Simulation: API antwortet mit Ergebnissen."""
        respx.get(f"{SL_API_URL}/search").mock(
            return_value=httpx.Response(
                200,
                json={"results": [{"name": "Aspirin Cardio"}]},
            )
        )

        result = await _sl_website_suche("Aspirin")
        assert "results" in result
        assert result["results"][0]["name"] == "Aspirin Cardio"


# ─────────────────────────── GGSL ──────────────────────────────────────────────

class TestGGSL:
    """Tests fuer die GGSL-Abfrage."""

    @pytest.mark.asyncio
    async def test_ggsl_markdown(self):
        eingabe = GGSLAbfrageInput(geburtsgebrechen_nr="313")
        result = await epl_ggsl_abfrage(eingabe)
        assert "313" in result
        assert "IVG" in result

    @pytest.mark.asyncio
    async def test_ggsl_json(self):
        eingabe = GGSLAbfrageInput(geburtsgebrechen_nr="404", format=ResponseFormat.JSON)
        result = await epl_ggsl_abfrage(eingabe)
        data = json.loads(result)
        assert data["geburtsgebrechen_nr"] == "404"
        assert "rechtsgrundlage" in data


# ─────────────────────────── MiGeL ─────────────────────────────────────────────

class TestMiGeL:
    """Tests fuer die MiGeL-Suche."""

    @pytest.mark.asyncio
    async def test_migel_markdown(self):
        eingabe = MiGeLSucheInput(suchbegriff="Rollstuhl")
        result = await epl_migel_suche(eingabe)
        assert "Rollstuhl" in result
        assert "KLV" in result

    @pytest.mark.asyncio
    async def test_migel_json(self):
        eingabe = MiGeLSucheInput(suchbegriff="Hoergeraet", format=ResponseFormat.JSON)
        result = await epl_migel_suche(eingabe)
        data = json.loads(result)
        assert data["suchbegriff"] == "Hoergeraet"


# ─────────────────────────── Gesuchseingaenge ──────────────────────────────────

class TestGesuchseingaenge:
    """Tests fuer Gesuchseingaenge."""

    @pytest.mark.asyncio
    async def test_gesuchseingaenge(self):
        result = await epl_gesuchseingaenge()
        assert "Gesuchseingaenge" in result
        assert "sl.bag.admin.ch" in result


# ─────────────────────────── Rechtskontext ─────────────────────────────────────

class TestRechtskontext:
    """Tests fuer Rechtskontext-Abfrage."""

    @pytest.mark.asyncio
    async def test_rechtskontext_markdown(self):
        eingabe = RechtskontextInput(frage="Welche Gesetze regeln die SL?")
        result = await epl_rechtskontext(eingabe)
        assert "KVG" in result
        assert "KLV" in result
        assert "WZW" in result
        assert "fedlex" in result

    @pytest.mark.asyncio
    async def test_rechtskontext_json(self):
        eingabe = RechtskontextInput(
            frage="Rechtsgrundlage SL", format=ResponseFormat.JSON,
        )
        result = await epl_rechtskontext(eingabe)
        data = json.loads(result)
        assert "gesetze" in data
        assert len(data["gesetze"]) >= 3
        assert "wzw_kriterien" in data


# ─────────────────────────── Server-Info ───────────────────────────────────────

class TestServerInfo:
    """Tests fuer Server-Info."""

    @pytest.mark.asyncio
    async def test_server_info(self):
        result = await epl_server_info()
        assert "BAG ePL MCP Server" in result
        assert "Phase 1" in result
        assert "epl_sl_suche" in result


# ─────────────────────────── Live-Tests (opt-in) ──────────────────────────────

@pytest.mark.live
class TestLiveSL:
    """Live-Tests gegen die SL-Website (nur mit -m live)."""

    @pytest.mark.asyncio
    async def test_live_sl_suche(self):
        result = await _sl_website_suche("Aspirin")
        # Phase 1: Entweder Ergebnisse oder Fallback
        assert "direkt_link" in result or "results" in result

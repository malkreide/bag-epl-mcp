"""Was dieser Server ueber seine Quellen sagt, gegen das Gemessene gehalten.

Ohne Netz: Grundlage ist ``tests/fixtures/``, aufgezeichnet am 2026-08-08 von
``scripts/record_fixtures.py``. Die Live-Fassung derselben Fragen steht in
``tests/test_live.py`` und laeuft nur mit ``-m live``.

Diese Trennung hat einen Anlass. Die Live-Tests dieses Repos waren sechsfach
rot und niemand sah es, weil die CI ``-m live`` ausschliesst. Was dauerhaft
gelten soll, gehoert deshalb in eine Datei, die **in** der CI laeuft — die
Aufzeichnung macht das moeglich.
"""

from __future__ import annotations

import re

import pytest
from fixture_data import adresse, payload

from bag_epl_mcp.server import (
    ALLOWED_HOSTS,
    BAG_LEISTUNGEN_URL,
    GESUCHSEINGAENGE_URL_TOT,
    GGSL_INFO_URL_TOT,
    MIGEL_INFO_URL,
    SL_API_URL,
    _sl_kein_api_zugang,
)


class TestAdressenDieDerServerAusgibt:
    """Jede Adresse, die als «offizielle Quelle» weitergegeben wird."""

    def test_die_ausgegebenen_einstiegspunkte_antworteten_mit_200(self):
        for label in ("bag_leistungen", "bag_migel", "sl_portal"):
            assert adresse(label)["status"] == 200

    def test_die_frueher_ausgegebenen_seiten_waren_404(self):
        for label in ("bag_ggsl_tot", "bag_gesuchseingaenge_tot"):
            assert adresse(label)["status"] == 404

    def test_die_kontrolle_traegt_diesen_befund(self):
        """Ohne sie hiesse er nur «ich habe eine 404 bekommen».

        Erst weil ein frei erfundener Pfad im selben Portal ebenfalls 404
        liefert, ist gezeigt, dass die beiden Seiten weg sind — und nicht,
        dass das Portal gerade jede Anfrage abweist.
        """
        assert adresse("kontrolle_bag_erfunden")["status"] == 404

    def test_keine_der_toten_adressen_steht_noch_in_einer_ausgabe(self):
        """Sie bleiben als Konstante stehen, damit der Recorder sie prueft —
        aber sie duerfen in keinem Werkzeug mehr als Quelle erscheinen."""
        from bag_epl_mcp import server

        quelltext = server.__file__
        with open(quelltext, encoding="utf-8") as fh:
            code = fh.read()
        # Die Konstanten selbst und ihre Erwaehnung in Kommentaren sind
        # erlaubt; was nicht sein darf, ist eine Zuweisung an ein Ausgabefeld.
        for feld in ("link=GGSL_INFO_URL_TOT", "direkt_link_bag=GESUCHSEINGAENGE_URL_TOT"):
            assert feld not in code


class TestDieAppHuelleIstKeineAntwort:
    """Der Befund, an dem dieser Server haengt."""

    def test_der_einzige_http_aufruf_bekam_html_nicht_json(self):
        gemessen = adresse("sl_api_search")
        assert gemessen["status"] == 200
        assert "html" in gemessen["content_type"]
        assert "json" not in gemessen["content_type"]

    def test_ein_erfundener_pfad_liefert_byte_fuer_byte_dasselbe(self):
        """Das ist der Beweis, nicht der Statuscode.

        200 auf `/api/search` allein liesse offen, ob dort eine Route liegt,
        die gerade nichts findet. Dass ein frei erfundener Pfad **dieselbe
        Byte-Zahl** liefert, zeigt: Es ist die Single-Page-App, jedes Mal.
        """
        echt = adresse("sl_api_search")
        erfunden = adresse("kontrolle_sl_api_erfunden")
        assert echt["status"] == erfunden["status"] == 200
        assert echt["content_type"] == erfunden["content_type"]
        assert echt["bytes"] == erfunden["bytes"]

    def test_die_antwort_nennt_die_messung_und_nicht_die_folgerung(self):
        ergebnis = _sl_kein_api_zugang("Aspirin", "HTTP 200 mit text/html")
        assert ergebnis["kein_api_zugang"] is True
        assert ergebnis["gemessen"] == "HTTP 200 mit text/html"
        # «nicht oeffentlich dokumentiert» war eine Behauptung ueber das BAG,
        # hergeleitet aus einem JSONDecodeError.
        assert "nicht oeffentlich dokumentiert" not in str(ergebnis)

    def test_der_host_der_app_steht_nicht_auf_der_allow_list(self):
        """Die SL-Oberflaeche ruft `epl.bag.admin.ch/api/sl/` auf.

        Dieser Host antwortet ohne Anmeldung mit 401 — **auch auf erfundene
        Pfade**. Daraus folgt nicht, dass eine bestimmte Route existiert, und
        deshalb waere eine Freigabe hier eine Freigabe auf Verdacht.
        """
        assert "epl.bag.admin.ch" not in ALLOWED_HOSTS


class TestRechtsverweise:
    """Ein falscher ELI-Link oeffnet eine leere Seite mit HTTP 200."""

    def test_jede_sr_nummer_fuehrt_auf_die_ausgegebene_eli(self):
        for kuerzel, v in payload("fedlex_register.json")["verweise"].items():
            assert v["eli_im_server"] in v["eli_im_register"], (
                f"{kuerzel} (SR {v['sr_nummer']}): der Server gibt "
                f"{v['eli_im_server']} aus, das Register fuehrt {v['eli_im_register']}"
            )

    def test_die_kontrolle_traegt_diese_zuordnung(self):
        """Eine erfundene SR-Nummer darf nichts liefern.

        Sonst gaebe die Abfrage fuer alles irgendetwas zurueck, und der Test
        darueber waere erfuellt, ohne etwas zu pruefen.
        """
        assert payload("fedlex_register.json")["kontrolle"]["treffer"] == 0

    def test_der_statuscode_haette_den_falschen_link_nie_gezeigt(self):
        """Warum es den SPARQL-Umweg braucht.

        Die frueher verlinkte ELI und die richtige liefern beide HTTP 200 mit
        derselben Byte-Zahl. Ein Link-Check ueber Statuscodes — die naechste
        naheliegende Idee — haette hier nichts gefunden.
        """
        proben = payload("fedlex_eli_ununterscheidbar.json")
        assert proben["ggsl_falsch_gewesen"]["status"] == 200
        assert proben["ggsl_richtig"]["status"] == 200
        assert proben["ggsl_falsch_gewesen"]["bytes"] == proben["ggsl_richtig"]["bytes"]

    def test_die_ausgegebene_ggsl_eli_ist_die_geprüfte(self):
        from bag_epl_mcp import server

        with open(server.__file__, encoding="utf-8") as fh:
            code = fh.read()
        assert "eli/cc/1986/46_46_46/de" in code
        assert 'fedlex="https://www.fedlex.admin.ch/eli/cc/1986/40_40_40/de"' not in code


class TestKeineFaehigkeitOhneCodepfad:
    def test_es_gibt_genau_einen_ausgehenden_http_aufruf(self):
        """Die Zahl, die den Zustand dieses Servers beschreibt.

        Fuenf der sechs Werkzeuge fragen nichts ab. Steigt diese Zahl, ist
        das eine gute Nachricht — der Test gehoert dann nachgezogen, nicht
        umgangen.
        """
        from bag_epl_mcp import server

        with open(server.__file__, encoding="utf-8") as fh:
            code = fh.read()
        aufrufe = re.findall(r"^\s*(?:resp = )?await _http_get\(", code, re.M)
        assert len(aufrufe) == 1, (
            f"{len(aufrufe)} Aufrufe von `_http_get` gefunden. Am 2026-08-08 "
            "war es genau einer — und er traf eine App-Huelle."
        )

    @pytest.mark.asyncio
    async def test_server_info_bewirbt_keinen_download(self):
        from bag_epl_mcp.server import epl_server_info

        result = await epl_server_info()
        text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
        assert "XML/XLSX-Download" not in text, (
            "«Phase 1 — XML/XLSX-Downloads» stand in der Antwort, die ein "
            "Client bekommt, wenn er den Server nach sich selbst fragt. Einen "
            "Download-Codepfad gibt es nicht."
        )

    @pytest.mark.asyncio
    async def test_werkzeuge_ohne_abruf_sagen_das(self):
        from bag_epl_mcp.server import GGSLAbfrageInput, epl_ggsl_abfrage

        result = await epl_ggsl_abfrage(GGSLAbfrageInput(geburtsgebrechen_nr="313"))
        text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
        assert "NICHT ab" in text or "nicht geprueft" in text
        assert GGSL_INFO_URL_TOT not in text
        assert BAG_LEISTUNGEN_URL in text


class TestDieFalleDieSechsLiveTestsUnbrauchbarMachte:
    """Warum `in` auf einem Tool-Ergebnis niemals zutrifft.

    Sechs Live-Tests dieses Repos schrieben ``assert "..." in result``.
    ``result`` ist ein ``CallToolResult``, also ein Pydantic-Modell: ``in``
    iteriert darauf ueber ``(Feldname, Wert)``-Paare, der Vergleich gegen
    einen String ist damit **immer** falsch. Diese Tests konnten nicht
    bestehen — und weil die CI ``-m live`` ausschliesst, meldete das
    niemandem etwas.

    Dieser Test haelt die Falle fest, damit sie nicht zurueckkehrt.
    """

    @pytest.mark.asyncio
    async def test_ein_direkter_in_vergleich_ist_immer_falsch(self):
        from bag_epl_mcp.server import epl_server_info

        result = await epl_server_info()
        assert "BAG ePL MCP Server" not in result, (
            "Wenn das hier zutrifft, hat sich das Rueckgabeobjekt geaendert — "
            "dann gehoert diese Notiz gestrichen statt weitergetragen."
        )
        text = "\n".join(c.text for c in result.content if hasattr(c, "text"))
        assert "BAG ePL MCP Server" in text


class TestKonstantenStimmenMitDerAufzeichnung:
    """Sonst prueft die Aufzeichnung eine Adresse, die der Server nicht nutzt."""

    def test_jede_gemessene_adresse_stammt_aus_dem_produktivcode(self):
        paare = {
            "bag_leistungen": BAG_LEISTUNGEN_URL,
            "bag_migel": MIGEL_INFO_URL,
            "bag_ggsl_tot": GGSL_INFO_URL_TOT,
            "bag_gesuchseingaenge_tot": GESUCHSEINGAENGE_URL_TOT,
        }
        for label, url in paare.items():
            assert adresse(label)["url"] == url, (
                f"Die Aufzeichnung fuer {label} zeigt auf eine andere Adresse "
                "als der Server baut — dann misst sie den falschen Gegenstand."
            )

    def test_die_sl_messung_nutzt_den_pfad_des_servers(self):
        assert adresse("sl_api_search")["url"].startswith(f"{SL_API_URL}/search")

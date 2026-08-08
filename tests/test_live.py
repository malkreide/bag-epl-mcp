"""
Live-Tests gegen die echten BAG-/Fedlex-Quellen (OPS-001).

Opt-in — nur mit ``pytest -m live``; in der CI standardmaessig ausgeschlossen
(``-m "not live"``).

WAS HIER VORHER STAND, UND WARUM ES NICHTS PRUEFTE. Sechs der acht Tests
verglichen einen String gegen das Rueckgabeobjekt eines Tools::

    assert "BAG ePL MCP Server" in result

``result`` ist ein ``CallToolResult`` — ein Pydantic-Modell. ``in`` iteriert
darauf ueber ``(Feldname, Wert)``-Paare, der Vergleich gegen einen String ist
also **immer** falsch. Diese sechs Tests konnten nicht bestehen. Aufgefallen
ist es nie, weil die CI ``-m live`` ausschliesst: ein Test, der nur
ausserhalb der CI laeuft und dort immer rot ist, meldet niemandem etwas.

UND SELBST BEHOBEN HAETTEN VIER VON IHNEN NICHTS GEZEIGT::

    assert "313" in result   # das Werkzeug schreibt die Eingabe in die Vorlage
    assert "Rollstuhl" in result
    assert "Gesuchseingaenge" in result   # die Ueberschrift, immer da

Sie sicherten zu, dass ein Werkzeug seine eigene Eingabe wiederholt. Genau
das taten fuenf der sechs Werkzeuge — sie fragen nichts ab; im ganzen Modul
steht **ein** ausgehender HTTP-Aufruf.

WAS JETZT GEPRUEFT WIRD, ist die Trennlinie, um die es in diesem Server
geht: ob eine Antwort ein Abruf oder eine Vorlage ist, und ob die Adressen,
die er als «offizielle Quelle» weitergibt, ueberhaupt etwas liefern.
"""

from __future__ import annotations

import httpx
import pytest

from bag_epl_mcp.server import (
    BAG_LEISTUNGEN_URL,
    GESUCHSEINGAENGE_URL_TOT,
    GGSL_INFO_URL_TOT,
    MIGEL_INFO_URL,
    SL_API_URL,
    GGSLAbfrageInput,
    MiGeLSucheInput,
    RechtskontextInput,
    SLSucheInput,
    _sl_website_suche,
    epl_gesuchseingaenge,
    epl_ggsl_abfrage,
    epl_migel_suche,
    epl_rechtskontext,
    epl_server_info,
    epl_sl_suche,
)

pytestmark = [pytest.mark.live, pytest.mark.asyncio]

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; bag-epl-mcp-tests/1.0)"}


def text_of(result) -> str:
    """Der Text aus einem ``CallToolResult``.

    Ohne diese Zeile vergleicht ein ``in`` gegen die Feldnamen des Modells
    und ist immer falsch — der Fehler, an dem sechs Tests dieses Moduls
    jahrelang haengengeblieben sind, ohne dass es jemand sah.
    """
    content = getattr(result, "content", None)
    if content is None:
        return str(result)
    return "\n".join(c.text for c in content if hasattr(c, "text"))


# ─── Der Transportpfad ────────────────────────────────────────────────────────


async def test_live_dns_pinning_tls_ok():
    # SEC-005: echter Request ueber den gepinnten Transport -> TLS muss gegen
    # den Hostnamen valide bleiben, obwohl auf die IP verbunden wird.
    from bag_epl_mcp.server import _new_http_client

    async with _new_http_client() as client:
        resp = await client.get("https://www.fedlex.admin.ch/")
        assert resp.status_code == 200


async def test_live_egress_erlaubt_sl_host():
    # Der Egress-Guard muss sl.bag.admin.ch weiterhin durchlassen — sonst
    # scheiterte die Messung unten schon am eigenen Code.
    ergebnis = await _sl_website_suche("Aspirin")
    assert isinstance(ergebnis, dict)


# ─── Die Trennlinie: Abruf oder Vorlage? ──────────────────────────────────────


async def test_live_sl_api_liefert_die_app_huelle_keine_daten():
    """Der Befund, an dem dieser Server haengt.

    Der einzige HTTP-Aufruf des Servers bekommt HTTP 200 — aber `text/html`.
    Frueher fiel das in ein nacktes `except Exception` und wurde zur Aussage
    «die API ist nicht oeffentlich dokumentiert»: eine Behauptung ueber die
    Quelle, hergeleitet aus einem Parserfehler.
    """
    ergebnis = await _sl_website_suche("Aspirin")
    assert ergebnis.get("kein_api_zugang") is True
    # Die Antwort muss sagen, WAS gemessen wurde — nicht, was daraus
    # geschlossen wurde.
    assert "200" in ergebnis["gemessen"] and "text/html" in ergebnis["gemessen"]


async def test_live_kontrolle_erfundener_pfad_liefert_dasselbe():
    """Ohne diese Kontrolle belegt der Test darueber nichts.

    Erst wenn ein frei erfundener Pfad dieselbe Antwort liefert, ist gezeigt,
    dass unter dieser Adresse gar keine API liegt — statt dass nur diese eine
    Abfrage misslang.
    """
    async with httpx.AsyncClient(timeout=60.0, follow_redirects=True, headers=HEADERS) as c:
        echt = await c.get(f"{SL_API_URL}/search", params={"query": "Aspirin"})
        erfunden = await c.get(f"{SL_API_URL}/diesen-pfad-gibt-es-nicht")
    assert echt.status_code == erfunden.status_code == 200
    assert "html" in echt.headers.get("content-type", "")
    assert len(echt.content) == len(erfunden.content), (
        "Die beiden Antworten unterscheiden sich jetzt — dann liegt unter "
        "/api/ moeglicherweise doch eine Route, und der Befund gehoert neu "
        "gemessen."
    )


async def test_live_sl_suche_nennt_das_gemessene_statt_einer_behauptung():
    md = text_of(await epl_sl_suche(SLSucheInput(suchbegriff="Aspirin")))
    assert "SL-Suche" in md
    assert "nicht oeffentlich dokumentiert" not in md, (
        "Diese Formulierung war eine Behauptung ueber die "
        "Veroeffentlichungspraxis des BAG, hergeleitet aus einem JSON-Parserfehler."
    )


# ─── Die Adressen, die der Server als «offizielle Quelle» ausgibt ─────────────


async def test_live_ausgegebene_einstiegspunkte_antworten():
    async with httpx.AsyncClient(timeout=90.0, follow_redirects=True, headers=HEADERS) as c:
        for url in (BAG_LEISTUNGEN_URL, MIGEL_INFO_URL):
            r = await c.get(url)
            assert r.status_code == 200, f"{url} antwortet mit {r.status_code}"


async def test_live_die_toten_seiten_sind_weiterhin_tot():
    """Nicht Selbstzweck: Kaeme eine zurueck, waere der Befund ueberholt.

    Ein Befund, der still veraltet, ist schlimmer als keiner — dann traegt
    der Server dauerhaft einen Hinweis, der nicht mehr stimmt.
    """
    async with httpx.AsyncClient(timeout=90.0, follow_redirects=True, headers=HEADERS) as c:
        for url in (GGSL_INFO_URL_TOT, GESUCHSEINGAENGE_URL_TOT):
            r = await c.get(url)
            assert r.status_code == 404, (
                f"{url} antwortet wieder mit {r.status_code} — die Seite ist "
                "zurueck, der Link gehoert wiederhergestellt."
            )
        # KONTROLLE: ohne sie hiesse der Befund nur «ich bekomme eine 404».
        r = await c.get(
            "https://www.bag.admin.ch/bag/de/home/versicherungen/"
            "krankenversicherung/diesen-pfad-gibt-es-nicht.html"
        )
        assert r.status_code == 404


async def test_live_ggsl_gibt_keine_tote_adresse_mehr_aus():
    md = text_of(await epl_ggsl_abfrage(GGSLAbfrageInput(geburtsgebrechen_nr="313")))
    assert GGSL_INFO_URL_TOT not in md
    assert BAG_LEISTUNGEN_URL in md
    # Ein Werkzeug, das nichts abruft, muss das sagen. Die alte Fassung
    # schrieb «Die vollstaendige Liste ist beim BAG einsehbar» und liess
    # offen, dass sie gar nicht gesucht hatte.
    assert "NICHT ab" in md or "nicht geprueft" in md


async def test_live_gesuchseingaenge_gibt_keine_tote_adresse_mehr_aus():
    md = text_of(await epl_gesuchseingaenge())
    assert GESUCHSEINGAENGE_URL_TOT not in md
    assert BAG_LEISTUNGEN_URL in md


async def test_live_migel_nennt_die_gepruefte_quelle():
    md = text_of(await epl_migel_suche(MiGeLSucheInput(suchbegriff="Rollstuhl")))
    assert MIGEL_INFO_URL in md


# ─── Die Rechtsverweise ───────────────────────────────────────────────────────


async def test_live_jeder_rechtsverweis_steht_im_register_der_fedlex():
    """Der Weg ueber die Weboberflaeche traegt hier nichts.

    Fedlex ist eine Single-Page-App: JEDE ELI liefert HTTP 200 mit derselben
    Byte-Zahl, auch eine frei erfundene. Der frueher ausgegebene GgV-Link
    (`eli/cc/1986/40_40_40`) zeigte auf eine ELI, die es im Register nicht
    gibt — sichtbar wurde das erst ueber den SPARQL-Endpunkt.
    """
    md = text_of(await epl_rechtskontext(RechtskontextInput(frage="Rechtsgrundlage SL?")))
    paare = {"832.10": "1995/1328_1328_1328", "831.232.21": "1986/46_46_46"}

    async with httpx.AsyncClient(timeout=180.0, follow_redirects=True) as c:

        async def elis_zu(sr: str) -> set[str]:
            query = (
                "PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#> "
                f'SELECT DISTINCT ?work WHERE {{ ?work jolux:historicalLegalId "{sr}" }} LIMIT 20'
            )
            r = await c.get(
                "https://fedlex.data.admin.ch/sparqlendpoint",
                params={"query": query, "format": "application/sparql-results+json"},
                headers={"Accept": "application/sparql-results+json"},
            )
            r.raise_for_status()
            return {
                b["work"]["value"].rsplit("/eli/cc/", 1)[-1].removesuffix("/de")
                for b in r.json()["results"]["bindings"]
            }

        # KONTROLLE zuerst: Eine erfundene SR-Nummer darf nichts liefern —
        # sonst unterscheidet die Abfrage nicht und belegt auch unten nichts.
        assert await elis_zu("999.999") == set()

        for sr, eli in paare.items():
            assert eli in await elis_zu(sr), f"SR {sr} fuehrt nicht auf {eli}"
            assert eli in md, f"Die Ausgabe nennt {eli} nicht"

    assert "1986/40_40_40" not in md, "Der GgV-Link zeigt wieder auf eine ELI ohne Registereintrag."


# ─── Der Server ueber sich selbst ─────────────────────────────────────────────


async def test_live_server_info_bewirbt_keine_faehigkeit_ohne_codepfad():
    """«Phase 1 — XML/XLSX-Downloads» stand hier, ohne dass es sie gab.

    Im ganzen Modul steht ein einziger ausgehender HTTP-Aufruf, und der geht
    an die SL-Suche. Ein Download-Codepfad existiert nicht.
    """
    md = text_of(await epl_server_info())
    assert "BAG ePL MCP Server" in md
    assert "XML/XLSX-Download" not in md

#!/usr/bin/env python3
"""Zeichnet auf, was dieser Server ueber seine Quellen behauptet — und misst es.

    python scripts/record_fixtures.py

WARUM ES DAS GIBT. Ein handgeschriebener Mock kodiert die Annahme seines
Autors und kann sie deshalb prinzipiell nicht widerlegen: Produktivcode und
Fixture stammen aus demselben Kopf, derselben Stunde, derselben Lektuere der
Doku. Wo beide irren, irren beide gleich, und die Suite bleibt dauerhaft
gruen.

WAS HIER AUFGEZEICHNET WIRD, ist nicht die Antwort einer API — dieser Server
hat keine, aus der man eine Fixture ziehen koennte. Aufgezeichnet wird der
Gegenstand, an dem seine Befunde haengen: **ob die Adressen, die er als
«offizielle Quelle» weitergibt, ueberhaupt etwas liefern**, und ob die
Rechtsverweise stimmen, die er ausgibt.

WAS DER ERSTE VERGLEICH AM 2026-08-08 ERGAB.

1. **Der einzige HTTP-Aufruf des Servers trifft eine App-Huelle.**
   `sl.bag.admin.ch/api/search` antwortet mit HTTP 200 und `text/html` —
   51 KB Angular. `raise_for_status()` geht durch, `.json()` wirft, und ein
   nacktes `except Exception` machte daraus die Aussage «Die SL-Datenbank-API
   ist derzeit nicht oeffentlich dokumentiert». Aus einem Parserfehler wurde
   eine Aussage ueber die Veroeffentlichungspraxis des BAG.

2. **Drei ausgegebene «offizielle Quellen» waren HTTP 404.** Fuer zwei
   Werkzeuge WAR dieser Link die ganze Antwort.

3. **Der Fedlex-Verweis auf die GgV zeigte auf eine ELI, die es nicht gibt.**
   Weil Fedlex eine Single-Page-App ist, die fuer jede ELI mit HTTP 200
   antwortet, konnte kein Statuscode das zeigen.

OHNE KONTROLLEN BELEGT DAS NICHTS. Zu jeder Messung gehoert hier ein frei
erfundenes Gegenstueck:

* ein erfundener Pfad unter `sl.bag.admin.ch/api/` — er liefert dieselbe
  200-Huelle, also liegt dort keine API;
* ein erfundener Pfad unter `www.bag.admin.ch/bag/de/` — er liefert 404, also
  sind die drei 404 oben echt und nicht eine Eigenheit des Portals;
* eine erfundene ELI — sie liefert 200, also ist ein 200 dort wertlos;
* eine erfundene SR-Nummer im SPARQL-Endpunkt — sie liefert nichts, also
  unterscheidet diese Abfrage tatsaechlich.

«404 oder 200 auf die einzige Adresse, die man kennt, misst die eigene
Adressliste — nicht den Bestand der Quelle.» Diesen Fehler hat dieses
Portfolio schon dreimal gemacht.

Ohne Aufzeichnungsdatum ist «gemessen» nach zwei Jahren von «angenommen»
nicht mehr zu unterscheiden. Es steht je Eintrag in
`tests/fixtures/PROVENANCE.md`.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures"
sys.path.insert(0, str(ROOT / "src"))

# Die Adressen kommen aus dem Produktivcode, nicht aus einer Abschrift. Ein
# Aufzeichnungsskript, das eine andere Adresse fragt als der Server, misst den
# falschen Gegenstand — und das faellt niemandem auf, weil das Ergebnis
# plausibel aussieht.
from bag_epl_mcp.server import (  # noqa: E402
    BAG_LEISTUNGEN_URL,
    GESUCHSEINGAENGE_URL_TOT,
    GGSL_INFO_URL_TOT,
    MIGEL_INFO_URL,
    SL_API_URL,
    SL_BASE_URL,
)

# Ein Browser-UA ist noetig: www.bag.admin.ch beendet die Verbindung ohne
# Antwort, wenn keiner mitkommt. Das ist keine Umgehung eines Schutzes,
# sondern die Bedingung dafuer, ueberhaupt einen Statuscode zu messen.
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; bag-epl-mcp-fixtures/1.0)"}

SPARQL = "https://fedlex.data.admin.ch/sparqlendpoint"

# Was `epl_rechtskontext` ausgibt: Kuerzel -> (SR-Nummer, ELI-Pfad).
# Gegen den SPARQL-Endpunkt der Fedlex gehalten; die letzte Zeile ist die
# Kontrolle.
RECHTSVERWEISE = {
    "KVG": ("832.10", "1995/1328_1328_1328"),
    "KLV": ("832.112.31", "1995/4964_4964_4964"),
    "IVG": ("831.20", "1959/827_857_845"),
    "GgV": ("831.232.21", "1986/46_46_46"),
}
KONTROLLE_SR = "999.999"


def record() -> int:
    FIXTURES.mkdir(parents=True, exist_ok=True)
    recorded_at = datetime.now(UTC).strftime("%Y-%m-%d")
    entries: list[dict] = []

    def write(name: str, payload: object, url: str, rule: str) -> None:
        text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        (FIXTURES / name).write_text(text, encoding="utf-8")
        entries.append(
            {
                "name": name,
                "url": url,
                "rule": rule,
                "bytes": len(text.encode("utf-8")),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            }
        )
        print(f"ok  {name:<32} {len(text.encode('utf-8')):>8} B")

    with httpx.Client(timeout=90.0, follow_redirects=True, headers=HEADERS) as c:
        # -- 1) Die Adressen, die der Server als Quelle weitergibt ------------
        sonden = [
            (
                "sl_api_search",
                f"{SL_API_URL}/search?query=Aspirin",
                "der einzige HTTP-Aufruf des Servers",
            ),
            (
                "kontrolle_sl_api_erfunden",
                f"{SL_API_URL}/diesen-pfad-gibt-es-nicht",
                "KONTROLLE: erfundener Pfad unter derselben Adresse",
            ),
            ("sl_portal", SL_BASE_URL, "die Weboberflaeche, auf die verwiesen wird"),
            ("bag_leistungen", BAG_LEISTUNGEN_URL, "der Einstiegspunkt, der ausgegeben wird"),
            ("bag_migel", MIGEL_INFO_URL, "die MiGeL-Seite, auf die verwiesen wird"),
            ("bag_ggsl_tot", GGSL_INFO_URL_TOT, "die frueher ausgegebene GGSL-Seite"),
            (
                "bag_gesuchseingaenge_tot",
                GESUCHSEINGAENGE_URL_TOT,
                "die frueher ausgegebene Gesuchseingaenge-Seite",
            ),
            (
                "kontrolle_bag_erfunden",
                "https://www.bag.admin.ch/bag/de/home/versicherungen/"
                "krankenversicherung/diesen-pfad-gibt-es-nicht.html",
                "KONTROLLE: erfundener Pfad im BAG-Portal",
            ),
        ]
        adressen: dict[str, dict] = {}
        for label, url, warum in sonden:
            r = c.get(url)
            adressen[label] = {
                "url": url,
                "status": r.status_code,
                "content_type": r.headers.get("content-type", ""),
                "bytes": len(r.content),
                "warum": warum,
            }
            print(f"    {r.status_code}  {label:<28} {r.headers.get('content-type', '')[:24]}")

        st = {k: v["status"] for k, v in adressen.items()}
        ct = {k: v["content_type"] for k, v in adressen.items()}

        if "html" not in ct["kontrolle_sl_api_erfunden"]:
            raise SystemExit(
                "Ein erfundener Pfad unter sl.bag.admin.ch/api/ liefert keine "
                "HTML-Huelle mehr — dann traegt der Befund nicht mehr, dass "
                "dort gar keine API liegt, und er gehoert neu gemessen."
            )
        if "json" in ct["sl_api_search"]:
            raise SystemExit(
                "sl.bag.admin.ch/api/search antwortet jetzt mit JSON — die API "
                "ist da. Dann gehoert der Aufrufer wiederhergestellt, nicht "
                "die Fixture nachgezogen."
            )
        if st["kontrolle_bag_erfunden"] != 404:
            raise SystemExit(
                f"Ein erfundener BAG-Pfad antwortet mit {st['kontrolle_bag_erfunden']} "
                "statt 404 — ohne diese Kontrolle belegen die 404 unten nichts."
            )
        if st["bag_leistungen"] != 200 or st["bag_migel"] != 200:
            raise SystemExit(
                "Ein Einstiegspunkt, den der Server ausgibt, antwortet nicht "
                f"mehr mit 200: leistungen={st['bag_leistungen']}, "
                f"migel={st['bag_migel']}. Das gehoert behoben, nicht "
                "aufgezeichnet — ein toter Link ist die ganze Antwort dieser "
                "Werkzeuge."
            )
        for tot in ("bag_ggsl_tot", "bag_gesuchseingaenge_tot"):
            if st[tot] == 200:
                raise SystemExit(
                    f"{tot} antwortet wieder mit 200 — die Seite ist zurueck. "
                    "Dann gehoert der Link wiederhergestellt und der Befund "
                    "gestrichen."
                )
        write(
            "quellen_adressen.json",
            {"recorded_at": recorded_at, "adressen": adressen},
            "www.bag.admin.ch, sl.bag.admin.ch",
            "Statuscode, Content-Type und Groesse je Adresse, die dieser "
            "Server als Quelle weitergibt — samt zweier Kontrollen mit "
            "erfundenen Pfaden. Erst die Kontrollen machen aus «ich bekomme "
            "404» die Aussage «diese Seite gibt es nicht», und aus «ich "
            "bekomme 200» die Aussage «hier liegt die App-Huelle, keine API»",
        )

        # -- 2) Die Rechtsverweise gegen das Register der Fedlex --------------
        #
        # Der Weg ueber die Weboberflaeche traegt hier nichts: Sie ist eine
        # Single-Page-App und antwortet fuer JEDE ELI mit 200 und derselben
        # Byte-Zahl. Aufgeloest wird deshalb ueber den SPARQL-Endpunkt.
        def sr_zu_eli(sr: str) -> list[dict]:
            query = (
                "PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#> "
                "SELECT DISTINCT ?work ?kurz WHERE { "
                f'?work jolux:historicalLegalId "{sr}" . '
                "OPTIONAL { ?work jolux:isRealizedBy ?e . "
                "?e jolux:language <http://publications.europa.eu/resource/authority/language/DEU> ; "
                "jolux:titleShort ?kurz } } LIMIT 10"
            )
            r = c.get(
                SPARQL,
                params={"query": query, "format": "application/sparql-results+json"},
                headers={"Accept": "application/sparql-results+json"},
            )
            r.raise_for_status()
            return r.json()["results"]["bindings"]

        register: dict[str, dict] = {}
        for kuerzel, (sr, eli) in RECHTSVERWEISE.items():
            treffer = sr_zu_eli(sr)
            elis = sorted(
                {b["work"]["value"].rsplit("/eli/cc/", 1)[-1].removesuffix("/de") for b in treffer}
            )
            register[kuerzel] = {
                "sr_nummer": sr,
                "eli_im_server": eli,
                "eli_im_register": elis,
                "stimmt": eli in elis,
            }
            print(f"    {'ok ' if eli in elis else 'ABW'}  {kuerzel:<6} SR {sr:<12} {elis}")

        # KONTROLLE: eine SR-Nummer, die es nicht gibt. Ohne sie belegte die
        # Abfrage oben nur, dass sie irgendetwas zurueckgibt.
        kontrolle = sr_zu_eli(KONTROLLE_SR)
        if kontrolle:
            raise SystemExit(
                f"Die erfundene SR-Nummer {KONTROLLE_SR} liefert Treffer — dann "
                "unterscheidet diese Abfrage nicht, und die Zuordnungen oben "
                "sind unbelegt."
            )
        falsch = sorted(k for k, v in register.items() if not v["stimmt"])
        if falsch:
            raise SystemExit(
                f"Diese Rechtsverweise stimmen nicht mit dem Register ueberein: "
                f"{falsch}. Das gehoert behoben, nicht aufgezeichnet — ein "
                "falscher ELI-Link oeffnet eine leere Fedlex-Seite mit HTTP 200."
            )
        write(
            "fedlex_register.json",
            {
                "recorded_at": recorded_at,
                "verweise": register,
                "kontrolle": {
                    "sr_nummer": KONTROLLE_SR,
                    "treffer": len(kontrolle),
                    "warum": "erfundene SR-Nummer; ohne sie belegt die Abfrage nichts",
                },
            },
            f"{SPARQL} (jolux:historicalLegalId)",
            "die Zuordnung SR-Nummer -> ELI aus dem Register der Fedlex, fuer "
            "jedes Gesetz, das `epl_rechtskontext` ausgibt. Der Weg ueber die "
            "Weboberflaeche traegt hier nicht: Sie antwortet fuer JEDE ELI mit "
            "200 und derselben Byte-Zahl, auch fuer eine frei erfundene. Genau "
            "so blieb ein falscher GgV-Verweis unbemerkt",
        )

        # -- 3) Die erfundene ELI, damit der Befund pruefbar bleibt ----------
        eli_proben = {}
        for label, eli in (
            ("ggsl_falsch_gewesen", "1986/40_40_40"),
            ("ggsl_richtig", "1986/46_46_46"),
        ):
            r = c.get(f"https://www.fedlex.admin.ch/eli/cc/{eli}/de")
            eli_proben[label] = {"eli": eli, "status": r.status_code, "bytes": len(r.content)}
        if len({p["status"] for p in eli_proben.values()}) != 1:
            raise SystemExit(
                "Die Fedlex-Oberflaeche unterscheidet jetzt zwischen "
                "vorhandener und erfundener ELI — dann waere der Befund ueber "
                f"den GgV-Link doch am Statuscode sichtbar gewesen: {eli_proben}"
            )
        write(
            "fedlex_eli_ununterscheidbar.json",
            eli_proben,
            "https://www.fedlex.admin.ch/eli/cc/…",
            "zwei ELI-Abrufe ueber die Weboberflaeche: der frueher verlinkte "
            "und der richtige. Beide HTTP 200. DAS ist der Befund — ein "
            "Statuscode konnte den falschen Rechtsverweis nicht zeigen, und "
            "ohne dieses Paar liesse sich das nicht mehr nachvollziehen",
        )

    _write_provenance(recorded_at, entries)
    print(f"\nPROVENANCE.md geschrieben, Aufzeichnungsdatum {recorded_at}")
    return 0


def _write_provenance(recorded_at: str, entries: list[dict]) -> None:
    lines = [
        "# Herkunft der Fixtures",
        "",
        "**Erzeugt von `scripts/record_fixtures.py`. Nicht von Hand pflegen.**",
        "",
        f"Aufgezeichnet am **{recorded_at}**.",
        "",
        "Ohne Datum ist «gemessen» nach zwei Jahren von «angenommen» nicht mehr",
        "zu unterscheiden — die Datei sieht gleich aus.",
        "",
        "## Was hier aufgezeichnet ist, ist nicht eine Antwort",
        "",
        "Dieser Server hat keine API, aus der sich eine Fixture ziehen liesse.",
        "Im ganzen Modul steht **ein** ausgehender HTTP-Aufruf, und der trifft",
        "eine Single-Page-App. Aufgezeichnet ist deshalb der Gegenstand, an dem",
        "seine Aussagen haengen: ob die Adressen, die er als «offizielle",
        "Quelle» weitergibt, etwas liefern — und ob die Rechtsverweise stimmen.",
        "",
        "## Ohne die Kontrollen belegt nichts davon etwas",
        "",
        "Zu jeder Messung gehoert ein frei erfundenes Gegenstueck:",
        "",
        "| Kontrolle | Antwort | Was sie traegt |",
        "|---|---|---|",
        "| erfundener Pfad unter `sl.bag.admin.ch/api/` | 200 + `text/html` | dort liegt keine API, sondern die App |",
        "| erfundener Pfad unter `www.bag.admin.ch/bag/de/` | 404 | die 404 der drei Seiten sind echt |",
        "| erfundene ELI bei der Fedlex | 200 | ein 200 dort ist wertlos |",
        "| erfundene SR-Nummer im SPARQL-Endpunkt | kein Treffer | die Abfrage unterscheidet |",
        "",
        "Ohne sie belegte jede Messung nur, was **ich** bekommen habe — nicht,",
        "was die Quelle fuehrt. Dieses Portfolio hat den Unterschied bereits",
        "dreimal verwechselt.",
        "",
        "Das Aufzeichnungsskript bricht ab, wenn eine Kontrolle nicht mehr",
        "traegt, wenn ein Einstiegspunkt stirbt, wenn eine der toten Seiten",
        "zurueckkehrt oder wenn ein Rechtsverweis vom Register abweicht. Ein",
        "Befund, der still veraltet, ist schlimmer als keiner.",
        "",
    ]
    for e in entries:
        lines += [
            f"## `{e['name']}`",
            "",
            f"- **Quelle:** `{e['url']}`",
            f"- **Aufgezeichnet:** {recorded_at}",
            f"- **Auswahl:** {e['rule']}",
            f"- **Groesse:** {e['bytes']} B",
            f"- **SHA-256:** `{e['sha256']}`",
            "",
        ]
    (FIXTURES / "PROVENANCE.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    try:
        raise SystemExit(record())
    except httpx.HTTPError as exc:
        print(f"FEHLER: Quelle nicht erreichbar: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

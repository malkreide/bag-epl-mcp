[\U0001f1ec\U0001f1e7 English Version](README.md)

> \U0001f1e8\U0001f1ed **Teil des [Swiss Public Data MCP Portfolios](https://github.com/malkreide)**

# \U0001f48a bag-epl-mcp

![Version](https://img.shields.io/badge/version-1.0.3-blue)
[![Lizenz: MIT](https://img.shields.io/badge/Lizenz-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![Kein API-Schluessel](https://img.shields.io/badge/Auth-keiner%20erforderlich-brightgreen)](https://github.com/malkreide/bag-epl-mcp)
![CI](https://github.com/malkreide/bag-epl-mcp/actions/workflows/ci.yml/badge.svg)

> MCP-Server fuer die elektronische Plattform Leistungen (ePL) des BAG — Spezialitaetenliste, GGSL, MiGeL

### Demo

![Demo: Claude nutzt epl_sl_suche und epl_rechtskontext](docs/assets/demo.svg)

---

## Uebersicht

`bag-epl-mcp` ermoeglicht KI-Modellen, Fragen zur obligatorischen Krankenpflegeversicherung in natuerlicher Sprache zu beantworten — verankert in echten Daten.

| Liste | Zweck | Rechtsgrundlage |
|-------|-------|-----------------|
| **Spezialitaetenliste (SL)** | Kassenpflichtige Medikamente | KVG Art. 52 |
| **GGSL** | Medikamente bei Geburtsgebrechen (IV) | IVG Anhang |
| **MiGeL** | Medizinprodukte und Hilfsmittel | KLV Art. 20 |

**Anker-Abfrage:** *«Ist dieses Medikament kassenpflichtig?»*
→ `epl_sl_suche`: Direktabfrage in der Spezialitaetenliste (SL)
→ [Weitere Anwendungsbeispiele nach Zielgruppe →](EXAMPLES.md)

---

## Funktionen

- \U0001f48a **6 Tools, 2 Resources, 2 Prompts** fuer Schweizer Gesundheitsdaten
- \U0001f50d **`epl_sl_suche`** — Medikamentensuche in der Spezialitaetenliste
- ⚖️ **`epl_rechtskontext`** — Rechtliche Grundlagen mit Fedlex-Links
- \U0001f513 **Kein API-Schluessel erforderlich** — alle Daten oeffentlich zugaenglich
- ☁️ **Dualer Transport** — stdio (Claude Desktop) + Streamable HTTP (Cloud)
- \U0001f4da **Prompt-Vorlagen** fuer Kassenpflicht-Checks und Schulgesundheit

---

## Voraussetzungen

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (empfohlen) oder pip

---

## Installation

```bash
git clone https://github.com/malkreide/bag-epl-mcp.git
cd bag-epl-mcp
pip install -e .
```

Oder mit `uvx`:

```bash
uvx bag-epl-mcp
```

---

## Schnellstart

```bash
# stdio (fuer Claude Desktop) — Default, oeffnet keine Netzwerk-Ports
python -m bag_epl_mcp.server

# Streamable HTTP (Cloud) — Transport-Wahl ueber Env-Variable
MCP_TRANSPORT=streamable-http MCP_HOST=0.0.0.0 MCP_PORT=8000 \
  pip install -e ".[http]" && python -m bag_epl_mcp.server
```

> **Transport und Host werden ausschliesslich ueber Umgebungsvariablen**
> gesteuert (`MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`). Default ist `stdio`;
> `MCP_HOST` ist `127.0.0.1` und sollte nur im Container auf `0.0.0.0` gesetzt
> werden. Sicherheitsmodell: siehe [`docs/SECURITY.md`](docs/SECURITY.md).

---

## Verfuegbare Tools

| Tool | Beschreibung |
|------|-------------|
| `epl_sl_suche` | Kassenpflichtige Medikamente in der SL suchen |
| `epl_ggsl_abfrage` | GGSL-Deckung bei Geburtsgebrechen pruefen |
| `epl_migel_suche` | Medizinprodukte in der MiGeL suchen |
| `epl_gesuchseingaenge` | Transparenzliste SL-Neuaufnahmen abrufen |
| `epl_rechtskontext` | Rechtliche Grundlagen zur Kassenpflicht (WZW) |
| `epl_server_info` | Serverstatus und API-Phaseninfo |

---

## Architektur

**Datenfluss (Phase 1):**

```
                         bag-epl-mcp (FastMCP)
 ┌────────────┐   MCP   ┌───────────────────────────────┐   HTTPS GET  ┌──────────────────┐
 │ MCP-Client │◀───────▶│  Tools (nur lesend)           │─────────────▶│ sl.bag.admin.ch  │
 │ (Claude    │ stdio / │   ├─ epl_sl_suche             │  Egress-     │ www.bag.admin.ch │
 │  Desktop,  │ Stream- │   ├─ epl_ggsl_abfrage         │  Allow-List  │ www.fedlex...    │
 │  claude.ai)│ able    │   ├─ epl_migel_suche          │◀─────────────│ (oeffentl. OGD)  │
 │            │ HTTP    │   ├─ epl_gesuchseingaenge     │  (keine Auth)└──────────────────┘
 │            │         │   ├─ epl_rechtskontext        │
 │            │         │   └─ epl_server_info          │   strukturierte JSON-Logs → stderr
 └────────────┘         │  resources: epl://uebersicht …│
                        │  prompts:   epl_kassenpflicht…│
                        └───────────────────────────────┘
```

**Phasenplan** (Details in [`docs/ROADMAP.md`](docs/ROADMAP.md)):

```
Phase 1 (aktuell)  → Rechtskontext + Einstiegspunkte, ohne Datenabruf
Phase 2 (geplant)  → FHIR/IDMP-API, sobald oeffentlich zugaenglich
Phase 3 (Vision)   → MiGeL + AL via ePL-FHIR
```

**Was Phase 1 tut — und was nicht.** Fuenf der sechs Werkzeuge stellen
ueberhaupt keine Netzwerkanfrage; im ganzen Modul steht genau ein ausgehender
HTTP-Aufruf. Sie geben Rechtsgrundlage und Einstiegspunkt zurueck, und sie
sagen das jetzt auch. Die fruehere Beschreibung «XML/XLSX-Downloads +
SL-Website-Zugriff» bewarb eine Faehigkeit ohne Codepfad; sie wurde am
2026-08-08 gestrichen statt umgesetzt, weil die zugrundeliegende Quelle nicht
maschinenlesbar ist.

Dieser eine Aufruf geht an `sl.bag.admin.ch/api/search` und bekommt **HTTP 200
mit `text/html`** — die 51 KB grosse Angular-Huelle. Ein frei erfundener Pfad
unter demselben Praefix liefert byte-identisch dasselbe: Dort liegt keine API.
Bisher fing ein nacktes `except Exception` den daraus folgenden
JSON-Parserfehler und machte daraus die Aussage «Die SL-Datenbank-API ist
derzeit nicht oeffentlich dokumentiert» — eine Behauptung ueber die
Veroeffentlichungspraxis des BAG, hergeleitet aus einem Parserfehler. Das
Werkzeug nennt jetzt, was gemessen wurde.

Die SL-Oberflaeche ruft stattdessen `https://epl.bag.admin.ch/api/sl/` auf,
also einen anderen Host. Der antwortet ohne Anmeldung mit 401 — aber auch auf
erfundene Pfade, weshalb daraus **nicht** folgt, dass eine bestimmte Route
existiert. Er steht bewusst **nicht** auf der Egress-Allow-List: Ohne
pruefbaren Zugang waere das eine Freigabe auf Verdacht.

**MCP-Protokoll-Version:** `2025-11-25` (via `epl_server_info`) — die
Obergrenze des `initialize`-Handshakes, aus dem SDK abgeleitet statt hier ein
zweites Mal hingeschrieben. Beide Aeren stehen unter
[MCP-Protokollversion](#mcp-protokollversion). SDK-Updates
werden monatlich via Dependabot vorgeschlagen.

---

## Sicherheit & Grenzen

- **Nur lesend:** Alle Tools fuehren ausschliesslich HTTP-GET-Anfragen aus — keine Daten werden geschrieben, geaendert oder geloescht.
- **Keine Personendaten:** Der Server greift auf oeffentliche Regulierungslisten (SL, GGSL, MiGeL) zu. Es werden keine personenbezogenen Daten (PII) verarbeitet oder gespeichert.
- **Keine medizinische Beratung:** Dieser Server bietet rein informativen Zugang zu regulatorischen Daten. Fuer medizinische oder rechtliche Entscheidungen konsultieren Sie die offiziellen BAG-Quellen und qualifizierte Fachpersonen.
- **Rate Limits:** Die SL-Website (sl.bag.admin.ch) ist eine oeffentliche Angular-SPA; der Server erzwingt ein 30s-Timeout pro Anfrage. Verwenden Sie `limit`-Parameter konservativ.
- **Datenaktualitaet:** Phase-1-Tools verlinken auf Live-BAG-Quellen. Kein Caching durch diesen Server.
- **Links werden gemessen, nicht angenommen:** Die Adressen, die als «offizielle Quelle» weitergegeben werden, prueft `scripts/record_fixtures.py` bei jedem Lauf neu — samt einer Kontrollanfrage an einen erfundenen Pfad. Zwei frueher ausgegebene BAG-Seiten (`.../Arzneimittel/geburtsgebrechen-spezialitaetenliste.html` und `.../Arzneimittel/gesuchseingaenge.html`) antworteten am 2026-08-08 mit HTTP 404 und wurden durch den nachweislich erreichbaren Einstiegspunkt ersetzt — nicht durch eine geratene Ersatzadresse.
- **Rechtsverweise werden gegen das Register geprueft:** Jede SR-Nummer, die der Server ausgibt, wird ueber den SPARQL-Endpunkt der Fedlex auf ihre ELI aufgeloest. Dieser Umweg ist noetig: Die Fedlex-Oberflaeche ist eine Single-Page-App und antwortet fuer *jede* ELI mit HTTP 200 und derselben Byte-Zahl, auch fuer eine erfundene. Genau so blieb ein falscher GgV-Link (`eli/cc/1986/40_40_40`, kein Registereintrag) unbemerkt; richtig ist `eli/cc/1986/46_46_46`.
- **Datenlizenz (OGD-CH):** Die zugrundeliegenden BAG-/Fedlex-Daten sind Swiss Open Government Data, lizenziert unter **CC BY 4.0**. Tool-Antworten fuehren einen `source`/`provenance`-Block (JSON) bzw. eine Quellen-/Lizenz-Fusszeile (Markdown), damit die Attribution erhalten bleibt.
- **Nutzungsbedingungen:** Daten unterliegen den Nutzungsbedingungen von [sl.bag.admin.ch](https://sl.bag.admin.ch), [bag.admin.ch](https://www.bag.admin.ch) und [fedlex.admin.ch](https://www.fedlex.admin.ch).
- **Keine Garantie:** Community-Projekt, nicht affiliiert mit dem BAG oder einer Behoerde. Verfuegbarkeit haengt von den Upstream-Quellen ab.

---

## MCP-Protokollversion

Dieser Server bedient **zwei Protokoll-Aeren** ueber denselben Endpunkt. Die
erste Anfrage einer Verbindung entscheidet, welche gilt; ein spaeterer Anspruch
aus der jeweils anderen Aera wird abgewiesen.

| Aera | Revision | Wer sie erreicht |
|---|---|---|
| `initialize`-Handshake | `2024-11-05` … **`2025-11-25`** | Was heutige Clients sprechen. Der Server antwortet mit der angefragten Revision — oder mit der Obergrenze `2025-11-25`, wenn die Anfrage etwas Neueres verlangt. |
| Pro-Request-Envelope | **`2026-07-28`** | Eine Anfrage mit dem `2026-07-28`-`_meta`-Envelope oeffnet eine moderne Verbindung. |

Beide Revisionen sind in
[`tests/test_protocol_version.py`](tests/test_protocol_version.py) gepinnt und
werden gegen das installierte SDK geprueft; ein Dependabot-Bump von `mcp` kann
also keine der beiden still verschieben. Dieser Server baut keine ASGI-App, durch die sich ein `initialize`
schicken liesse; das Gate sichert deshalb die SDK-Konstanten statt einer
gemessenen Antwort — die schwaechere Form, benannt statt verschwiegen.

Zu beachten: `LATEST_PROTOCOL_VERSION` im SDK ist ein Alias auf die **moderne**
Aera, nicht auf die Handshake-Aera — wer nur dagegen pinnt, laesst genau die
Aera frei wandern, die heutige Clients tatsaechlich aushandeln.

**Update-Politik.** Faellt das Gate, die Konstante nicht blind nachziehen: erst
das Spec-Changelog zwischen den beiden Revisionen lesen, pruefen, ob sich der
Server weiterhin richtig verhaelt, dann Konstante, diesen Abschnitt, `README.md`
und [`CHANGELOG.md`](CHANGELOG.md) gemeinsam bewegen.

---

## Tests

```bash
# Unit- und Vertragstests (ohne Netz) — das faehrt die CI
PYTHONPATH=src pytest tests/ -m "not live"

# Live-Tests gegen die echten BAG-/Fedlex-Quellen
PYTHONPATH=src pytest tests/ -m "live"

# Messungen neu aufzeichnen (schreibt tests/fixtures/ + PROVENANCE.md)
PYTHONPATH=src python scripts/record_fixtures.py
```

**100 Tests** — 88 offline, 12 gegen die Live-Quellen.

### Warum es neben den Live-Tests eine Vertragsdatei gibt

Bis zum 2026-08-08 konnten sechs der acht Live-Tests **nicht bestehen**. Sie
verglichen einen String gegen das Rueckgabeobjekt eines Werkzeugs:

```python
assert "BAG ePL MCP Server" in result   # result ist ein CallToolResult
```

`CallToolResult` ist ein Pydantic-Modell; `in` iteriert darauf ueber
`(Feldname, Wert)`-Paare, der Vergleich ist also immer falsch. Aufgefallen ist
es nie, weil die CI `-m live` ausschliesst — ein Test, der nur ausserhalb der
CI laeuft und dort immer rot ist, meldet niemandem etwas.

Und selbst behoben haetten vier von ihnen nichts gezeigt: `assert "313" in
result` gegen ein Werkzeug, das die Eingabe in seine Vorlage schreibt, `assert
"Rollstuhl" in result` ebenso. Sie sicherten zu, dass ein Werkzeug seine
eigene Eingabe wiederholt — genau das, was diese Werkzeuge tun.

Was dauerhaft gelten soll, steht deshalb in `tests/test_quellen_vertrag.py`
und laeuft **in** der CI gegen die aufgezeichneten Messungen unter
`tests/fixtures/`. `PROVENANCE.md` nennt je Datei Quelle, Datum, Auswahlregel
und SHA-256.

Vier der Messungen sind **Kontrollen** — ein erfundener Pfad unter
`sl.bag.admin.ch/api/`, ein erfundener Pfad im BAG-Portal, eine erfundene ELI
und eine erfundene SR-Nummer. Ohne sie zeigte jede Messung nur, was *ich*
bekommen habe, nicht was die Quelle fuehrt. Der Recorder bricht ab, wenn eine
Kontrolle nicht mehr traegt, wenn ein Einstiegspunkt stirbt, wenn eine der
toten Seiten zurueckkehrt oder wenn ein Rechtsverweis vom Register abweicht.

---

## Changelog

Siehe [CHANGELOG.md](CHANGELOG.md)

---

## Mitwirken

Siehe [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Sicherheit

Siehe [SECURITY.de.md](SECURITY.de.md) ([English](SECURITY.md)) für die
Sicherheitslage und die Meldung von Schwachstellen.

---

## Lizenz

MIT-Lizenz — siehe [LICENSE](LICENSE)

---

## Autor

Hayal Oezkan · [malkreide](https://github.com/malkreide)

---

## Credits & Verwandte Projekte

- **BAG Spezialitaetenliste:** [sl.bag.admin.ch](https://sl.bag.admin.ch) — Bundesamt fuer Gesundheit
- **KVG:** [SR 832.10](https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/de) — Krankenversicherungsgesetz
- **KLV:** [SR 832.112.31](https://www.fedlex.admin.ch/eli/cc/1995/4964_4964_4964/de) — Krankenpflege-Leistungsverordnung
- **Protokoll:** [Model Context Protocol](https://modelcontextprotocol.io/) — Anthropic / Linux Foundation
- **Verwandt:** [fedlex-mcp](https://github.com/malkreide/fedlex-mcp) — Schweizer Bundesrecht
- **Verwandt:** [swiss-cultural-heritage-mcp](https://github.com/malkreide/swiss-cultural-heritage-mcp) — Kulturerbe-Daten
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Behoben

- **Beide READMEs zeigten literale `\uXXXX`-Sequenzen statt Zeichen.** 37
  Zeilen in `README.md`, 36 in `README.de.md`; insgesamt 507 Sequenzen, davon
  allein 320 waagrechte Rahmenstriche. Auf GitHub stand dort sichtbar
  `\u2192` statt `→` und im Architekturdiagramm eine Wand aus
  `\u2500\u2500\u2500`.

  Entstanden ist das unabhaengig von den Datentreue-Aenderungen — eine Datei
  war irgendwann durch einen JSON-escapenden Pfad gelaufen. Aufgeloest sind
  jetzt alle Sequenzen; ausserhalb des Diagramms ist der Text Zeichen fuer
  Zeichen derselbe.

- **Das Architekturdiagramm war schief, und das Escaping hat es verdeckt.**
  Erst mit aufgeloesten Zeichen wurde sichtbar, dass die Kastenraender nicht
  fluchten: Der linke Rand des mittleren Kastens stand mal auf Spalte 23, mal
  auf 24, der rechte zwischen 56 und 58.

  Solange dort `\u250c\u2500\u2500` stand, war es kein Diagramm, sondern
  eine Zeichenkette — falsch ausrichten kann man nur, was man sieht. Der
  Rahmen ist mit festen Spaltenbreiten neu gesetzt, in beiden Sprachen
  identisch.


### Behoben

- **Der Fedlex-Verweis auf die GgV zeigte auf eine ELI, die es nicht gibt.**
  Ausgegeben wurde `eli/cc/1986/40_40_40`; das Register der Fedlex fuehrt
  unter SR 831.232.21 die ELI `eli/cc/1986/46_46_46` («Verordnung vom
  9. Dezember 1985 ueber Geburtsgebrechen»).

  Kein Statuscode haette das zeigen koennen. Die Fedlex-Oberflaeche ist eine
  Single-Page-App und antwortet fuer **jede** ELI mit HTTP 200 — beide
  Adressen liefern exakt 77 151 Byte. Wer den Link anklickte, bekam eine
  Seite, die leer blieb, ohne Fehlermeldung.

  Aufgeloest ueber den SPARQL-Endpunkt der Fedlex
  (`jolux:historicalLegalId`). Kontrolle: Die erfundene SR-Nummer 999.999
  liefert dort keinen Treffer, die Abfrage unterscheidet also. Alle vier
  Rechtsverweise (KVG, KLV, IVG, GgV) stehen jetzt gegen das Register
  geprueft im Code.

- **Drei ausgegebene «offizielle Quellen» waren HTTP 404** —
  `.../Arzneimittel/geburtsgebrechen-spezialitaetenliste.html`,
  `.../Arzneimittel/gesuchseingaenge.html` und
  `.../krankenversicherung-leistungen-tarife` (ohne `.html`). Fuer
  `epl_ggsl_abfrage` und `epl_gesuchseingaenge` WAR dieser Link die ganze
  Antwort: ausgeliefert wurde eine Sackgasse in der Aufmachung einer
  Auskunft.

  Kontrolle: Ein frei erfundener Pfad im BAG-Portal antwortet mit demselben
  404 und demselben Titel «Error 404: Seite nicht gefunden» — die drei 404
  sind also echt und keine Eigenheit des Portals.

  **Ersatzadressen sind bewusst nicht geraten.** Die BAG-Navigation liegt
  hinter JavaScript, und die Portalsuche ist selbst 404. Eine plausibel
  gebaute URL waere genau der Fehler, den dieser Commit behebt. Ausgegeben
  wird jetzt der Einstiegspunkt, der nachweislich mit 200 antwortet, samt
  Hinweis, dass die frueher verlinkte Seite nicht mehr existiert.

- **Aus einem JSON-Parserfehler wurde eine Aussage ueber das BAG.**
  `_sl_website_suche` fing jeden Fehler in einem nackten `except Exception`
  und antwortete «Die SL-Datenbank-API ist derzeit nicht oeffentlich
  dokumentiert».

  Gemessen worden ist das nie. `sl.bag.admin.ch/api/search` antwortet mit
  **HTTP 200** und `text/html` — 51 KB Angular-Huelle. `raise_for_status()`
  geht durch, `.json()` wirft, und der Rest war eine Behauptung ueber die
  Veroeffentlichungspraxis einer Behoerde.

  Kontrolle: Ein frei erfundener Pfad unter `/api/` liefert **byte-identisch
  dasselbe** (51 710 B). Unter dieser Adresse liegt gar keine API. Die
  Funktion prueft jetzt Statuscode und Content-Type und gibt zurueck, was
  gemessen wurde — nicht, was jemand daraus geschlossen hat.

  Nebenbefund, bewusst nicht verwertet: Die SL-Oberflaeche ruft intern
  `https://epl.bag.admin.ch/api/sl/` auf, also einen anderen Host. Der
  antwortet mit 401 — **auch auf erfundene Pfade**, weshalb daraus nicht
  folgt, dass eine bestimmte Route existiert. Er steht deshalb nicht auf der
  Egress-Allow-List; ohne pruefbaren Zugang waere das eine Freigabe auf
  Verdacht.

- **`epl_server_info` bewarb eine Faehigkeit ohne Codepfad.** «Phase 1 —
  XML/XLSX-Downloads + SL-Website-Zugriff» stand in der Antwort, die ein
  Client bekommt, wenn er den Server nach sich selbst fragt. Einen XML- oder
  XLSX-Download gibt es nicht: Im ganzen Modul steht **ein** ausgehender
  HTTP-Aufruf, und der geht an die SL-Suche.

  Die Phasenbeschreibung nennt jetzt, was der Server tut. Fuenf der sechs
  Werkzeuge fragen nichts ab, und ihre Antworten sagen das — vorher hiess es
  «Die vollstaendige Liste ist beim BAG einsehbar», ohne offenzulegen, dass
  gar nicht gesucht worden war.

- **Sechs der acht Live-Tests konnten nicht bestehen.** Sie verglichen einen
  String gegen ein `CallToolResult`; das ist ein Pydantic-Modell, `in`
  iteriert darauf ueber `(Feldname, Wert)`-Paare, und der Vergleich ist damit
  immer falsch.

  Aufgefallen ist es nie, weil die CI `-m live` ausschliesst: Ein Test, der
  nur ausserhalb der CI laeuft und dort immer rot ist, meldet niemandem
  etwas.

  Und selbst behoben haetten vier von ihnen nichts gezeigt. `assert "313" in
  result` gegen ein Werkzeug, das die Eingabe in seine Vorlage schreibt;
  `assert "Rollstuhl" in result` ebenso; `assert "Gesuchseingaenge" in
  result` traf die Ueberschrift. Sie sicherten zu, dass ein Werkzeug seine
  eigene Eingabe wiederholt.

### Hinzugefuegt

- **Aufgezeichnete Messungen statt Annahmen** — `tests/fixtures/`,
  `scripts/record_fixtures.py`, `tests/fixture_data.py` und ein
  `PROVENANCE.md` mit Quelle, Datum, Auswahlregel und SHA-256 je Datei.

  Aufgezeichnet ist hier nicht die Antwort einer API — dieser Server hat
  keine, aus der sich eine Fixture ziehen liesse. Aufgezeichnet ist der
  Gegenstand, an dem seine Aussagen haengen: ob die Adressen, die er als
  «offizielle Quelle» weitergibt, etwas liefern, und ob die Rechtsverweise
  stimmen.

  **Vier der Messungen sind Kontrollen**: ein erfundener Pfad unter
  `sl.bag.admin.ch/api/` (liefert dieselbe Huelle — dort ist keine API), ein
  erfundener Pfad im BAG-Portal (liefert 404 — die 404 oben sind echt), eine
  erfundene ELI (liefert 200 — ein 200 dort ist wertlos) und eine erfundene
  SR-Nummer (liefert nichts — die Registerabfrage unterscheidet). Ohne sie
  belegte jede Messung nur, was ich bekommen habe.

  Das Skript bricht ab, wenn eine Kontrolle nicht mehr traegt, wenn ein
  Einstiegspunkt stirbt, wenn eine der toten Seiten zurueckkehrt oder wenn
  ein Rechtsverweis vom Register abweicht. Ein Befund, der still veraltet,
  ist schlimmer als keiner.

- **`tests/test_quellen_vertrag.py`** — 18 Tests, die **in** der CI laufen.
  Das ist der Punkt: Was dauerhaft gelten soll, gehoert nicht in eine Datei,
  die die CI ueberspringt.

- **`tests/test_live.py` neu geschrieben** — 12 Tests statt 8, jeder mit einer
  Zusicherung, die fehlschlagen kann. Darunter zwei, die pruefen, dass die
  toten Seiten tot bleiben und die Kontrollen weiter tragen: Kaeme eine Seite
  zurueck, waere der Befund ueberholt und der Hinweis im Code falsch.

  Gegengeprueft mit fuenf gezielten Rueckmutationen — falsche GgV-ELI, alte
  XML/XLSX-Behauptung, toter Link zurueck in die Ausgabe, Behauptung statt
  Messung in der SL-Antwort, und der `in`-Vergleich gegen das rohe
  Rueckgabeobjekt. Alle fuenf machen die Suite rot.

## [1.0.3] - 2026-08-02

### Behoben

- **`structlog` hatte keine Obergrenze, und der Index fuehrt bereits einen Major
  oberhalb der Untergrenze.** Deklariert war `structlog>=25.5.0`; auf PyPI liegt
  `26.1.0`. Das Artefakt aendert sich nicht — die Antwort des Resolvers auf
  die naechste frische Installation schon, und genau so wurde
  `swiss-energy-mcp` 0.3.3 uninstallierbar, als `mcp` 2.0.0 das Modul entfernt
  hat, das es importierte.

  Neu `structlog>=25.5.0,<27`. Die Grenze ist gemessen, nicht geraten: dieses Paket installiert
  und importiert heute gegen `structlog 26.1.0`, die Obergrenze laesst also zu,
  was nachweislich funktioniert, und stoppt nur den naechsten, unbekannten
  Major.

Ein Abhaengigkeitsbereich erreicht die Nutzenden nur ueber ein neues
Release, daher der Versions-Bump. Am Code aendert sich nichts.

## [1.0.2] - 2026-07-31

### Hinzugefuegt

- **Der Server nennt jetzt seinen Namen.** Bisher ging gegenueber jedem
  Upstream der httpx-Default hinaus: der Betreiber der Datenquelle sah
  eine Bibliothek, nicht uns, und hatte keinen Weg, uns bei Fehlverhalten
  zu erreichen. Neu traegt den HTTP-Client
  `bag-epl-mcp/<version> (+github.com/malkreide/bag-epl-mcp)`.

  Die Version stammt aus `importlib.metadata` und kann nicht getrennt vom
  Paket driften.

### Fixed

- **Streamable-HTTP wies unter jedem echten Hostnamen mit 421 ab (SEC-005).**
  `_build_http_app()` rief `mcp.streamable_http_app()` ohne `host` auf. Unter
  mcp 2.x ist das kein neutraler Default: das SDK leitet daraus seine
  Host-Allow-List ab und aktiviert bei loopback-artigem Wert automatisch
  `127.0.0.1:*`. Da das Argument selbst auf `127.0.0.1` defaultet, traf das jedes
  Cloud-Deployment mit `MCP_HOST=0.0.0.0`. Vor der Migration ging `host` an den
  `FastMCP`-Konstruktor, wo dieselbe Logik den echten Bind sah und den Schutz
  korrekt ausliess.

  Besonders tückisch hier: `/healthz` ist bewusst von der Transport-Prüfung
  ausgenommen (SCALE-004) und antwortete weiter mit 200. Ein Load-Balancer sah
  also einen gesunden Server, der keine einzige MCP-Anfrage bedienen konnte.

  Der Bind reist jetzt in die App, und eine echte Allow-List wird aus dem neuen
  `MCP_ALLOWED_HOSTS` gebaut. Ohne diese Variable bleibt der Schutz auf einem
  Nicht-Loopback-Bind bewusst aus und der Aufrufer warnt — eine geratene Liste
  wäre genau der 421-Fall. `https://claude.ai` (CORS-Default) wird in die
  Origin-Liste übernommen, sonst weist der Transport genau den Browser-Client ab,
  für den die CORS-Konfiguration existiert.

  13 neue Tests, darunter der tragende Fall „richtiger Hostname, falscher Port"
  und einer, der die `/healthz`-Asymmetrie festhält — sie ist gewollt, war aber
  auch der Grund, warum der Fehler verdeckt blieb. Mutationsgetestet: nimmt man
  den `host`-Kwarg wieder weg, reproduziert der Test das 421.

  Geprüft mit den wörtlichen CI-Kommandos: 70 passed / 8 deselected,
  `ruff check src/ tests/` clean, Versions-Sync OK.


### Fixed

- **Capped `mcp` at `<2`.** `mcp` 2.0.0, published 2026-07-28, removed
  `mcp.server.fastmcp` — the module this server imports. With the previous
  unbounded `>=1.28.1` every fresh resolve picked 2.0.0 and failed at import
  with `ModuleNotFoundError`, in CI and for anyone running `pip install` alike.
  Verified in both directions: 2.0.0 fails, `<2` resolves to 1.29.0 and imports
  cleanly. Migrating to the 2.x API (`mcp.server.mcpserver`) stays a separate,
  deliberate piece of work.

## [0.2.0] - 2026-06-01

### Added
- **Env-based transport selection** (`MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`):
  the Streamable HTTP transport for cloud deployment is now actually
  implemented (previously only documented). Default remains `stdio`.
- CORS middleware on the HTTP transport exposing `Mcp-Session-Id` for browser
  clients (claude.ai), with an explicit origin allow-list (`MCP_CORS_ORIGINS`).
- Tool annotations (`readOnlyHint`, `openWorldHint`) on all six tools.
- Egress allow-list guard (`ALLOWED_HOSTS` + `_assert_safe_url`): HTTPS-only,
  host allow-list, and resolved-IP blocklist (SSRF protection) before any
  outbound request.
- `docs/SECURITY.md` — threat model (Lethal-Trifecta assessment, no-auth/
  session rationale, egress and host-binding policy).
- `[http]` optional dependency group (`uvicorn`, `starlette`).
- **Multi-stage `Dockerfile`** (slim base, non-root UID 10001, `HEALTHCHECK`)
  and `render.yaml` Blueprint with health check and resource plan.
- `/healthz` HTTP endpoint for load-balancer probes.
- **Lifespan-managed pooled `httpx.AsyncClient`** (connection reuse / keep-alive)
  instead of a fresh client per request.
- **Structured JSON logging** via `structlog`, written to **stderr** (stdout
  stays reserved for the stdio JSON-RPC stream); full error detail is logged
  server-side while the model only sees a sanitized message.
- `$PORT` fallback for `MCP_PORT` (PaaS/Render compatibility).
- **Structured response envelope** for tool JSON output: `source`, `provenance`
  (incl. `license`), `match_type`, `count`, `results` (SDK-002, ARCH-003).
- **OGD-CH attribution** (CC BY 4.0) in every tool response — JSON `provenance`
  block and Markdown source/licence footer (CH-004).
- `<use_case>` tags in all tool docstrings (ARCH-002).
- `protocolVersion` constant + update policy; surfaced via `epl_server_info`
  (ARCH-012); `.github/dependabot.yml` for monthly pip / actions updates.
- `docs/ROADMAP.md` with phase gates and sign-offs (OPS-003); data-flow
  architecture diagram in both READMEs (OPS-002).
- Optional OpenTelemetry tracing (`[otel]` extra, `MCP_OTEL_ENABLED`) — OBS-006.
- `scripts/snapshot_tool_hashes.py` + release-workflow step recording SHA-256
  hashes of tool definitions (SEC-022).
- Tests split into `tests/test_unit.py` (mocked) and `tests/test_live.py`
  (opt-in, one per tool) with a shared `conftest.py` (OPS-001).
- `ctx: Context` injection in all tools + per-tool-call bound structured logging
  context (`tool`, `correlation_id`, `request_id`/`client_id`) — SDK-003 / OBS-003.
- **Structured tool output (SDK-002):** all 6 tools now declare typed Pydantic
  output schemas and return `structuredContent` alongside the curated Markdown
  (`content`) — a hybrid `CallToolResult`, so machine consumers get a validated
  schema with no loss of the human-readable output.
- **OpenTelemetry on by default (OBS-006):** `MCP_OTEL_ENABLED` now defaults to
  on; a silent no-op when the `[otel]` extra isn't installed (base installs and
  stdout are unaffected). `TracerProvider` + OTLP exporter +
  Starlette/httpx auto-instrumentation; set `MCP_OTEL_ENABLED=0` to disable.
- **DNS-pinned HTTP transport** (`_PinnedNetworkBackend`): the host is resolved
  exactly once, the resolved IP is validated and the TCP connection pinned to it,
  while TLS SNI/cert verification still use the hostname — eliminates the
  resolve/connect TOCTOU (SEC-005).
- `deploy/haproxy.cfg`: reference sticky-session (Mcp-Session-Id stick-table +
  TTL) config for the horizontal-scaling path (SCALE-002/003).

### Changed
- Console entrypoint is now `bag_epl_mcp.server:main` (transport-aware).
- Configuration via a `pydantic-settings` `ServerSettings` object instead of
  module-level transport globals.
- Errors now surface as MCP `isError` results (raised `ToolError`); the generic
  error path no longer echoes raw exception messages to the model.
- Corrected README/README.de deployment instructions to the real
  env-var-based mechanism and the `/mcp` endpoint.
- Input models now use Pydantic `strict=True` (the `format` field stays lenient
  so clients may pass the string `"json"`/`"markdown"`) — SEC-018.

### Security
- Addresses audit findings SCALE-001, ARCH-009, SDK-004, SEC-004/005/021,
  SEC-016, SEC-019, SEC-009, OBS-001/002 (Phase 1); SEC-007, SCALE-004,
  SCALE-006, SDK-001, OBS-003 (Phase 2); and SEC-018, SEC-022, ARCH-002,
  ARCH-012, SDK-002, ARCH-003, CH-004, OBS-006, OPS-001/002/003 (Phase 3);
  and SDK-003, OBS-003, SEC-005, SDK-002, OBS-006 (post-re-audit follow-up). See
  `docs/audit/2026-06-01/` and `docs/audit/2026-06-01-reaudit/`.

## [0.1.0] - 2026-04-13

### Added
- Initial release with Phase 1 implementation (no authentication required)
- **SL module**: `epl_sl_suche` — search the Spezialitaetenliste
- **GGSL module**: `epl_ggsl_abfrage` — check congenital disorder coverage
- **MiGeL module**: `epl_migel_suche` — search medical devices
- **Transparency**: `epl_gesuchseingaenge` — pending SL admission requests
- **Legal context**: `epl_rechtskontext` — WZW criteria, KVG/KLV/IVG references
- **Server info**: `epl_server_info` — status and phase information
- 2 Resources: `epl://uebersicht`, `epl://rechtsrahmen`
- 2 Prompts: `epl_kassenpflicht_check`, `epl_schulgesundheit_recherche`
- Dual transport: stdio (Claude Desktop) + Streamable HTTP (cloud/Render.com)
- GitHub Actions CI (Python 3.11, 3.12, 3.13)
- Bilingual documentation (DE/EN)
- Unit and integration tests (mocked HTTP via respx)

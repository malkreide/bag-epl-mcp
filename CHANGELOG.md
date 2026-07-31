# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

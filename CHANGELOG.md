# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

### Changed
- Console entrypoint is now `bag_epl_mcp.server:main` (transport-aware).
- Configuration via a `pydantic-settings` `ServerSettings` object instead of
  module-level transport globals.
- Errors now surface as MCP `isError` results (raised `ToolError`); the generic
  error path no longer echoes raw exception messages to the model.
- Corrected README/README.de deployment instructions to the real
  env-var-based mechanism and the `/mcp` endpoint.

### Security
- Addresses audit findings SCALE-001, ARCH-009, SDK-004, SEC-004/005/021,
  SEC-016, SEC-019, SEC-009, OBS-001/002 (Phase 1) and SEC-007, SCALE-004,
  SCALE-006, SDK-001, OBS-003 (Phase 2). See `docs/audit/2026-06-01/`.

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

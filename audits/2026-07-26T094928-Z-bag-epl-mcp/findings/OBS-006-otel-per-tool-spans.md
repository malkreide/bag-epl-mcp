## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `OBS-006` |
| **PDF-Reference** | Anhang B10 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

OpenTelemetry is wired up (TracerProvider + OTLP exporter, Starlette + httpx auto-instrumentation) and on by default, but only produces request-level and outbound-httpx spans. There is no per-tool span carrying MCP-specific attributes.

### Expected Behavior

OBS-006 Modus 1 expects one span per tool call named after the tool, with attributes `mcp.tool.name`, `mcp.user.id`, and `mcp.tool.result.is_error`, so slow-tool and behaviour analysis are possible.

### Evidence

- `src/bag_epl_mcp/server.py:950-982` — `_init_otel` instruments the ASGI app and httpx client only; no `tracer.start_as_current_span('mcp.tool.<name>')`
- `src/bag_epl_mcp/server.py:966-975` — tracing sits behind the optional `[otel]` extra and is a silent no-op if not installed
- `pyproject.toml:44-49` — otel is an optional extra, not a base dependency

### Risk Description

Without per-tool spans, P99-latency attribution per tool and anomalous tool-sequence detection are not available; in a base install (no `[otel]` extra) there is no tracing at all.

### Remediation

Add a tracing decorator that wraps each `@mcp.tool` handler and opens `mcp.tool.<name>` spans with `mcp.tool.name` and `mcp.tool.result.is_error` (omit PII; use a `sub`/opaque id only if auth is ever added). Optionally promote the otel packages to base deps or document the extra as required for cloud.

### Effort Estimate

M

### Dependencies / Blockers

None.

### Verification After Fix

Re-audit OBS-006: a span per tool call is visible in the OTLP backend with the required attributes.

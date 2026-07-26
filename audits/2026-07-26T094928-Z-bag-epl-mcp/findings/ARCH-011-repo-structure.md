## Finding: ARCH-011 — Standardisierte Repo-Struktur (src-Layout, tests, README.de.md)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `ARCH-011` |
| **PDF-Reference** | Anhang A8 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

The repo satisfies almost the whole standard layout (src-layout, tests/, .github/workflows/, all mandatory top-level files), but all 6 tools plus resources, prompts, settings, HTTP client, envelopes and the HTTP app live in a single `src/bag_epl_mcp/server.py` of ~1010 lines.

### Expected Behavior

For servers with more than 5 tools, ARCH-011 Modus 4 expects a `tools/` package (one file per tool group) and a `server.py` reduced to registry + lifecycle (~200 lines).

### Evidence

- `src/bag_epl_mcp/server.py` — single file, ~1010 lines, holds all 6 tool bodies (lines 511-850), 2 resources (855-886), 2 prompts (891-915), settings, egress guard and HTTP app
- No `src/bag_epl_mcp/tools/` directory present
- `pyproject.toml:69` — correct src-layout otherwise

### Risk Description

Low direct risk. A 1010-line module raises code-review and test-isolation cost and makes portfolio-wide tooling assumptions (file-per-tool-group) inconsistent as the server grows into Phase 2/3.

### Remediation

Split tool bodies into `src/bag_epl_mcp/tools/{sl,ggsl,migel,rechtskontext,info}.py`, keep `server.py` as the FastMCP registry + lifespan. Move Pydantic schemas into `schemas/` and the egress guard into `clients/`.

### Effort Estimate

M

### Dependencies / Blockers

None.

### Verification After Fix

Re-audit ARCH-011 Modus 4: `ls src/bag_epl_mcp/tools/*.py` returns files and `wc -l src/bag_epl_mcp/server.py` < 200.

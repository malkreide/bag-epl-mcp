## Finding: SEC-014 — Tool-Allow-Listing via MCP-Gateway-Pattern

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | accepted-risk |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `SEC-014` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

There is no MCP-gateway per-team/role default-deny tool allow-list. The tool surface is static, read-only and authored in-repo (PR-reviewed).

### Expected Behavior

SEC-014 (applicable because cloud-deployed) expects a default-deny tool allow-list per team/role plus server-side role checks for sensitive tools and audit of denied calls - typically at a gateway.

### Evidence

- `docs/SECURITY.md:101-110` — documents the absence of gateway tool allow-listing and the rationale
- `SECURITY.md:58-63` — recorded as portfolio/gateway-layer accepted-risk
- All 6 tools are unconditionally exposed, read-only, epl_-namespaced

### Risk Description

Low for a single public read-only server with no sensitive tools. Becomes relevant only when aggregated behind a shared gateway serving multiple teams/enterprise context.

### Remediation

When the server sits behind a portfolio MCP gateway, define a default-deny per-team/role allow-list there and audit denied tool calls. No server-side change is needed for the standalone read-only deployment.

### Effort Estimate

M

### Dependencies / Blockers

Requires a portfolio MCP gateway to exist.

### Verification After Fix

Re-audit SEC-014 once a gateway is in place: confirm default-deny allow-list and denied-call auditing.

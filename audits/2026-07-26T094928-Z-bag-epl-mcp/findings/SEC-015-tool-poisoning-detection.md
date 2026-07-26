## Finding: SEC-015 — Pre-Flight Tool-Poisoning Detection

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | accepted-risk |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `SEC-015` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

No pre-flight tool-poisoning detection layer exists (no scanning for system-prompt injection, override phrases, invisible characters, or homoglyphs in tool definitions).

### Expected Behavior

SEC-015 (applicable because cloud-deployed) expects a gateway-level detection layer covering at least four pattern classes, with high-risk tools filtered default-deny and audit events to a SIEM.

### Evidence

- `docs/SECURITY.md:101-110` — documents absence of pre-flight tool-poisoning detection; tools are static and in-repo
- `SECURITY.md:58-63` — recorded as gateway/host-layer accepted-risk
- `scripts/snapshot_tool_hashes.py` — tool definitions are hashed at release (change-detection), but no content scanning

### Risk Description

Low: this server only exposes its own static, reviewed tools, so there is no untrusted/remote tool registration to poison. Relevant only when aggregating third-party tools behind a shared host.

### Remediation

Implement pattern-class detection (system-prompt/override/invisible-char/homoglyph) at the portfolio gateway; forward audit events to SIEM. Not required for this server's own static tool set.

### Effort Estimate

M

### Dependencies / Blockers

Requires a portfolio MCP gateway.

### Verification After Fix

Re-audit SEC-015 once a gateway exists: confirm detection tests for standard attack patterns.

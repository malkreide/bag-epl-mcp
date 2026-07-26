## Finding: OPS-002 — Doku-Standard: bilingualer README, ASCII-Diagramm, Limits-Sektion

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `OPS-002` |
| **PDF-Reference** | Anhang C2 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

README.md contains all 8 mandatory sections; README.de.md is close but omits the dedicated Configuration section (Claude Desktop config JSON + Cloud Deployment) that the English README has, so top-level section parity is incomplete.

### Expected Behavior

OPS-002 expects README.de.md to carry the same top-level sections as README.md.

### Evidence

- `README.md:101-155` — `## Configuration` with `### Claude Desktop` and `### Cloud Deployment`
- `README.de.md` — sections jump from Schnellstart to Verfuegbare Tools; no equivalent `## Konfiguration` block
- All other sections (overview, tools, architecture, safety, license) exist in both

### Risk Description

Low. German-speaking operators (Swiss public-sector context) miss the Claude Desktop config block in their language, increasing setup friction and weakening the bilingual documentation norm.

### Remediation

Add a `## Konfiguration` section to README.de.md mirroring README.md:101-155 (Claude Desktop JSON + Cloud Deployment env vars).

### Effort Estimate

S

### Dependencies / Blockers

None.

### Verification After Fix

Re-audit OPS-002: `grep '^## ' README.md` and README.de.md yield matching top-level section inventories.

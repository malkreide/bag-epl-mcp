## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Praefix gegen Rug Pull

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `SEC-022` |
| **PDF-Reference** | Anhang B4 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

All tools carry the consistent `epl_` namespace prefix, and a deterministic SHA-256 snapshot of tool definitions is generated at each release - but the snapshot is uploaded as a CI artifact only; no baseline `tool-hashes.json` is committed to the repo to diff against.

### Expected Behavior

SEC-022 expects the tool-definition hash snapshot to be generated at release AND stored in the repo, so a committed baseline exists for rug-pull detection, with CHANGELOG discipline and semver bumps on tool changes.

### Evidence

- `src/bag_epl_mcp/server.py:511-800` — consistent `epl_` namespace prefix on all tools
- `scripts/snapshot_tool_hashes.py:24-36` — deterministic SHA-256 over name+description+inputSchema+annotations
- `.github/workflows/publish.yml:26-45` — snapshot produced at release and uploaded as an artifact, not committed

### Risk Description

Without an in-repo baseline, a silent tool-definition change (rug pull) has no committed reference to diff against in code review; detection relies on CHANGELOG discipline and recovering the prior CI artifact.

### Remediation

Commit a `tool-hashes.json` baseline into the repo and update it in the release PR (or add a CI check that diffs the generated snapshot against the committed baseline and fails on unexplained drift). Keep the namespace prefix and CHANGELOG discipline.

### Effort Estimate

S

### Dependencies / Blockers

Synergy with ARCH-012 (CHANGELOG) release discipline.

### Verification After Fix

Re-audit SEC-022: a committed baseline exists and CI diffs new snapshots against it.

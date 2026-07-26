## Finding: SCALE-002 — Stateful Load Balancing fuer Streamable HTTP / SSE

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | accepted-risk |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `SCALE-002` |
| **PDF-Reference** | Sec 5.2 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

Streamable-HTTP sessions are stateful, but the deployed Render service runs a single instance. Sticky-session routing exists only as a reference HAProxy config that is not part of the actual deployment, and there is no shared-state (Redis/Durable Objects) session manager.

### Expected Behavior

SCALE-002 expects at least one of: sticky sessions on the edge LB keyed on `Mcp-Session-Id`, or a shared-state session manager - actually implemented, with an explicit TTL and a failover test.

### Evidence

- `deploy/haproxy.cfg:30-37` — reference stick-table (Mcp-Session-Id, 30m TTL), not wired into Render
- `render.yaml` — single web service, no LB fan-out, no shared session store
- `docs/SECURITY.md:41-56` — documents single-instance Phase-1 operation requirement

### Risk Description

If the service is scaled to more than one replica without first enabling sticky routing/shared state, follow-up requests can hit a backend that never created the session, breaking in-flight Streamable-HTTP sessions.

### Remediation

For multi-instance: deploy the `deploy/haproxy.cfg` stick-table (or a platform equivalent) in front of the replicas, or add a Redis-backed shared session manager; add a failover test. For Phase 1, keep the documented single-instance constraint.

### Effort Estimate

M

### Dependencies / Blockers

Tied to SCALE-003 (same Mcp-Session-Id routing).

### Verification After Fix

Re-audit SCALE-002 with a multi-instance failover test showing a session surviving a backend change.

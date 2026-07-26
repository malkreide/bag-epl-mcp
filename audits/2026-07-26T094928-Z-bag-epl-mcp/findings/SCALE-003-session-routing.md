## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB (HAProxy Stick-Tables)

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | accepted-risk |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `SCALE-003` |
| **PDF-Reference** | Sec 5.2 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

An HAProxy stick-table config keyed on the Mcp-Session-Id header (100k capacity, 30m TTL) is provided but is not deployed - Render runs a single instance with no edge LB in front - and failover behaviour is untested.

### Expected Behavior

SCALE-003 expects the edge LB to actually read `Mcp-Session-Id`, route via a stick-table/hash of >=100k capacity with an explicit TTL, and to have tested failover behaviour.

### Evidence

- `deploy/haproxy.cfg:33-34` — `stick-table type string len 64 size 100k expire 30m` + `stick on req.hdr(Mcp-Session-Id)`
- No edge LB in the actual Render deployment (render.yaml single service)
- `docs/SECURITY.md:41-56` — routing + TTL documented for the scaling path only

### Risk Description

Same class of risk as SCALE-002: without a deployed session-affinity layer, horizontal scaling would misroute stateful sessions.

### Remediation

When scaling horizontally, deploy the provided stick-table config (or K8s Ingress affinity) in front of the replicas and run a backend-loss failover test.

### Effort Estimate

M

### Dependencies / Blockers

Blocks/pairs with SCALE-002.

### Verification After Fix

Re-audit SCALE-003 against a live multi-replica deployment with session-affinity enabled and a failover test.

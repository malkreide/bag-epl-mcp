## Finding: SCALE-006 — Resource-Limits per Container (Memory, CPU, FDs)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `SCALE-006` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

The Render `starter` plan sets the platform memory/CPU envelope, but there is no explicit file-descriptor / ulimit configuration and OOM/clean-crash + restart behaviour is untested.

### Expected Behavior

SCALE-006 expects explicit memory and CPU limits, requests < limits, an FD limit (>=4096) for many outbound connections, and tested OOM behaviour with an active restart policy.

### Evidence

- `render.yaml:8` — `plan: starter` (defines mem/CPU envelope)
- No `ulimit -n` / FD configuration in Dockerfile or render.yaml
- No explicit container-level memory limit beyond the plan; no OOM test

### Risk Description

Under connection bursts the process could hit the default FD ceiling; an untested OOM path could crash without a clean restart, causing avoidable downtime.

### Remediation

Add an explicit FD limit (e.g. `ulimit -n 4096` in an entrypoint or a K8s pod spec), document the memory/CPU request-vs-limit values, and add an OOM smoke test verifying clean crash + restart.

### Effort Estimate

S

### Dependencies / Blockers

None.

### Verification After Fix

Re-audit SCALE-006: FD limit configured, OOM behaviour tested, restart policy confirmed.

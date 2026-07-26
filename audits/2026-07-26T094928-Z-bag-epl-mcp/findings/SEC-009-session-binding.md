## Finding: SEC-009 — Session-ID Cryptographic Binding (user_id:session_id)

| Feld | Wert |
|---|---|
| **Severity** | critical |
| **Status** | accepted-risk |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `SEC-009` |
| **PDF-Reference** | Sec 4.6 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

Over Streamable HTTP the server is stateless and unauthenticated: it relies on the MCP SDK's default session manager and adds no cryptographic user_id:session_id binding, no OAuth-sub validation, and no server-side session invalidation.

### Expected Behavior

SEC-009 expects session IDs bound to a validated OAuth `sub`, high-entropy generation, explicit TTL, and server-side invalidation - but only when a user identity exists.

### Evidence

- `docs/SECURITY.md:41-56` — documents the stateless/unauthenticated model and the accepted-risk decision
- `SECURITY.md:52-56` — SEC-009 recorded as N/A (no auth) with a re-audit trigger
- `src/bag_epl_mcp/server.py` — no auth middleware, no session-binding code

### Risk Description

Currently low: there is no user identity to impersonate and no confidential per-user state to steal (public read-only open data). The risk only materialises if authentication or per-user state is added without re-introducing binding.

### Remediation

Keep as accepted-risk for the unauthenticated Phase-1 server. If auth/per-user state is ever introduced: generate session IDs with `secrets.token_urlsafe()`, bind to the validated `sub` claim (signed), set a TTL, invalidate server-side on logout, and re-audit before merge.

### Effort Estimate

L

### Dependencies / Blockers

Only relevant once an auth model (SEC-013/OAuth) is introduced.

### Verification After Fix

Re-audit SEC-009 after any auth introduction; verify signed binding + 401/403 on session/user mismatch.

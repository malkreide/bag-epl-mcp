## Finding: SEC-021 — Egress-Allow-List: Code-Layer und Network-Layer

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `SEC-021` |
| **PDF-Reference** | Anhang B5 + B12 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

The code-layer egress allow-list is strong (frozenset, pre-request check on every outbound GET), but there is no network-layer egress control (NetworkPolicy / security group / Cloudflare WARP) as defense-in-depth on Render, and no documented allow-list update procedure.

### Expected Behavior

SEC-021 expects both a code-layer frozenset allow-list AND a network-layer egress control, plus a documented update procedure and an explicitly allowed DNS path.

### Evidence

- `src/bag_epl_mcp/server.py:254-258` — code-layer `ALLOWED_HOSTS` frozenset (not config-mutable)
- `src/bag_epl_mcp/server.py:356` — `_assert_safe_url` called before every outbound GET
- `docs/SECURITY.md:57-78` — allow-list hosts documented, but no network-layer policy and no change procedure

### Risk Description

If the code-layer check is ever bypassed (dependency change, new code path), there is no independent network boundary to stop egress to an unintended host. Render does not provide an easy NetworkPolicy equivalent, so the second layer is genuinely absent.

### Remediation

Add a network-layer egress control where the platform allows it (K8s NetworkPolicy, security group, or a Cloudflare WARP/egress proxy such as Smokescreen), document the allow-list update procedure in `docs/network-egress.md`, and ensure the DNS resolution path is explicitly permitted.

### Effort Estimate

M

### Dependencies / Blockers

Depends on target platform capabilities (Render has limited egress controls).

### Verification After Fix

Re-audit SEC-021: confirm a network-layer egress control blocks a non-allow-listed host independent of the code check.

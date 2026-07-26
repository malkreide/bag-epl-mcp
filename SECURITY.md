# Security Policy & Posture

[:de: Deutsche Version](SECURITY.de.md)

`bag-epl-mcp` was hardened against the internal MCP best-practice audit
catalogue. This document summarises the security posture and records the
**accepted-risk** decisions for controls that are deliberately handled at the
portfolio/gateway layer rather than inside this single server. The full threat
model and per-control rationale live in
[`docs/SECURITY.md`](docs/SECURITY.md).

## Reporting a vulnerability

Please open a private report via
[GitHub Security Advisories](https://github.com/malkreide/bag-epl-mcp/security/advisories),
or contact the maintainer listed in `README.md`. Do not file public issues for
exploitable vulnerabilities, and do not include any sensitive data.

## Posture summary

This is a **read-only**, **no-PII**, **public-open-data** MCP server. All 6
tools only issue HTTPS `GET` requests against a fixed allow-list of Swiss
federal hosts (`sl.bag.admin.ch`, `www.bag.admin.ch`, `www.fedlex.admin.ch`).
Hardening already in place:

| Area | Control |
|---|---|
| Egress | HTTPS-enforced allow-list to `*.admin.ch` hosts only, with IP-block validation against SSRF (SEC-004/021) |
| TLS | DNS-pinned transport: hostname resolved once, IP pinned, TLS/cert verification against the original hostname (SEC-005) |
| Binding | Network transports default to `127.0.0.1`; `0.0.0.0` only inside a container (SEC-016) |
| Transport | stdio (default, no ports) + Streamable HTTP with a CORS allow-list (SDK-004) |
| Input | Pydantic v2 strict validation at all tool boundaries (SEC-018) |
| Secrets | Env-vars only, `.gitignore` guards `.env`, no hardcoded secrets (SEC-013) |
| Errors | Upstream bodies logged to stderr, never forwarded to the model (OBS-002) |
| Stdout | Reserved for the JSON-RPC stream; structured logging pinned to stderr (OBS-004) |
| Tool surface | 6 read-only tools, `epl_` namespaced, `readOnlyHint=true` (SEC-014) |
| Container | Multi-stage `Dockerfile` runs non-root (UID 10001) with a `HEALTHCHECK` (SEC-007) |

The most recent independent re-audit (run `2026-07-26T094928-Z-bag-epl-mcp`,
skill v1.0.0, catalog of 68 checks) reports **production-ready** (no blocking
critical/high failures): **29 pass · 11 partial · 0 fail** across 40 applicable
checks. The 11 partials are non-blocking accepted-risk / deferred items
(SEC-009, SEC-014/015, SCALE-002/003/006, SEC-021, SEC-022, OBS-006, OPS-002,
ARCH-011). The full scorecard, findings and report are in
[`audits/2026-07-26T094928-Z-bag-epl-mcp/`](audits/2026-07-26T094928-Z-bag-epl-mcp/);
the earlier `2026-06-01` re-audit remains in [`docs/audit/`](docs/audit/) and
the hardening history in `CHANGELOG.md`.

## Accepted risks (portfolio-level controls)

The following audit checks are **not** fully implemented inside this server by
design. They are portfolio-wide concerns best enforced at an MCP gateway / host
layer, and the residual risk here is low because the server is read-only and
only reaches a fixed set of trusted public-data providers. The detailed
rationale is recorded in [`docs/SECURITY.md`](docs/SECURITY.md).

### SEC-009 — Session crypto-binding → N/A (no auth)

There is no user identity to bind a session to: `bag-epl-mcp` exposes public
open data with no authentication and no per-user state. Binding a session to a
validated OAuth `sub` claim is only meaningful once authentication exists.

### SEC-014 / SEC-015 — Gateway tool allow-list & tool-poisoning detection

The tool surface is static, read-only, and authored in-repo (reviewed via PR);
there is no enterprise context and no dynamic/remote tool registration.
Cross-server allow-listing and pre-flight tool-poisoning detection remain a
gateway/host responsibility tracked at the portfolio level.

### SCALE-002 / SCALE-003 — Sticky sessions (multi-instance)

Phase 1 runs as a **single instance**, so `Mcp-Session-Id` sticky-session
routing is not required. A reference HAProxy stick-table config for the scaling
path is provided in [`deploy/haproxy.cfg`](deploy/haproxy.cfg).

## Re-evaluation triggers

These acceptances should be revisited if the server ever:

- gains **write** capability or starts processing **PII**, or
- adds an **authentication** model (then implement SEC-009: bound, TTL'd,
  server-side-invalidated session IDs and re-audit before merge), or
- registers tools **dynamically** / from remote sources, or
- is scaled **horizontally** (then enable sticky sessions per SCALE-002/003), or
- is aggregated behind a shared MCP gateway (then enable the gateway's tool
  allow-listing and tool-poisoning detection).

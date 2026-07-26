# MCP-Server Audit-Report — `bag-epl-mcp`

**Audit-Datum:** 
**Skill-Version:** 1.0.0
**Catalog-Version:** ?

---

## 1. Executive Summary

Server `bag-epl-mcp` wurde gegen 40 anwendbare Best-Practice-Checks geprüft. 29 bestanden, 11 Findings dokumentiert (1 critical, 4 high, 6 medium, 0 low). Production-Readiness: erreicht.

**Production-Readiness:** YES

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `bag-epl-mcp` |
| Audit-Datum | ? |
| Skill-Version | 1.0.0 |
| Catalog-Version | ? |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 10 | 0 | 1 | 0 | 0 |
| CH | 1 | 0 | 0 | 0 | 0 |
| OBS | 4 | 0 | 1 | 0 | 0 |
| OPS | 2 | 0 | 1 | 0 | 0 |
| SCALE | 2 | 0 | 3 | 0 | 0 |
| SEC | 10 | 0 | 5 | 0 | 0 |
| **Total** | **29** | **0** | **11** | **0** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| SEC-009 | SEC | critical | partial |
| SCALE-002 | SCALE | high | partial |
| SCALE-003 | SCALE | high | partial |
| SEC-021 | SEC | high | partial |
| SEC-022 | SEC | high | partial |
| ARCH-011 | ARCH | medium | partial |
| OBS-006 | OBS | medium | partial |
| OPS-002 | OPS | medium | partial |
| SCALE-006 | SCALE | medium | partial |
| SEC-014 | SEC | medium | partial |
| SEC-015 | SEC | medium | partial |

**Gesamt:** 11 Findings

---

## 5. Detail-Findings

### ARCH-011

## Finding: ARCH-011 — Standardisierte Repo-Struktur (src-Layout, tests, README.de.md)

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `ARCH-011` |
| **PDF-Reference** | Anhang A8 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

The repo satisfies almost the whole standard layout (src-layout, tests/, .github/workflows/, all mandatory top-level files), but all 6 tools plus resources, prompts, settings, HTTP client, envelopes and the HTTP app live in a single `src/bag_epl_mcp/server.py` of ~1010 lines.

### Expected Behavior

For servers with more than 5 tools, ARCH-011 Modus 4 expects a `tools/` package (one file per tool group) and a `server.py` reduced to registry + lifecycle (~200 lines).

### Evidence

- `src/bag_epl_mcp/server.py` — single file, ~1010 lines, holds all 6 tool bodies (lines 511-850), 2 resources (855-886), 2 prompts (891-915), settings, egress guard and HTTP app
- No `src/bag_epl_mcp/tools/` directory present
- `pyproject.toml:69` — correct src-layout otherwise

### Risk Description

Low direct risk. A 1010-line module raises code-review and test-isolation cost and makes portfolio-wide tooling assumptions (file-per-tool-group) inconsistent as the server grows into Phase 2/3.

### Remediation

Split tool bodies into `src/bag_epl_mcp/tools/{sl,ggsl,migel,rechtskontext,info}.py`, keep `server.py` as the FastMCP registry + lifespan. Move Pydantic schemas into `schemas/` and the egress guard into `clients/`.

### Effort Estimate

M

### Dependencies / Blockers

None.

### Verification After Fix

Re-audit ARCH-011 Modus 4: `ls src/bag_epl_mcp/tools/*.py` returns files and `wc -l src/bag_epl_mcp/server.py` < 200.


### OBS-006

## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bag-epl-mcp` |
| **Check-Reference** | `OBS-006` |
| **PDF-Reference** | Anhang B10 |
| **Audit-Datum** | 2026-07-26 |
| **Auditor** | MCP Audit Skill (claude, Opus 4.8) |

### Observed Behavior

OpenTelemetry is wired up (TracerProvider + OTLP exporter, Starlette + httpx auto-instrumentation) and on by default, but only produces request-level and outbound-httpx spans. There is no per-tool span carrying MCP-specific attributes.

### Expected Behavior

OBS-006 Modus 1 expects one span per tool call named after the tool, with attributes `mcp.tool.name`, `mcp.user.id`, and `mcp.tool.result.is_error`, so slow-tool and behaviour analysis are possible.

### Evidence

- `src/bag_epl_mcp/server.py:950-982` — `_init_otel` instruments the ASGI app and httpx client only; no `tracer.start_as_current_span('mcp.tool.<name>')`
- `src/bag_epl_mcp/server.py:966-975` — tracing sits behind the optional `[otel]` extra and is a silent no-op if not installed
- `pyproject.toml:44-49` — otel is an optional extra, not a base dependency

### Risk Description

Without per-tool spans, P99-latency attribution per tool and anomalous tool-sequence detection are not available; in a base install (no `[otel]` extra) there is no tracing at all.

### Remediation

Add a tracing decorator that wraps each `@mcp.tool` handler and opens `mcp.tool.<name>` spans with `mcp.tool.name` and `mcp.tool.result.is_error` (omit PII; use a `sub`/opaque id only if auth is ever added). Optionally promote the otel packages to base deps or document the extra as required for cloud.

### Effort Estimate

M

### Dependencies / Blockers

None.

### Verification After Fix

Re-audit OBS-006: a span per tool call is visible in the OTLP backend with the required attributes.


### OPS-002

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


### SCALE-002

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


### SCALE-003

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


### SCALE-006

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


### SEC-009

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


### SEC-014

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


### SEC-015

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


### SEC-021

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


### SEC-022

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


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **SEC-009** (critical, partial)
2. **SCALE-002** (high, partial)
3. **SCALE-003** (high, partial)
4. **SEC-021** (high, partial)
5. **SEC-022** (high, partial)
6. **ARCH-011** (medium, partial)
7. **OBS-006** (medium, partial)
8. **OPS-002** (medium, partial)
9. **SCALE-006** (medium, partial)
10. **SEC-014** (medium, partial)
11. **SEC-015** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| policy | `fail-or-partial` |


_Generated by tools/build_report.py — do not edit by hand._

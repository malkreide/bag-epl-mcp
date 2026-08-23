> \U0001f1e8\U0001f1ed **Part of the [Swiss Public Data MCP Portfolio](https://github.com/malkreide)**

# \U0001f48a bag-epl-mcp

![Version](https://img.shields.io/badge/version-1.0.3-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-Model%20Context%20Protocol-purple)](https://modelcontextprotocol.io/)
[![No Auth Required](https://img.shields.io/badge/auth-none%20required-brightgreen)](https://github.com/malkreide/bag-epl-mcp)
![CI](https://github.com/malkreide/bag-epl-mcp/actions/workflows/ci.yml/badge.svg)

> MCP Server for the Swiss BAG electronic benefits platform (ePL) — Spezialitaetenliste, GGSL, MiGeL

[\U0001f1e9\U0001f1ea Deutsche Version](README.de.md)

### Demo

![Demo: Claude using epl_sl_suche and epl_rechtskontext](docs/assets/demo.svg)

---

## Overview

`bag-epl-mcp` enables AI models to answer questions about mandatory health insurance coverage in Switzerland — in natural language, grounded in real data.

| List | Purpose | Legal basis |
|------|---------|-------------|
| **Spezialitaetenliste (SL)** | Compulsory-insurance medications | KVG Art. 52 |
| **GGSL** | Medications for congenital disorders (IV) | IVG Anhang |
| **MiGeL** | Medical devices & aids | KLV Art. 20 |

**Anchor query:** *"Is this medication covered by mandatory health insurance?"*
→ `epl_sl_suche`: Live lookup in the Spezialitaetenliste (SL)
→ [More use cases by audience →](EXAMPLES.md)

---

## Features

- \U0001f48a **6 tools, 2 resources, 2 prompts** for Swiss health insurance data
- \U0001f50d **`epl_sl_suche`** — search the Spezialitaetenliste for medications
- ⚖️ **`epl_rechtskontext`** — legal context with Fedlex links
- \U0001f513 **No API key required** — all data publicly accessible
- ☁️ **Dual transport** — stdio (Claude Desktop) + Streamable HTTP (cloud)
- \U0001f4da **Prompt templates** for insurance coverage checks and school health queries

---

## Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

---

## Installation

```bash
# Clone the repository
git clone https://github.com/malkreide/bag-epl-mcp.git
cd bag-epl-mcp

# Install
pip install -e .
# or with uv:
uv pip install -e .
```

Or with `uvx` (no permanent installation):

```bash
uvx bag-epl-mcp
```

---

## Quickstart

```bash
# stdio (for Claude Desktop) — default, opens no network ports
python -m bag_epl_mcp.server

# Streamable HTTP (cloud) — transport selected via env var
MCP_TRANSPORT=streamable-http MCP_HOST=0.0.0.0 MCP_PORT=8000 \
  pip install -e ".[http]" && python -m bag_epl_mcp.server
```

> **Transport & host are configured exclusively via environment variables**
> (`MCP_TRANSPORT`, `MCP_HOST`, `MCP_PORT`). The default is `stdio` bound to
> nothing; `MCP_HOST` defaults to `127.0.0.1` and should only be set to
> `0.0.0.0` inside a container/cloud environment.

Try it immediately in Claude Desktop:

> *"Is Methylphenidate (Ritalin) covered by mandatory health insurance?"*
> *"Which laws regulate admission to the Spezialitaetenliste?"*
> *"Is a wheelchair covered by mandatory insurance?"*

---

## Configuration

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "bag-epl": {
      "command": "python",
      "args": ["-m", "bag_epl_mcp.server"]
    }
  }
}
```

Or with `uvx`:

```json
{
  "mcpServers": {
    "bag-epl": {
      "command": "uvx",
      "args": ["bag-epl-mcp"]
    }
  }
}
```

### Cloud Deployment (Streamable HTTP for browser access)

**Render.com (recommended):**
1. Push/fork the repository to GitHub
2. On [render.com](https://render.com): New Web Service → connect GitHub repo
3. Build command: `pip install -e ".[http]"`
4. Set the following environment variables:
   - `MCP_TRANSPORT=streamable-http`
   - `MCP_HOST=0.0.0.0` (required so the container accepts external traffic)
   - `MCP_PORT=8000` (or Render's `$PORT`)
   - *(optional)* `MCP_CORS_ORIGINS='["https://claude.ai"]'` to extend the
     browser CORS allow-list
   - *(optional)* OpenTelemetry tracing is **on by default** but a no-op unless
     the tracing deps are installed — build with `pip install -e ".[http,otel]"`
     and point `OTEL_EXPORTER_OTLP_ENDPOINT` at your collector. Set
     `MCP_OTEL_ENABLED=0` to disable.
5. Start command: `python -m bag_epl_mcp.server`
6. In claude.ai under Settings → MCP Servers, add: `https://your-app.onrender.com/mcp`

> **Security note:** the server exposes only public, read-only data and uses no
> authentication. See [`docs/SECURITY.md`](docs/SECURITY.md) for the threat
> model (egress allow-list, host binding, Lethal-Trifecta assessment).

---

## Available Tools

| Tool | Description |
|------|-------------|
| `epl_sl_suche` | Search the Spezialitaetenliste for compulsory-insurance medications |
| `epl_ggsl_abfrage` | Check GGSL coverage for congenital disorders |
| `epl_migel_suche` | Search the MiGeL for medical devices & aids |
| `epl_gesuchseingaenge` | List pending SL admission requests (transparency) |
| `epl_rechtskontext` | Legal context for coverage questions (WZW criteria) |
| `epl_server_info` | Server status and API phase information |

### Example Use Cases

| Query | Tool |
|-------|------|
| *"Is Ritalin covered by insurance?"* | `epl_sl_suche` |
| *"Which medications for congenital disorder GG-313?"* | `epl_ggsl_abfrage` |
| *"Is a wheelchair covered?"* | `epl_migel_suche` |
| *"Which laws regulate the SL?"* | `epl_rechtskontext` |

---

## Architecture

**Data flow (Phase 1):**

```
                         bag-epl-mcp (FastMCP)
 ┌────────────┐   MCP   ┌───────────────────────────────┐   HTTPS GET  ┌──────────────────┐
 │ MCP Client │◀───────▶│  tools (read-only)            │─────────────▶│ sl.bag.admin.ch  │
 │ (Claude    │ stdio / │   ├─ epl_sl_suche             │  egress      │ www.bag.admin.ch │
 │  Desktop,  │ Stream- │   ├─ epl_ggsl_abfrage         │  allow-list  │ www.fedlex...    │
 │  claude.ai)│ able    │   ├─ epl_migel_suche          │◀─────────────│ (public OGD)     │
 │            │ HTTP    │   ├─ epl_gesuchseingaenge     │  (no auth)   └──────────────────┘
 │            │         │   ├─ epl_rechtskontext        │
 │            │         │   └─ epl_server_info          │   structured JSON logs → stderr
 └────────────┘         │  resources: epl://uebersicht …│
                        │  prompts:   epl_kassenpflicht…│
                        └───────────────────────────────┘
```

**Phase roadmap** (details in [`docs/ROADMAP.md`](docs/ROADMAP.md)):

```
Phase 1 (current)  → legal context + entry points, no data retrieval
Phase 2 (planned)  → FHIR/IDMP API, once publicly accessible
Phase 3 (vision)   → MiGeL + AL via ePL-FHIR
```

**What Phase 1 does, and what it does not.** Five of the six tools make no
network request at all — there is exactly one outgoing HTTP call in the whole
module. They return the legal basis and an entry point, and they now say so.
The previous wording, "XML/XLSX downloads + SL website access", advertised a
capability with no code path behind it; on 2026-08-08 it was removed rather
than implemented, because the underlying source is not machine-readable.

That one HTTP call goes to `sl.bag.admin.ch/api/search` and receives **HTTP 200
with `text/html`** — the 51 KB Angular shell. A freely invented path under the
same prefix returns the identical response, byte for byte: there is no API at
that address. Previously the resulting JSON parse error was caught by a bare
`except Exception` and turned into the claim "the SL database API is not
publicly documented" — a statement about the BAG's publishing practice,
derived from a parser error. The tool now reports what was measured.

The SL front end calls `https://epl.bag.admin.ch/api/sl/` instead, on a
different host. That host answers 401 without authentication — but it answers
401 for invented paths too, so this does **not** establish that any particular
route exists. It is deliberately **not** on the egress allow-list: without
verifiable access, adding it would be a grant on suspicion.

**MCP protocol version:** `2025-11-25` (surfaced via `epl_server_info`) — the
`initialize` handshake ceiling, derived from the SDK rather than written down
here a second time. See [MCP Protocol Version](#mcp-protocol-version) for both
eras. SDK
updates are proposed monthly via Dependabot; the protocol version is reviewed on
every `mcp` SDK bump — see the versioning policy in [`docs/ROADMAP.md`](docs/ROADMAP.md).

---

## Safety & Limits

- **Read-only:** All tools perform HTTP GET requests only — no data is written, modified, or deleted.
- **No personal data:** The server accesses public regulatory lists (SL, GGSL, MiGeL). No personally identifiable information (PII) is processed or stored.
- **No medical advice:** This server provides informational access to regulatory data only. For medical or legal decisions, always consult the official BAG sources and qualified professionals.
- **Rate limits:** The SL website (sl.bag.admin.ch) is a public Angular SPA; the server enforces a 30s timeout per request. Use `limit` parameters conservatively.
- **Data freshness:** Phase 1 tools link to live BAG sources. No caching is performed by this server.
- **Links are measured, not assumed:** the addresses handed out as "official source" are re-checked by `scripts/record_fixtures.py` on every run, together with a control request to an invented path. Two BAG pages previously handed out (`.../Arzneimittel/geburtsgebrechen-spezialitaetenliste.html` and `.../Arzneimittel/gesuchseingaenge.html`) answered HTTP 404 on 2026-08-08 and were replaced by the entry point that verifiably resolves — not by a guessed replacement URL.
- **Legal references are checked against the register:** every SR number the server prints is resolved to its ELI via the Fedlex SPARQL endpoint. This detour is necessary: Fedlex's web front end is a single-page app that answers HTTP 200 with the same byte count for *any* ELI, including an invented one. That is how a wrong GgV link (`eli/cc/1986/40_40_40`, no register entry) went unnoticed; the correct ELI is `eli/cc/1986/46_46_46`.
- **Data licence (OGD-CH):** The underlying BAG/Fedlex data is Swiss Open Government Data, licensed **CC BY 4.0**. Tool outputs carry a `source` / `provenance` block (JSON) or a source-and-licence footer (Markdown) so attribution is preserved.
- **Structured output:** every tool returns both a human-readable Markdown/JSON block (`content`) and a typed `structuredContent` validated against a per-tool output schema, so MCP clients can consume results programmatically without parsing prose.
- **Terms of service:** Data is subject to the ToS of [sl.bag.admin.ch](https://sl.bag.admin.ch), [bag.admin.ch](https://www.bag.admin.ch), and [fedlex.admin.ch](https://www.fedlex.admin.ch).
- **No guarantees:** This is a community project, not affiliated with the BAG or any government entity. Availability depends on upstream sources.

---

## MCP Protocol Version

This server speaks **two protocol eras** over the same endpoint. The client's
first request on a connection decides which one applies; a later claim from the
other era is refused.

| Era | Revision | Who reaches it |
|---|---|---|
| `initialize` handshake | `2024-11-05` … **`2025-11-25`** | What today's clients speak. The server answers with the revision asked for, or with the `2025-11-25` ceiling when the request asks for something newer. |
| Per-request envelope | **`2026-07-28`** | A request carrying the `2026-07-28` `_meta` envelope opens a modern connection. |

Both revisions are pinned in
[`tests/test_protocol_version.py`](tests/test_protocol_version.py) and asserted
against the installed SDK, so a Dependabot bump of `mcp` cannot move either one
silently. This server builds no ASGI app to send an `initialize` through, so
the gate asserts the SDK constants rather than a measured response — the
weaker form, named rather than left unsaid.

Note that the SDK's `LATEST_PROTOCOL_VERSION` is an alias for the **modern**
era, not for the handshake era — pinning against it alone would leave the era
that current clients actually negotiate free to drift.

**Update policy.** When the gate fails, do not edit the constant blindly: read
the spec changelog between the two revisions, verify the server still behaves,
then move the constant, this section, `README.de.md` and
[`CHANGELOG.md`](CHANGELOG.md) together.

---

## Testing

```bash
# Unit + contract tests (no network) — this is what CI runs
PYTHONPATH=src pytest tests/ -m "not live"

# Live tests against the real BAG/Fedlex sources
PYTHONPATH=src pytest tests/ -m "live"

# Re-record the measurements (writes tests/fixtures/ + PROVENANCE.md)
PYTHONPATH=src python scripts/record_fixtures.py
```

**100 tests** — 88 offline, 12 against the live sources.

### Why there is a contract test file as well as live tests

Until 2026-08-08 six of the eight live tests **could not pass**. They compared
a string against a tool's return value:

```python
assert "BAG ePL MCP Server" in result   # result is a CallToolResult
```

`CallToolResult` is a Pydantic model; `in` iterates over `(field, value)`
pairs, so the comparison is always false. Nobody noticed, because CI excludes
`-m live` — a test that only runs outside CI and is always red there reports to
no one.

And even fixed, four of them would have proved nothing: `assert "313" in
result` against a tool that writes its own input into a template, `assert
"Rollstuhl" in result` likewise. They asserted that a tool echoes its input —
which is precisely what those tools do.

What must hold permanently therefore lives in `tests/test_quellen_vertrag.py`,
which runs **inside** CI against the recorded measurements under
`tests/fixtures/`. `PROVENANCE.md` records source, date, selection rule and
SHA-256 for each one.

Four of the recorded measurements are **controls** — an invented path under
`sl.bag.admin.ch/api/`, an invented path in the BAG portal, an invented ELI,
and an invented SR number. Without them each measurement would only show what
*we* received, not what the source actually holds. The recorder aborts if a
control stops discriminating, if a live entry point dies, if one of the dead
pages returns, or if a legal reference drifts from the register.

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## Security

See [SECURITY.md](SECURITY.md) ([Deutsch](SECURITY.de.md)) for the security
posture and how to report a vulnerability.

---

## License

MIT License — see [LICENSE](LICENSE)

---

## Author

Hayal Oezkan · [malkreide](https://github.com/malkreide)

---

## Credits & Related Projects

- **BAG Spezialitaetenliste:** [sl.bag.admin.ch](https://sl.bag.admin.ch) — Federal Office of Public Health
- **KVG:** [SR 832.10](https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/de) — Health Insurance Act
- **KLV:** [SR 832.112.31](https://www.fedlex.admin.ch/eli/cc/1995/4964_4964_4964/de) — Healthcare Benefits Ordinance
- **Protocol:** [Model Context Protocol](https://modelcontextprotocol.io/) — Anthropic / Linux Foundation
- **Related:** [fedlex-mcp](https://github.com/malkreide/fedlex-mcp) — Swiss federal law
- **Related:** [swiss-cultural-heritage-mcp](https://github.com/malkreide/swiss-cultural-heritage-mcp) — Cultural heritage data
- **Portfolio:** [Swiss Public Data MCP Portfolio](https://github.com/malkreide)

<!-- mcp-name: io.github.malkreide/bag-epl-mcp -->

<!-- BEGIN GENERATED: install -->
## Installation

Run via [`uv`](https://docs.astral.sh/uv/)'s `uvx` — no clone or manual install needed. Add to your MCP client config (`mcpServers` for Claude Desktop, Cursor and Windsurf; use a top-level `servers` key for VS Code in `.vscode/mcp.json`):

```json
{
  "mcpServers": {
    "bag-epl-mcp": {
      "command": "uvx",
      "args": [
        "bag-epl-mcp"
      ]
    }
  }
}
```
<!-- END GENERATED: install -->

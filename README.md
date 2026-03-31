# bag-epl-mcp

[![CI](https://github.com/malkreide/bag-epl-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/malkreide/bag-epl-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/bag-epl-mcp)](https://pypi.org/project/bag-epl-mcp/)
[![Python](https://img.shields.io/pypi/pyversions/bag-epl-mcp)](https://pypi.org/project/bag-epl-mcp/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![swiss-public-data-mcp](https://img.shields.io/badge/portfolio-swiss--public--data--mcp-blue)](https://github.com/malkreide/swiss-public-data-mcp)

**MCP server for the Swiss Federal Office of Public Health (BAG) electronic benefits platform (ePL).**

Enables AI models to answer questions about mandatory health insurance coverage in Switzerland — in natural language, grounded in real data.

> **Anchor query:** *"Is this medication covered by mandatory health insurance?"*
> → `epl_sl_suche`: Live lookup in the Spezialitätenliste (SL)

---

## What is the ePL?

The **elektronische Plattform Leistungen (ePL)** is the BAG's new platform for three key lists of the Swiss healthcare system:

| List | Purpose | Legal basis |
|------|---------|-------------|
| **Spezialitätenliste (SL)** | Compulsory-insurance medications | KVG Art. 52 |
| **Geburtsgebrechen-Spezialitätenliste (GGSL)** | Medications for congenital disorders (IV) | IVG Anhang |
| **Mittel- und Gegenständeliste (MiGeL)** | Medical devices & aids | KLV Art. 20 |

## Tools

| Tool | Description |
|------|-------------|
| `epl_sl_suche` | Search the Spezialitätenliste for a medication |
| `epl_ggsl_abfrage` | Check GGSL coverage for congenital disorders |
| `epl_migel_suche` | Search the MiGeL for medical devices |
| `epl_gesuchseingaenge` | List pending SL admission requests (transparency) |
| `epl_rechtskontext` | Legal context for coverage questions (WZW criteria) |
| `epl_server_info` | Server status and API phase information |

## Architecture: Three-Phase Design

```
Phase 1 (current)  → XML/XLSX downloads + SL website access
Phase 2 (planned)  → FHIR/IDMP API (BAG, ~2025/2026)
Phase 3 (vision)   → MiGeL + AL via ePL-FHIR (2026/2027)
```

The server is **already useful today** and will seamlessly upgrade when the BAG publishes its FHIR API.

## Portfolio Synergies

| Combination | Value | Rating |
|-------------|-------|--------|
| `bag-epl-mcp` + `fedlex-mcp` | Legal context loop: statute → concrete list | ⭐⭐⭐ |
| `bag-epl-mcp` + `swiss-statistics-mcp` | Healthcare cost analysis | ⭐⭐ |
| `bag-epl-mcp` + `global-education-mcp` | OECD special needs benchmarking | ⭐ |

**The compliance loop** (strongest combination with `fedlex-mcp`):
1. *"Must this service be covered?"* → `epl_rechtskontext` → KVG/KLV norms
2. *"What does the law say?"* → `fedlex-mcp` → exact legal text
3. *"Is it actually on the list?"* → `epl_sl_suche` → live SL check

## Installation

```bash
pip install bag-epl-mcp
```

## Usage with Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "bag-epl-mcp": {
      "command": "uvx",
      "args": ["bag-epl-mcp"]
    }
  }
}
```

## Usage with Streamable HTTP (Cloud/Render.com)

```bash
MCP_TRANSPORT=streamable_http MCP_PORT=8000 bag-epl-mcp
```

## Example Queries

```
# School health service use case:
"Is Methylphenidate (Ritalin) covered by mandatory health insurance?"
→ epl_sl_suche: suchbegriff="Methylphenidat"

# Special needs education:
"Which medications are covered for children with congenital disorder GG-313 (diabetes)?"
→ epl_ggsl_abfrage: geburtsgebrechen_nr="313"

# Legal compliance:
"Which laws regulate admission to the Spezialitätenliste?"
→ epl_rechtskontext: frage="Welche Gesetze regeln die Aufnahme in die SL?"

# Medical devices for inclusive schools:
"Is a wheelchair covered by mandatory health insurance?"
→ epl_migel_suche: suchbegriff="Rollstuhl"
```

## Context: Schulamt der Stadt Zürich

This server is particularly relevant for the school system:

- **School health service**: Check if a pupil's medication is covered before advising families
- **Special needs support**: GGSL coverage for pupils with congenital disorders
- **Inclusive education**: MiGeL coverage for assistive devices
- **HR / Stadtentwicklung**: Benefits questions for city employees

## Known Limitations

- **Phase 1 limitation**: The ePL internal API is not publicly documented. The SL website (sl.bag.admin.ch) is an Angular SPA with a private backend. Direct medication search may return no results until the BAG publishes its FHIR API.
- **Fallback**: All tools provide direct links to sl.bag.admin.ch for manual searches.
- **MiGeL**: Not yet integrated in ePL (planned 2026/2027); MiGeL tools use category matching.

## Testing

```bash
# Unit tests (no live API calls):
PYTHONPATH=src pytest tests/ -m "not live" -v

# Live tests (requires network):
PYTHONPATH=src pytest tests/ -m "live" -v
```

## Legal Notices

Data sources:
- [Spezialitätenliste (SL)](https://sl.bag.admin.ch) — Bundesamt für Gesundheit (BAG)
- [KVG SR 832.10](https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/de)
- [KLV SR 832.112.31](https://www.fedlex.admin.ch/eli/cc/1995/4964_4964_4964/de)

This server provides informational access only. For medical or legal decisions, always consult the official BAG sources directly.

---

Part of the [swiss-public-data-mcp](https://github.com/malkreide/swiss-public-data-mcp) portfolio.

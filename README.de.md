# bag-epl-mcp

[![CI](https://github.com/malkreide/bag-epl-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/malkreide/bag-epl-mcp/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/bag-epl-mcp)](https://pypi.org/project/bag-epl-mcp/)
[![swiss-public-data-mcp](https://img.shields.io/badge/portfolio-swiss--public--data--mcp-blue)](https://github.com/malkreide/swiss-public-data-mcp)

**MCP-Server für die elektronische Plattform Leistungen (ePL) des Bundesamts für Gesundheit (BAG).**

Ermöglicht KI-Modellen, Fragen zur obligatorischen Krankenpflegeversicherung in natürlicher Sprache zu beantworten — verankert in echten Daten.

> **Anker-Abfrage:** *«Ist dieses Medikament kassenpflichtig?»*
> → `epl_sl_suche`: Direktabfrage in der Spezialitätenliste (SL)

---

## Was ist die ePL?

Die **elektronische Plattform Leistungen (ePL)** ist die neue Plattform des BAG für drei Schlüssellisten des Schweizer Gesundheitssystems:

| Liste | Zweck | Rechtsgrundlage |
|-------|-------|-----------------|
| **Spezialitätenliste (SL)** | Kassenpflichtige Medikamente | KVG Art. 52 |
| **Geburtsgebrechen-Spezialitätenliste (GGSL)** | Medikamente bei Geburtsgebrechen (IV) | IVG Anhang |
| **Mittel- und Gegenständeliste (MiGeL)** | Medizinprodukte und Hilfsmittel | KLV Art. 20 |

## Tools

| Tool | Beschreibung |
|------|-------------|
| `epl_sl_suche` | Kassenpflichtige Medikamente in der SL suchen |
| `epl_ggsl_abfrage` | GGSL-Deckung bei Geburtsgebrechen prüfen |
| `epl_migel_suche` | Medizinprodukte in der MiGeL suchen |
| `epl_gesuchseingaenge` | Transparenzliste SL-Neuaufnahmen abrufen |
| `epl_rechtskontext` | Rechtliche Grundlagen zur Kassenpflicht (WZW) |
| `epl_server_info` | Serverstatus und API-Phaseninfo |

## Architektur: Drei-Phasen-Design

```
Phase 1 (aktuell)  → XML/XLSX-Downloads + SL-Website-Zugriff
Phase 2 (geplant)  → FHIR/IDMP-API (BAG, ~2025/2026)
Phase 3 (Vision)   → MiGeL + AL via ePL-FHIR (2026/2027)
```

**Gleise bauen, bevor der Zug kommt:** Der Server ist heute nutzbar und upgradet nahtlos, sobald das BAG seine FHIR-API publiziert.

## Portfolio-Synergien

| Kombination | Mehrwert | Bewertung |
|-------------|---------|-----------|
| `bag-epl-mcp` + `fedlex-mcp` | Rechtskontext-Loop: Gesetz → konkrete Liste | ⭐⭐⭐ |
| `bag-epl-mcp` + `swiss-statistics-mcp` | Gesundheitskosten-Analyse | ⭐⭐ |
| `bag-epl-mcp` + `global-education-mcp` | OECD Sonderpädagogik-Benchmarking | ⭐ |

**Der Compliance-Loop** (stärkste Kombination mit `fedlex-mcp`):
1. *«Muss diese Leistung gedeckt sein?»* → `epl_rechtskontext` → KVG/KLV-Normen
2. *«Was sagt das Gesetz genau?»* → `fedlex-mcp` → Gesetzestext
3. *«Ist es tatsächlich auf der Liste?»* → `epl_sl_suche` → Live-SL-Prüfung

## Installation

```bash
pip install bag-epl-mcp
```

## Verwendung mit Claude Desktop

In `claude_desktop_config.json` eintragen:

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

## Beispielabfragen

```
# Schulgesundheitsdienst:
«Ist Methylphenidat (Ritalin) kassenpflichtig?»
→ epl_sl_suche: suchbegriff="Methylphenidat"

# Sonderpädagogik:
«Welche Medikamente sind bei GG-Nr. 313 (Diabetes) gedeckt?»
→ epl_ggsl_abfrage: geburtsgebrechen_nr="313"

# Rechtliche Compliance:
«Welche Gesetze regeln die Aufnahme in die Spezialitätenliste?»
→ epl_rechtskontext: frage="Welche Gesetze regeln die Aufnahme in die SL?"

# Inklusionsschule:
«Ist ein Rollstuhl über die Grundversicherung gedeckt?»
→ epl_migel_suche: suchbegriff="Rollstuhl"
```

## Bekannte Einschränkungen

- **Phase-1-Limitation**: Die interne ePL-API ist nicht öffentlich dokumentiert. Die SL-Website (sl.bag.admin.ch) ist eine Angular-SPA mit privatem Backend. Direkte Medikamentensuche kann leer zurückkehren, bis das BAG seine FHIR-API veröffentlicht.
- **Fallback**: Alle Tools liefern direkte Links zu sl.bag.admin.ch für manuelle Suchen.
- **MiGeL**: Noch nicht in ePL integriert (geplant 2026/2027).

---

Teil des [swiss-public-data-mcp](https://github.com/malkreide/swiss-public-data-mcp)-Portfolios.

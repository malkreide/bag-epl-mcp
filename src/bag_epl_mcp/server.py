#!/usr/bin/env python3
"""
BAG ePL MCP Server — v0.1.0

KI-nativer Zugang zur elektronischen Plattform Leistungen (ePL) des BAG:
  · Spezialitaetenliste (SL):   Kassenpflichtige Medikamente (KVG Art. 52)
  · GGSL:                       Medikamente bei Geburtsgebrechen (IVG)
  · MiGeL:                      Medizinprodukte und Hilfsmittel (KLV Art. 20)

Kein API-Schluessel erforderlich. Alle Daten oeffentlich zugaenglich.
"""

from __future__ import annotations

import asyncio
import json
from enum import StrEnum

import httpx
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, field_validator

# ─────────────────────────── Server ────────────────────────────────────────────
mcp = FastMCP("bag_epl_mcp")

# ─────────────────────────── Konstanten ────────────────────────────────────────
SL_BASE_URL       = "https://sl.bag.admin.ch"
SL_API_URL        = "https://sl.bag.admin.ch/api"
BAG_DOWNLOAD_URL  = "https://www.bag.admin.ch/bag/de/home/versicherungen/krankenversicherung/krankenversicherung-leistungen-tarife"
GGSL_INFO_URL     = "https://www.bag.admin.ch/bag/de/home/versicherungen/krankenversicherung/krankenversicherung-leistungen-tarife/Arzneimittel/geburtsgebrechen-spezialitaetenliste.html"
MIGEL_INFO_URL    = "https://www.bag.admin.ch/bag/de/home/versicherungen/krankenversicherung/krankenversicherung-leistungen-tarife/Mittel-und-Gegenstaendeliste.html"
HTTP_TIMEOUT      = 30.0
DEFAULT_LIMIT     = 20
MAX_LIMIT         = 100

# Phase 2: FHIR-API-Endpunkt (wird aktiviert, sobald BAG publiziert)
FHIR_BASE_URL = "https://epl.bag.admin.ch/fhir"  # Platzhalter

# ─────────────────────────── Enum ──────────────────────────────────────────────
class ResponseFormat(StrEnum):
    """Ausgabeformat fuer Tool-Antworten."""
    MARKDOWN = "markdown"
    JSON     = "json"


# ─────────────────────────── Hilfsfunktionen ───────────────────────────────────

async def _http_get(url: str, params: dict | None = None) -> httpx.Response:
    """Async HTTP GET mit Timeout."""
    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        return await client.get(url, params=params)


def _handle_error(error: Exception, context: str = "") -> str:
    """Einheitliche Fehlerbehandlung mit deutschen Meldungen."""
    prefix = f"Fehler bei {context}: " if context else "Fehler: "

    if isinstance(error, httpx.HTTPStatusError):
        status = error.response.status_code
        if status == 404:
            return f"{prefix}Ressource nicht gefunden (404)."
        if status == 429:
            return f"{prefix}Zu viele Anfragen — bitte spaeter erneut versuchen (429)."
        if status in (502, 503):
            return f"{prefix}Dienst voruebergehend nicht erreichbar ({status})."
        return f"{prefix}HTTP-Fehler {status}."
    if isinstance(error, httpx.TimeoutException):
        return f"{prefix}Zeitueberschreitung — der Server antwortet nicht innerhalb von {HTTP_TIMEOUT}s."
    if isinstance(error, httpx.ConnectError):
        return f"{prefix}Verbindung fehlgeschlagen — Server nicht erreichbar."
    return f"{prefix}{type(error).__name__}: {error}"


def _paginate(total: int, limit: int, offset: int) -> dict:
    """Standard-Paginierungshelfer."""
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "hat_mehr": offset + limit < total,
    }


# ─────────────────────────── SL-Website-Suche (Phase 1) ───────────────────────

async def _sl_website_suche(suchbegriff: str, limit: int = DEFAULT_LIMIT) -> dict:
    """
    Versucht, die SL-Website nach einem Medikament zu durchsuchen.
    Phase 1: Die interne API ist nicht dokumentiert — Fallback auf Info-Links.
    Phase 2: Wird durch FHIR-API-Aufrufe ersetzt.
    """
    try:
        resp = await _http_get(
            f"{SL_API_URL}/search",
            params={"query": suchbegriff, "limit": limit},
        )
        resp.raise_for_status()
        return resp.json()
    except Exception:
        # Phase 1 Fallback: API nicht oeffentlich zugaenglich
        return {
            "hinweis": (
                "Die SL-Datenbank-API ist derzeit nicht oeffentlich dokumentiert. "
                "Bitte verwenden Sie den direkten Link fuer eine manuelle Suche."
            ),
            "direkt_link": f"{SL_BASE_URL}/#/search/{suchbegriff}",
            "phase": "Phase 1 — Website-Zugriff",
            "fhir_status": "FHIR/IDMP-API noch nicht publiziert (erwartet ~2025/2026)",
        }


# ─────────────────────────── Input-Modelle ─────────────────────────────────────

class SLSucheInput(BaseModel):
    """Eingabe fuer die Medikamentensuche in der Spezialitaetenliste."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    suchbegriff: str = Field(
        ..., min_length=1, max_length=200,
        description="Name oder Wirkstoff des Medikaments (z.B. 'Methylphenidat', 'Aspirin')",
    )
    limit: int = Field(
        default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT,
        description="Maximale Anzahl Ergebnisse (1-100)",
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


class GGSLAbfrageInput(BaseModel):
    """Eingabe fuer GGSL-Abfrage bei Geburtsgebrechen."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    geburtsgebrechen_nr: str = Field(
        ..., min_length=1, max_length=10,
        description="Geburtsgebrechen-Nummer (z.B. '313' fuer Diabetes, '404' fuer Zystische Fibrose)",
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


class MiGeLSucheInput(BaseModel):
    """Eingabe fuer die MiGeL-Suche."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    suchbegriff: str = Field(
        ..., min_length=1, max_length=200,
        description="Suchbegriff fuer Medizinprodukte (z.B. 'Rollstuhl', 'Hoergeraet')",
    )
    limit: int = Field(
        default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT,
        description="Maximale Anzahl Ergebnisse (1-100)",
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )

    @field_validator("limit")
    @classmethod
    def clamp_limit(cls, v: int) -> int:
        return min(max(v, 1), MAX_LIMIT)


class RechtskontextInput(BaseModel):
    """Eingabe fuer rechtliche Kontext-Abfrage."""
    model_config = ConfigDict(str_strip_whitespace=True, validate_assignment=True, extra="forbid")

    frage: str = Field(
        ..., min_length=1, max_length=500,
        description="Rechtliche Frage zur Kassenpflicht (z.B. 'Welche Gesetze regeln die SL-Aufnahme?')",
    )
    format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Ausgabeformat: 'markdown' oder 'json'",
    )


# ─────────────────────────── Tools ─────────────────────────────────────────────

@mcp.tool()
async def epl_sl_suche(eingabe: SLSucheInput) -> str:
    """
    Suche in der Spezialitaetenliste (SL) nach kassenpflichtigen Medikamenten.

    Die SL enthaelt alle Arzneimittel, die von der obligatorischen
    Krankenpflegeversicherung (OKP) verguetet werden (KVG Art. 52).
    """
    try:
        ergebnis = await _sl_website_suche(eingabe.suchbegriff, eingabe.limit)

        if eingabe.format == ResponseFormat.JSON:
            return json.dumps(ergebnis, ensure_ascii=False, indent=2)

        # Markdown-Ausgabe
        md = f"## SL-Suche: \u00ab{eingabe.suchbegriff}\u00bb\n\n"

        if "hinweis" in ergebnis:
            md += f"> **Hinweis:** {ergebnis['hinweis']}\n\n"
            md += f"**Direkte Suche:** [{eingabe.suchbegriff} auf sl.bag.admin.ch]({ergebnis['direkt_link']})\n\n"
            md += f"**API-Status:** {ergebnis['fhir_status']}\n\n"
            md += "### Rechtsgrundlage\n"
            md += "- KVG Art. 52: Spezialitaetenliste\n"
            md += "- KLV Art. 30ff: Aufnahme-Kriterien (WZW: Wirksamkeit, Zweckmaessigkeit, Wirtschaftlichkeit)\n"
        else:
            md += f"Gefundene Medikamente: {len(ergebnis.get('results', []))}\n\n"
            for item in ergebnis.get("results", []):
                md += f"- **{item.get('name', 'Unbekannt')}**\n"

        return md

    except Exception as e:
        return _handle_error(e, "SL-Suche")


@mcp.tool()
async def epl_ggsl_abfrage(eingabe: GGSLAbfrageInput) -> str:
    """
    GGSL-Deckung bei Geburtsgebrechen pruefen.

    Die Geburtsgebrechen-Spezialitaetenliste (GGSL) enthaelt Arzneimittel,
    die bei anerkannten Geburtsgebrechen von der Invalidenversicherung (IV)
    uebernommen werden.
    """
    try:
        gg_nr = eingabe.geburtsgebrechen_nr

        info = {
            "geburtsgebrechen_nr": gg_nr,
            "status": "Phase 1 \u2014 Statische Information",
            "erklaerung": (
                f"Die GGSL listet Medikamente, die bei Geburtsgebrechen Nr. {gg_nr} "
                "von der IV uebernommen werden. Die vollstaendige Liste ist beim BAG einsehbar."
            ),
            "link": GGSL_INFO_URL,
            "rechtsgrundlage": "IVG Art. 13 / GgV (Geburtsgebrechen-Verordnung)",
            "hinweis": (
                "Fuer die aktuelle Medikamentenliste zu diesem Geburtsgebrechen "
                "konsultieren Sie bitte die offizielle BAG-Seite."
            ),
        }

        if eingabe.format == ResponseFormat.JSON:
            return json.dumps(info, ensure_ascii=False, indent=2)

        md = f"## GGSL-Abfrage: Geburtsgebrechen Nr. {gg_nr}\n\n"
        md += f"> {info['erklaerung']}\n\n"
        md += f"**Offizielle Quelle:** [BAG GGSL]({info['link']})\n\n"
        md += f"**Rechtsgrundlage:** {info['rechtsgrundlage']}\n\n"
        md += f"**Hinweis:** {info['hinweis']}\n"
        return md

    except Exception as e:
        return _handle_error(e, "GGSL-Abfrage")


@mcp.tool()
async def epl_migel_suche(eingabe: MiGeLSucheInput) -> str:
    """
    Suche in der Mittel- und Gegenstaendeliste (MiGeL) nach Medizinprodukten.

    Die MiGeL enthaelt alle von der OKP vergueteten Mittel und Gegenstaende
    (KLV Art. 20), z.B. Rollstuehle, Hoergeraete, Inkontinenzprodukte.
    """
    try:
        info = {
            "suchbegriff": eingabe.suchbegriff,
            "status": "Phase 1 \u2014 Kategorie-basierte Information",
            "erklaerung": (
                f"Die MiGeL-Suche nach \u00ab{eingabe.suchbegriff}\u00bb liefert Informationen "
                "zu vergueteten Medizinprodukten und Hilfsmitteln."
            ),
            "link": MIGEL_INFO_URL,
            "rechtsgrundlage": "KLV Art. 20 / MiGeL-Verordnung",
            "migel_integration": "MiGeL wird voraussichtlich 2026/2027 in die ePL integriert.",
        }

        if eingabe.format == ResponseFormat.JSON:
            return json.dumps(info, ensure_ascii=False, indent=2)

        md = f"## MiGeL-Suche: \u00ab{eingabe.suchbegriff}\u00bb\n\n"
        md += f"> {info['erklaerung']}\n\n"
        md += f"**Offizielle Quelle:** [BAG MiGeL]({info['link']})\n\n"
        md += f"**Rechtsgrundlage:** {info['rechtsgrundlage']}\n\n"
        md += f"**ePL-Integration:** {info['migel_integration']}\n"
        return md

    except Exception as e:
        return _handle_error(e, "MiGeL-Suche")


@mcp.tool()
async def epl_gesuchseingaenge() -> str:
    """
    Aktuelle Gesuchseingaenge fuer die Spezialitaetenliste abrufen.

    Transparenzliste: Zeigt, welche Medikamente aktuell zur Aufnahme
    in die SL beantragt sind.
    """
    try:
        info = {
            "beschreibung": (
                "Die Gesuchseingaenge zeigen, welche Arzneimittel aktuell zur Aufnahme "
                "in die Spezialitaetenliste beantragt wurden. Diese Transparenzliste wird "
                "periodisch vom BAG aktualisiert."
            ),
            "link": f"{SL_BASE_URL}/#/applications",
            "direkt_link_bag": f"{BAG_DOWNLOAD_URL}/Arzneimittel/gesuchseingaenge.html",
            "hinweis": (
                "Die vollstaendige Liste der Gesuchseingaenge ist auf sl.bag.admin.ch einsehbar. "
                "Die API-basierte Abfrage wird mit Phase 2 (FHIR) verfuegbar."
            ),
        }

        md = "## Gesuchseingaenge Spezialitaetenliste\n\n"
        md += f"> {info['beschreibung']}\n\n"
        md += f"**SL-Portal:** [Gesuchseingaenge ansehen]({info['link']})\n\n"
        md += f"**BAG-Seite:** [Offizielle BAG-Seite]({info['direkt_link_bag']})\n\n"
        md += f"**Hinweis:** {info['hinweis']}\n"
        return md

    except Exception as e:
        return _handle_error(e, "Gesuchseingaenge")


@mcp.tool()
async def epl_rechtskontext(eingabe: RechtskontextInput) -> str:
    """
    Rechtlichen Kontext zur Kassenpflicht liefern.

    Gibt strukturierte Informationen zu den Rechtsgrundlagen der
    obligatorischen Krankenpflegeversicherung (WZW-Kriterien, KVG, KLV).
    """
    try:
        rechtsrahmen = {
            "frage": eingabe.frage,
            "gesetze": [
                {
                    "kuerzel": "KVG",
                    "titel": "Bundesgesetz ueber die Krankenversicherung",
                    "sr_nummer": "SR 832.10",
                    "fedlex": "https://www.fedlex.admin.ch/eli/cc/1995/1328_1328_1328/de",
                    "relevante_artikel": ["Art. 25 (Leistungen)", "Art. 32 (WZW)", "Art. 52 (SL)"],
                },
                {
                    "kuerzel": "KLV",
                    "titel": "Krankenpflege-Leistungsverordnung",
                    "sr_nummer": "SR 832.112.31",
                    "fedlex": "https://www.fedlex.admin.ch/eli/cc/1995/4964_4964_4964/de",
                    "relevante_artikel": ["Art. 20 (MiGeL)", "Art. 30ff (SL-Aufnahme)"],
                },
                {
                    "kuerzel": "IVG",
                    "titel": "Bundesgesetz ueber die Invalidenversicherung",
                    "sr_nummer": "SR 831.20",
                    "fedlex": "https://www.fedlex.admin.ch/eli/cc/1959/827_857_845/de",
                    "relevante_artikel": ["Art. 13 (Geburtsgebrechen)"],
                },
                {
                    "kuerzel": "GgV",
                    "titel": "Verordnung ueber Geburtsgebrechen",
                    "sr_nummer": "SR 831.232.21",
                    "fedlex": "https://www.fedlex.admin.ch/eli/cc/1986/40_40_40/de",
                    "relevante_artikel": ["Anhang (Liste der Geburtsgebrechen)"],
                },
            ],
            "wzw_kriterien": {
                "wirksamkeit": "Das Arzneimittel muss wirksam sein (klinische Studien).",
                "zweckmaessigkeit": "Der Einsatz muss zweckmaessig sein (Nutzen-Risiko).",
                "wirtschaftlichkeit": "Die Kosten muessen in einem angemessenen Verhaeltnis stehen.",
            },
            "hinweis": "Fuer verbindliche Rechtsauskunft konsultieren Sie die offiziellen Fedlex-Quellen.",
        }

        if eingabe.format == ResponseFormat.JSON:
            return json.dumps(rechtsrahmen, ensure_ascii=False, indent=2)

        md = f"## Rechtskontext: {eingabe.frage}\n\n"
        md += "### Relevante Gesetze\n\n"
        for g in rechtsrahmen["gesetze"]:
            md += f"#### {g['kuerzel']} \u2014 {g['titel']}\n"
            md += f"- **SR-Nummer:** {g['sr_nummer']}\n"
            md += f"- **Fedlex:** [{g['kuerzel']} auf Fedlex]({g['fedlex']})\n"
            md += f"- **Relevante Artikel:** {', '.join(g['relevante_artikel'])}\n\n"

        md += "### WZW-Kriterien (KVG Art. 32)\n\n"
        for k, v in rechtsrahmen["wzw_kriterien"].items():
            md += f"- **{k.capitalize()}:** {v}\n"

        md += f"\n> **Hinweis:** {rechtsrahmen['hinweis']}\n"
        return md

    except Exception as e:
        return _handle_error(e, "Rechtskontext")


@mcp.tool()
async def epl_server_info() -> str:
    """
    Serverstatus und API-Phaseninformation anzeigen.

    Liefert Informationen zum aktuellen Funktionsumfang und den geplanten
    Erweiterungen des BAG-ePL-MCP-Servers.
    """
    info = {
        "server": "bag-epl-mcp",
        "version": "0.1.0",
        "phase": "Phase 1 \u2014 XML/XLSX-Downloads + SL-Website-Zugriff",
        "tools": {
            "epl_sl_suche": "Medikamentensuche in der Spezialitaetenliste (SL)",
            "epl_ggsl_abfrage": "GGSL-Deckung bei Geburtsgebrechen pruefen",
            "epl_migel_suche": "Medizinprodukte in der MiGeL suchen",
            "epl_gesuchseingaenge": "SL-Gesuchseingaenge (Transparenz)",
            "epl_rechtskontext": "Rechtliche Grundlagen zur Kassenpflicht",
            "epl_server_info": "Serverstatus (dieses Tool)",
        },
        "phasen": {
            "phase_1": "XML/XLSX-Downloads + SL-Website (aktuell)",
            "phase_2": "FHIR/IDMP-API des BAG (~2025/2026)",
            "phase_3": "MiGeL + AL via ePL-FHIR (2026/2027)",
        },
        "datenquellen": {
            "sl": f"{SL_BASE_URL} \u2014 Spezialitaetenliste",
            "ggsl": GGSL_INFO_URL,
            "migel": MIGEL_INFO_URL,
        },
    }

    md = "## BAG ePL MCP Server \u2014 Status\n\n"
    md += f"**Version:** {info['version']}\n\n"
    md += f"**Aktuelle Phase:** {info['phase']}\n\n"
    md += "### Verfuegbare Tools\n\n"
    for tool, desc in info["tools"].items():
        md += f"| `{tool}` | {desc} |\n"
    md += "\n### Phasenplan\n\n"
    for phase, desc in info["phasen"].items():
        md += f"- **{phase}:** {desc}\n"
    return md


# ─────────────────────────── Resources ─────────────────────────────────────────

@mcp.resource("epl://uebersicht")
def epl_uebersicht() -> str:
    """Uebersicht ueber die ePL-Datenquellen und den aktuellen Funktionsumfang."""
    return (
        "# BAG ePL \u2014 Uebersicht\n\n"
        "Die elektronische Plattform Leistungen (ePL) des BAG umfasst drei Listen:\n\n"
        "1. **Spezialitaetenliste (SL)** \u2014 Kassenpflichtige Medikamente (KVG Art. 52)\n"
        "2. **GGSL** \u2014 Medikamente bei Geburtsgebrechen (IVG)\n"
        "3. **MiGeL** \u2014 Medizinprodukte und Hilfsmittel (KLV Art. 20)\n\n"
        "## Aktueller Stand\n"
        "- Phase 1: SL-Website-Zugriff + strukturierte Rechtsinfo\n"
        "- Phase 2 (geplant): FHIR/IDMP-API\n"
        "- Phase 3 (Vision): Volle ePL-Integration\n"
    )


@mcp.resource("epl://rechtsrahmen")
def epl_rechtsrahmen() -> str:
    """Rechtsrahmen der obligatorischen Krankenpflegeversicherung."""
    return (
        "# Rechtsrahmen OKP\n\n"
        "| Gesetz | SR-Nummer | Thema |\n"
        "|--------|-----------|-------|\n"
        "| KVG | SR 832.10 | Krankenversicherungsgesetz |\n"
        "| KLV | SR 832.112.31 | Leistungsverordnung |\n"
        "| IVG | SR 831.20 | Invalidenversicherung |\n"
        "| GgV | SR 831.232.21 | Geburtsgebrechen |\n\n"
        "## WZW-Kriterien (KVG Art. 32)\n"
        "- **Wirksamkeit** \u2014 klinisch belegt\n"
        "- **Zweckmaessigkeit** \u2014 angemessenes Nutzen-Risiko-Verhaeltnis\n"
        "- **Wirtschaftlichkeit** \u2014 Kosten im Verhaeltnis zum Nutzen\n"
    )


# ─────────────────────────── Prompts ───────────────────────────────────────────

@mcp.prompt()
def epl_kassenpflicht_check(medikament: str) -> str:
    """Strukturierter Workflow: Ist ein Medikament kassenpflichtig?"""
    return (
        f"Pruefe, ob \u00ab{medikament}\u00bb von der obligatorischen Krankenpflegeversicherung "
        "verguetet wird. Gehe dabei wie folgt vor:\n\n"
        f"1. Suche \u00ab{medikament}\u00bb in der Spezialitaetenliste (epl_sl_suche)\n"
        "2. Pruefe die Rechtsgrundlage (epl_rechtskontext)\n"
        "3. Falls fuer Geburtsgebrechen relevant: GGSL pruefen (epl_ggsl_abfrage)\n"
        "4. Falls Medizinprodukt: MiGeL pruefen (epl_migel_suche)\n"
        "5. Fasse die Ergebnisse zusammen mit Quellenangaben\n"
    )


@mcp.prompt()
def epl_schulgesundheit_recherche(thema: str) -> str:
    """Recherche-Workflow fuer Schulgesundheitsdienst-Anfragen."""
    return (
        f"Recherchiere zum Thema \u00ab{thema}\u00bb im Kontext des Schulgesundheitsdienstes:\n\n"
        "1. Pruefe Medikamenten-Kassenpflicht (epl_sl_suche)\n"
        "2. Klaere rechtliche Grundlagen (epl_rechtskontext)\n"
        "3. Bei Hilfsmitteln: MiGeL-Abdeckung pruefen (epl_migel_suche)\n"
        "4. Bei Geburtsgebrechen: IV-Deckung klaeren (epl_ggsl_abfrage)\n"
        "5. Gib eine strukturierte Zusammenfassung fuer Schulleitung/Eltern\n"
    )


# ─────────────────────────── Einstiegspunkt ────────────────────────────────────

if __name__ == "__main__":
    mcp.run()

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-13

### Added
- Initial release with Phase 1 implementation (no authentication required)
- **SL module**: `epl_sl_suche` — search the Spezialitaetenliste
- **GGSL module**: `epl_ggsl_abfrage` — check congenital disorder coverage
- **MiGeL module**: `epl_migel_suche` — search medical devices
- **Transparency**: `epl_gesuchseingaenge` — pending SL admission requests
- **Legal context**: `epl_rechtskontext` — WZW criteria, KVG/KLV/IVG references
- **Server info**: `epl_server_info` — status and phase information
- 2 Resources: `epl://uebersicht`, `epl://rechtsrahmen`
- 2 Prompts: `epl_kassenpflicht_check`, `epl_schulgesundheit_recherche`
- Dual transport: stdio (Claude Desktop) + Streamable HTTP (cloud/Render.com)
- GitHub Actions CI (Python 3.11, 3.12, 3.13)
- Bilingual documentation (DE/EN)
- Unit and integration tests (mocked HTTP via respx)

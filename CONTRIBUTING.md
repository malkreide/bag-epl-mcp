# Contributing to bag-epl-mcp

Thank you for your interest in contributing! This server is part of the [swiss-public-data-mcp](https://github.com/malkreide/swiss-public-data-mcp) portfolio.

## Development Setup

```bash
git clone https://github.com/malkreide/bag-epl-mcp
cd bag-epl-mcp
pip install -e ".[dev]"
```

## Running Tests

```bash
# Unit tests only (no network):
PYTHONPATH=src pytest tests/ -m "not live" -v

# All tests including live API calls:
PYTHONPATH=src pytest tests/ -v
```

## Code Style

This project uses [ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
python -m ruff check src/ tests/
python -m ruff format src/ tests/
```

## Phase 2: FHIR API

When the BAG publishes its FHIR/IDMP API for the ePL, contributions updating the tools to use it are very welcome. The architecture is designed to make this upgrade minimal — see the `FHIR_BASE_URL` constant and the `_sl_website_suche` function in `server.py`.

## Reporting Issues

- Bug reports: [GitHub Issues](https://github.com/malkreide/bag-epl-mcp/issues)
- API changes: Open an issue if the BAG ePL API structure changes

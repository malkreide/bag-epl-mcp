"""Zugriff auf die aufgezeichneten Messungen unter ``tests/fixtures/``.

Quelle, Datum, Auswahlregel und SHA-256 je Datei stehen in
``tests/fixtures/PROVENANCE.md``, geschrieben von
``scripts/record_fixtures.py``.

Ein fehlender Name ist hier ein Fehler und keine leere Struktur. Ein Loader,
der bei einem Tippfehler ``{}`` zurueckgibt, erzeugt einen Test, der nichts
mehr prueft und trotzdem Erfolg meldet — die teuerste Sorte gruen.
"""

from __future__ import annotations

import copy
import json
from functools import cache
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).resolve().parent / "fixtures"


@cache
def _load(name: str) -> Any:
    path = FIXTURES / name
    if not path.is_file():
        available = sorted(p.name for p in FIXTURES.glob("*.json"))
        raise FileNotFoundError(
            f"Keine Fixture {name!r} unter {FIXTURES}. Vorhanden: {available}. "
            "Neu aufzeichnen mit `python scripts/record_fixtures.py`."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def payload(name: str) -> Any:
    """Die aufgezeichnete Messung fuer ``name`` — als Kopie."""
    return copy.deepcopy(_load(name))


def adresse(label: str) -> dict[str, Any]:
    """Eine aufgezeichnete Adressmessung: Status, Content-Type, Groesse.

    Ein unbekanntes Label ist ein Fehler. Ein Test, der still auf ``{}``
    faellt, prueft danach nichts mehr und meldet trotzdem Erfolg.
    """
    adressen = _load("quellen_adressen.json")["adressen"]
    if label not in adressen:
        raise KeyError(f"Keine Messung fuer {label!r}. Vorhanden: {sorted(adressen)}.")
    return copy.deepcopy(adressen[label])

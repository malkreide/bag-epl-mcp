"""Prueft, dass das aufgerufene ruff die in pyproject.toml gepinnte Version ist.

Der Sinn eines lokalen Gates ist, dass es dasselbe Ergebnis liefert wie die CI.
Ein anderes ruff meldet Abweichungen, die niemand verursacht hat, und
verschweigt umgekehrt welche, die die CI dann rot machen.

Der Pin steht an genau einer Stelle und wird beim Install auch gezogen. Er
wirkt trotzdem nicht, wenn frueher im PATH ein anderes ruff liegt: `ruff`
nimmt dann jenes Binary, und der Install meldet dazu nichts. Dieses Skript
ist der Ausgleich - es vergleicht, was `ruff --version` sagt, mit dem, was
pyproject.toml verlangt.

Verwendung:
    python scripts/check_ruff_pin.py     # exit 1 bei Abweichung

Zwei Einschraenkungen, die diese Datei zwischen den Repos kopierbar halten:

  - Nur Standardbibliothek, und kein tomllib: fuenf Server im Portfolio
    fahren ihre CI auch auf Python 3.10, wo es tomllib nicht gibt. Fuer ein
    Feld lohnt weder eine Abhaengigkeit noch ein Versions-Zweig.
  - Keine Zeile ueber 88 Zeichen und keine impliziten String-Verkettungen
    ueber mehrere Zeilen; lange Meldungen bekommen eine lokale Variable. Im
    Portfolio stehen line-length 88, 100, 110 und 120 nebeneinander, und
    `ruff format` zieht einen Ausdruck zusammen, sobald er in die jeweilige
    Breite passt. Eine Verkettung, die bei 88 auf zwei Zeilen gehoert, waere
    bei 100 eine Zeile - und `ruff format --check` fiele beim Kopieren um.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYPROJECT = ROOT / "pyproject.toml"

# `"ruff==0.16.1"` als Eintrag einer Dependency-Liste. Bewusst eng: eine
# Spanne (`ruff>=…`) soll nicht als Pin durchgehen.
_PIN = re.compile(r"""['"]ruff==([0-9][^'"\s;]*)['"]""")

# Aus `ruff 0.16.1` bzw. `ruff 0.16.1 (abc1234 2026-01-01)`.
_REPORTED = re.compile(r"([0-9]+\.[0-9]+\.[0-9]+)")

_INSTALL = '    pip install -e ".[dev]"'


def pinned_version() -> str:
    """Die exakt gepinnte Version aus pyproject.toml. Einzige Quelle."""
    text = PYPROJECT.read_text(encoding="utf-8")
    found = sorted(set(_PIN.findall(text)))
    if not found:
        kein = "Kein exakter ruff-Pin (ruff==X.Y.Z) in pyproject.toml."
        grund = "Ohne ihn kann kein lokaler Lauf die CI reproduzieren."
        raise SystemExit(f"{kein} {grund}")
    if len(found) > 1:
        others = ", ".join(repr(v) for v in found)
        grund = "Genau einer muss es sein, sonst ist unklar, welcher gilt."
        raise SystemExit(f"Mehrere ruff-Pins in pyproject.toml: {others}. {grund}")
    return found[0]


def installed_version() -> str:
    """Die Version, die ein Aufruf von `ruff` tatsaechlich liefert."""
    binary = shutil.which("ruff")
    if binary is None:
        fehlt = "ruff ist nicht im PATH. Dev-Umgebung installieren:"
        raise SystemExit(f"{fehlt}\n{_INSTALL}")
    call = [binary, "--version"]
    out = subprocess.run(call, capture_output=True, text=True, check=True).stdout
    match = _REPORTED.search(out)
    if match is None:
        raise SystemExit(f"Version aus 'ruff --version' nicht lesbar: {out!r}")
    return match.group(1)


def main() -> int:
    want = pinned_version()
    have = installed_version()
    if want == have:
        print(f"Ruff-Pin OK ({want}; geprueft: PATH gegen pyproject.toml)")
        return 0
    kopf = f"ruff-Version weicht ab: aufgerufen wird {have}, gepinnt ist {want}."
    wo = f"Verwendet wird {shutil.which('ruff')}."
    folge = "Die Gates fallen damit lokal anders aus als in der CI."
    print(f"{kopf}\n{wo} {folge} Angleichen mit:\n{_INSTALL}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

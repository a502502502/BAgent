"""Rigenera portal/schedine.html dalle schedine registrate.

Il portale sul Pi la serve insieme a index.html. Il ciclo del portale
la riscrive da solo; questo script serve per aggiornarla subito.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.portal.slip_archive import write_slip_archive


def main() -> None:
    path = write_slip_archive()
    print(f"Archivio scritto in {path}")


if __name__ == "__main__":
    main()

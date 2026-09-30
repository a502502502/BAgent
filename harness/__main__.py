"""python -m harness [percorso/settled.json]

Stampa Brier, ECE, bankroll finale e drawdown massimo di una lista di esiti già chiusi.
"""

from __future__ import annotations

import sys
from pathlib import Path

from harness.calibration import load_settled, report_settled


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    payload = load_settled(Path(args[0]) if args else None)
    calibration, curve = report_settled(payload)
    print(f"n={calibration.n}")
    print(f"brier={calibration.brier:.4f}")
    print(f"ece={calibration.ece:.4f}")
    print(f"bankroll={curve.start:.2f}->{curve.end:.2f}")
    print(f"max_drawdown={curve.max_drawdown:.2%}")
    for item in calibration.bins:
        print(
            f"bin {item.lower:.2f}-{item.upper:.2f} "
            f"n={item.count} predetta={item.mean_predicted:.3f} "
            f"osservata={item.observed_frequency:.3f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

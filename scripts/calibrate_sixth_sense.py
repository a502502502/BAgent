"""Carica i risultati del campionato e ricalibra dopo la 3ª partita di ciascuna squadra.

Lo storico è quello già scaricato in matches. Le prime 3 gare per squadra
non entrano. I prior restano finché, su quel recinto, non ci sono abbastanza
partite confrontabili.

    python scripts/calibrate_sixth_sense.py --season 2026-27
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.football.sixth_sense.calibration import calibrate_season


def main() -> None:
    parser = argparse.ArgumentParser(description="Calibra i fattori del sesto senso sulla stagione in corso.")
    parser.add_argument("--season", required=True, help="Chiave stagione, es. 2026-27")
    parser.add_argument("--db", default="", help="Percorso di bagent.db. Default: data/bagent.db")
    args = parser.parse_args()
    db_path = args.db or None
    run = calibrate_season(args.season, db_path)
    print(
        f"Stagione {args.season}: {run.loaded} partite caricate dalla fonte, "
        f"{run.eligible} utilizzabili dopo la 3ª di entrambe le squadre."
    )
    for fit in run.fits:
        state = "in uso" if fit.used else "prior conservato"
        print(
            f"  {fit.name}: prior {fit.prior:.3f} → stimato {fit.fitted:.3f} "
            f"(trattate {fit.n_treated}, controllo {fit.n_control}, "
            f"peso interno {fit.internal_weight:.0%}) [{state}]"
        )


if __name__ == "__main__":
    main()

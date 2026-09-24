"""Classifica le combo gol contro quote vere, dopo il sesto senso.

Senza una quota il mercato resta fuori: non viene inventato un edge.

Esempio:
  python scripts/scan_combo_edge.py --xg-home 1.7 --xg-away 1.05 --corto-muso-home \
    --odds "1X + Under 3.5=1.55,Chance Mix: 1X o Over 1.5=1.28,1X + Over 1.5=1.70"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.combo_book_search import search_combo_edge
from services.football.sixth_sense.lambda_context import MatchContext


def main() -> None:
    parser = argparse.ArgumentParser(description="Combo gol contro il banco, con sesto senso.")
    parser.add_argument("--xg-home", type=float, required=True)
    parser.add_argument("--xg-away", type=float, required=True)
    parser.add_argument("--odds", default="", help="Mercato=quota, separati da virgola")
    parser.add_argument("--min-edge", type=float, default=0.04)
    parser.add_argument("--slow-start", action="store_true")
    parser.add_argument("--rotation", action="store_true")
    parser.add_argument("--corto-muso-home", action="store_true")
    parser.add_argument("--corto-muso-away", action="store_true")
    parser.add_argument("--low-motivation-home", action="store_true")
    parser.add_argument("--low-motivation-away", action="store_true")
    args = parser.parse_args()

    result = search_combo_edge(
        args.xg_home,
        args.xg_away,
        _parse_odds(args.odds),
        MatchContext(
            slow_start=args.slow_start,
            rotation_risk=args.rotation,
            low_motivation_home=args.low_motivation_home,
            low_motivation_away=args.low_motivation_away,
            corto_muso_home=args.corto_muso_home,
            corto_muso_away=args.corto_muso_away,
        ),
        min_edge=args.min_edge,
    )
    print(f"xG usati: casa {result.xg_home:.2f} | ospite {result.xg_away:.2f}")
    for note in result.notes:
        print(f"sesto senso: {note}")
    if not result.ranked:
        print("Nessuna combo batte il banco alla soglia di edge. Le quote assenti non generano valore.")
    for index, combo in enumerate(result.ranked, start=1):
        print(
            f"{index}. {combo.market}  P {combo.probability:.1%}  "
            f"fair {combo.fair_odd:.2f}  banco {combo.book_odd:.2f}  edge {combo.edge:+.1%}"
        )


def _parse_odds(raw: str) -> dict[str, float]:
    odds: dict[str, float] = {}
    for piece in raw.split(","):
        if "=" not in piece:
            continue
        market, price = piece.split("=", 1)
        market = market.strip()
        if market:
            odds[market] = float(price)
    return odds


if __name__ == "__main__":
    main()

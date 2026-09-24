"""Classifica le combo gol contro quote vere, dopo il sesto senso.

Senza una quota il mercato resta fuori: non viene inventato un edge.
`--gems-only` tiene solo lo sweet spot: P di matrice >= 70%, edge >= +4.5%,
quota tra 1.35 e 1.80, e nessun veto tattico.

Esempio:
  python scripts/scan_combo_edge.py --xg-home 1.7 --xg-away 1.05 --corto-muso-home \
    --odds "1X + Under 3.5=1.55,Chance Mix: 1X o Over 1.5=1.28,1X + Over 1.5=1.70"
  python scripts/scan_combo_edge.py --gems-only --xg-home 1.5 --xg-away 1.2 \
    --corners-home 6 --corners-away 3 \
    --odds "Over 1.5=1.55,Over 4.5 Corner Casa=1.50"
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.combo_book_search import (
    ComboSearch,
    HiddenMarketFilter,
    find_hidden_gems,
    search_combo_edge,
)
from services.football.sixth_sense.lambda_context import MatchContext


def main() -> None:
    parser = argparse.ArgumentParser(description="Combo gol contro il banco, con sesto senso.")
    parser.add_argument("--xg-home", type=float, required=True)
    parser.add_argument("--xg-away", type=float, required=True)
    parser.add_argument("--odds", default="", help="Mercato=quota, separati da virgola")
    parser.add_argument("--min-edge", type=float, default=None)
    parser.add_argument("--gems-only", action="store_true", help="Solo pepite nello sweet spot 1.35-1.80")
    parser.add_argument("--corners-home", type=float, default=None)
    parser.add_argument("--corners-away", type=float, default=None)
    parser.add_argument("--referee-cards", type=float, default=None)
    parser.add_argument("--referee-style", default=None)
    parser.add_argument("--first-leg-home", type=int, default=None)
    parser.add_argument("--first-leg-away", type=int, default=None)
    parser.add_argument("--slow-start", action="store_true")
    parser.add_argument("--rotation", action="store_true")
    parser.add_argument("--corto-muso-home", action="store_true")
    parser.add_argument("--corto-muso-away", action="store_true")
    parser.add_argument("--low-motivation-home", action="store_true")
    parser.add_argument("--low-motivation-away", action="store_true")
    args = parser.parse_args()

    context = MatchContext(
        slow_start=args.slow_start,
        rotation_risk=args.rotation,
        low_motivation_home=args.low_motivation_home,
        low_motivation_away=args.low_motivation_away,
        corto_muso_home=args.corto_muso_home,
        corto_muso_away=args.corto_muso_away,
        referee_cards_per_game=args.referee_cards,
        referee_style=args.referee_style,
        first_leg_home=args.first_leg_home,
        first_leg_away=args.first_leg_away,
    )
    odds = _parse_odds(args.odds)
    if args.gems_only:
        sweet = HiddenMarketFilter()
        if args.min_edge is not None:
            sweet = replace(sweet, min_edge=args.min_edge)
        result = find_hidden_gems(
            args.xg_home,
            args.xg_away,
            odds,
            context,
            sweet,
            corners_home=args.corners_home,
            corners_away=args.corners_away,
        )
        _print_gems(result)
        return

    result = search_combo_edge(
        args.xg_home,
        args.xg_away,
        odds,
        context,
        min_edge=0.04 if args.min_edge is None else args.min_edge,
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


def _print_gems(result: ComboSearch) -> None:
    print(f"xG usati: casa {result.xg_home:.2f} | ospite {result.xg_away:.2f}")
    for note in result.notes:
        print(f"sesto senso: {note}")
    headers = ("Mercato", "Quota Book", "Fair Odd", "P_matrix", "Edge", "Note Tattiche Sesto Senso")
    if not result.ranked:
        print(" | ".join(headers))
        print("Nessuna pepita nello sweet spot. Quota sotto 1.35, sopra 1.80, o con veto, resta fuori.")
        return
    rows = [headers]
    for combo in result.ranked:
        note = "; ".join(combo.notes) if combo.notes else "—"
        rows.append(
            (
                combo.market,
                f"{combo.book_odd:.2f}",
                f"{combo.fair_odd:.2f}",
                f"{combo.probability:.1%}",
                f"{combo.edge:+.1%}",
                note,
            )
        )
    widths = [max(len(row[index]) for row in rows) for index in range(len(headers))]
    for row in rows:
        print(" | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))


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

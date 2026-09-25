"""Prezza i mercati live sul tempo che resta e tiene solo lo sweet spot.

Esempio:
  python scripts/scan_live_opportunities.py --minute 72 --score "1-0" \
    --xg-home 1.8 --xg-away 1.1 --shots-home 14 --shots-away 3 \
    --corners-home 7 --corners-away 1 --red-cards-away 1 \
    --odds "Over 1.5 Gol Live=1.55,Over 9.5 Corner Live=1.65,Next Goal Casa=1.85"
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.live.live_in_play_engine import project_residual, scan_live_book
from services.live.live_momentum_sniper import LiveMatchSnapshot, LiveMomentumSniper


def main() -> None:
    parser = argparse.ArgumentParser(description="Sniping live sul Poisson dei minuti rimanenti.")
    parser.add_argument("--minute", type=int, required=True)
    parser.add_argument("--score", required=True, help='Punteggio live, es. "1-0"')
    parser.add_argument("--xg-home", type=float, required=True)
    parser.add_argument("--xg-away", type=float, required=True)
    parser.add_argument("--shots-home", type=int, default=0)
    parser.add_argument("--shots-away", type=int, default=0)
    parser.add_argument("--sot-home", type=int, default=0)
    parser.add_argument("--sot-away", type=int, default=0)
    parser.add_argument("--corners-home", type=int, default=0)
    parser.add_argument("--corners-away", type=int, default=0)
    parser.add_argument("--red-cards-home", type=int, default=0)
    parser.add_argument("--red-cards-away", type=int, default=0)
    parser.add_argument("--stoppage", type=int, default=4)
    parser.add_argument("--favorite", default="EQUAL", choices=("HOME", "AWAY", "EQUAL"))
    parser.add_argument("--suspended", action="store_true", help="Quote live sospese (VAR, rigore)")
    parser.add_argument("--odds", default="", help="Mercato=quota, separati da virgola")
    parser.add_argument("--match", default="Live")
    args = parser.parse_args()

    home_goals, away_goals = _score(args.score)
    odds = _parse_odds(args.odds)
    state = project_residual(
        args.xg_home,
        args.xg_away,
        args.minute,
        stoppage=args.stoppage,
        home_goals=home_goals,
        away_goals=away_goals,
        home_reds=args.red_cards_home,
        away_reds=args.red_cards_away,
        home_shots=args.shots_home,
        away_shots=args.shots_away,
        home_shots_on_target=args.sot_home,
        away_shots_on_target=args.sot_away,
        home_corners=args.corners_home,
        away_corners=args.corners_away,
        favorite=args.favorite,
    )
    priced, rejected = scan_live_book(
        state,
        odds,
        home_goals=home_goals,
        away_goals=away_goals,
        home_corners=args.corners_home,
        away_corners=args.corners_away,
        second_half_goals=0 if home_goals + away_goals == 0 and args.minute >= 46 else None,
        suspended=args.suspended,
    )
    print(
        f"xG residui: casa {state.lambda_home:.2f} | ospite {state.lambda_away:.2f} "
        f"| tempo {state.time_fraction:.1%}"
    )
    for note in state.notes:
        print(f"sesto senso: {note}")

    snapshot = LiveMatchSnapshot(
        fixture_id="cli",
        match_name=args.match,
        minute=args.minute,
        home_team="Casa",
        away_team="Ospite",
        home_goals=home_goals,
        away_goals=away_goals,
        home_shots=args.shots_home,
        away_shots=args.shots_away,
        home_shots_on_target=args.sot_home,
        away_shots_on_target=args.sot_away,
        home_corners=args.corners_home,
        away_corners=args.corners_away,
        home_red_cards=args.red_cards_home,
        away_red_cards=args.red_cards_away,
        pre_match_favorite=args.favorite,
        xg_home=args.xg_home,
        xg_away=args.xg_away,
        stoppage=args.stoppage,
        odds_suspended=args.suspended,
    )
    signals = LiveMomentumSniper().scan(snapshot, odds)
    by_market = {signal.exact_selection: signal for signal in signals}

    headers = ("Mercato", "Quota Book", "Fair Odd", "P_live", "Edge", "Stake", "Esito")
    rows = [headers]
    for item in priced:
        signal = by_market.get(item.market)
        rows.append(
            (
                item.market,
                f"{item.book_odd:.2f}",
                f"{item.fair_odd:.2f}",
                f"{item.probability:.1%}",
                f"{item.edge:+.1%}",
                f"{item.stake_pct:.1%}",
                "PEPITA" if signal is not None else "",
            )
        )
    for item in rejected:
        rows.append((item.market, "-", "-", "-", "-", "-", item.reason))
    if len(rows) == 1:
        print("Nessuna quota live da prezzare.")
        return
    widths = [max(len(row[index]) for row in rows) for index in range(len(headers))]
    for row in rows:
        print(" | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row)))
    if not priced:
        print("Nessuna pepita nello sweet spot live.")


def _score(raw: str) -> tuple[int, int]:
    parts = raw.replace(" ", "").split("-")
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        raise SystemExit(f"Punteggio non leggibile: {raw!r}")
    return int(parts[0]), int(parts[1])


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

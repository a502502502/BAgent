"""Scansione dei mercati Netwin di una partita, ordinati per probabilità.

Esempio:
    python scripts/match_market_scanner.py --match "Germania vs Serbia" --alternatives
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.match_market_optimizer import MatchMarketOptimizer, _CARD_WORD, _CORNER_WORD


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argv)
    optimizer = MatchMarketOptimizer()
    try:
        scan = optimizer.scan(args.match or "", args.home or "", args.away or "")
    except LookupError as exc:
        print(exc)
        return 1
    print(
        f"{scan.match_name}  {scan.tournament}  {scan.kickoff}\n"
        f"lambda {scan.lambda_home:.2f} / {scan.lambda_away:.2f}  "
        f"rho {scan.rho:+.3f}  fonte {scan.source}\n"
        f"corner {scan.corner_home:.2f} / {scan.corner_away:.2f}  "
        f"cartellini {scan.card_home:.2f} / {scan.card_away:.2f}  fonte {scan.count_source}"
    )
    if scan.sample_home is not None and scan.sample_away is not None:
        print(f"partite nel fit  {scan.home_team} {scan.sample_home}  {scan.away_team} {scan.sample_away}")
        if min(scan.sample_home, scan.sample_away) < 5:
            print("campione sotto 5 partite: le lambda sono shrinkage, non la caratura della rosa")
    top = [
        row for row in optimizer.get_highest_probability_markets(min_odd=args.min_odd, limit=20)
        if row.probability >= args.min_prob
    ]
    print("\nTop mercati per probabilità")
    _print_markets(top)
    print("\nSweet spot  P>=70%  quota 1.25-1.80  edge>0")
    _print_markets(optimizer.sweet_spot())
    specialty = [
        row for row in scan.markets
        if _CORNER_WORD.search(row.market) or _CARD_WORD.search(row.market)
    ]
    print("\nCorner e cartellini")
    _print_markets(specialty)
    if args.alternatives:
        print("\nAlternative combo contro il singolo")
        _print_alternatives(optimizer.find_alternative_combos("1X2"))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Scanner mercati Netwin di una partita")
    parser.add_argument("--match", default="", help='Es. "Germania vs Serbia"')
    parser.add_argument("--home", default="")
    parser.add_argument("--away", default="")
    parser.add_argument("--min-prob", type=float, default=0.70)
    parser.add_argument("--min-odd", type=float, default=1.20)
    parser.add_argument("--alternatives", action="store_true")
    return parser


def _print_markets(rows) -> None:
    if not rows:
        print("  nessuno")
        return
    print(f"  {'Mercato':<32} {'Quota':>7} {'Fair':>7} {'P%':>7} {'Edge%':>8}  Resilienza")
    for row in rows:
        odd = f"{row.odd:7.2f}" if row.odd is not None else "      -"
        edge = f"{row.edge * 100:7.1f}" if row.edge is not None else "      -"
        print(
            f"  {row.market:<32} {odd} {row.fair_odd:7.2f} "
            f"{row.probability * 100:6.1f} {edge}  {row.resilience}"
        )


def _print_alternatives(rows) -> None:
    if not rows:
        print("  nessuna combo quotata da confrontare")
        return
    print(f"  {'Singolo':<14} {'Q':>5} {'P%':>6} {'Combo':<28} {'Q':>5} {'P%':>6} {'dP':>7}  Scenario")
    for row in rows:
        single_odd = f"{row.single_odd:5.2f}" if row.single_odd else "    -"
        alternative_odd = f"{row.alternative_odd:5.2f}" if row.alternative_odd else "    -"
        print(
            f"  {row.single:<14} {single_odd} {row.single_probability * 100:6.1f} "
            f"{row.alternative:<28} {alternative_odd} {row.alternative_probability * 100:6.1f} "
            f"{row.delta_p * 100:6.1f}  {row.scenario}"
        )


if __name__ == "__main__":
    raise SystemExit(main())

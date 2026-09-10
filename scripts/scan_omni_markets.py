#!/usr/bin/env python3
"""
scripts/scan_omni_markets.py — Scanner Onnimercato & Classifica Bilanciamento (Regole #33, #39, #40, #41).

Scansiona TUTTI i mercati a disposizione per un match e individua quelli
con il perfetto bilanciamento tra:
- ALTA PROBABILITÀ REALE (P >= 72-85%)
- QUOTA EFFICACE (1.28 - 1.65, NO quote stracciate a resa zero, NO quote a varianza folle)
- VALORE / EDGE MATEMATICO (Edge >= +4.0%)
- RESPIRO A 90 MINUTI (Protezione contro la trappola del 45')

Uso:
    python scripts/scan_omni_markets.py --fixture 1635659
    python scripts/scan_omni_markets.py --fixture 1635708
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.omni_market_scanner import OmniMarketScanner

def main():
    parser = argparse.ArgumentParser(description="Scanner Onnimercato & Balanced Safety Score")
    parser.add_argument("--fixture", type=int, required=True, help="ID Fixture API-Football")
    parser.add_argument("--xg-home", type=float, default=1.75, help="xG stimato squadra casa")
    parser.add_argument("--xg-away", type=float, default=1.15, help="xG stimato squadra ospite")
    parser.add_argument("--xc-home", type=float, default=6.5, help="xC corner stimati casa")
    parser.add_argument("--xc-away", type=float, default=3.5, help="xC corner stimati ospite")
    parser.add_argument("--xk-home", type=float, default=2.1, help="xK cartellini stimati casa")
    parser.add_argument("--xk-away", type=float, default=2.7, help="xK cartellini stimati ospite")
    args = parser.parse_args()

    scanner = OmniMarketScanner()
    print(f"\n=========================================================================================")
    print(f"📡 SCANSIONE ONNIMERCATO COMPLETA — Fixture #{args.fixture}")
    print(f"=========================================================================================")

    fix_data = scanner.fetch_fixture_info(args.fixture)
    h_team = fix_data.get("teams", {}).get("home", {}).get("name", "Casa")
    a_team = fix_data.get("teams", {}).get("away", {}).get("name", "Ospite")
    league = fix_data.get("league", {}).get("name", "Competizione")

    print(f"⚽ Match:    {h_team} vs {a_team} ({league})")
    print(f"📊 Modello:  xG Casa={args.xg_home:.2f} | xG Ospite={args.xg_away:.2f} | xC={args.xc_home:.1f}-{args.xc_away:.1f} | xK={args.xk_home:.1f}-{args.xk_away:.1f}")
    print(f"-----------------------------------------------------------------------------------------")

    picks = scanner.scan_fixture(
        fixture_id=args.fixture,
        xg_home=args.xg_home,
        xg_away=args.xg_away,
        xc_home=args.xc_home,
        xc_away=args.xc_away,
        xk_home=args.xk_home,
        xk_away=args.xk_away,
    )

    approved = [p for p in picks if p.is_approved]
    rejected = [p for p in picks if not p.is_approved]

    print(f"\n🏆 I MERCATI PIÙ BILANCIATI & SICURI (Sweet Spot: Probabilità 75-88% | Quota 1.28-1.65 | Edge >= +5%):")
    print(f"{'#':<3} {'Categoria':<18} {'Mercato / Selezione':<28} {'Quota':<7} {'Prob Reale':<12} {'Edge':<9} {'BSS Score':<10}")
    print(f"{'-'*92}")

    for idx, p in enumerate(approved[:8], 1):
        print(
            f"{idx:<3} {p.market_category:<18} {p.market_name:<28} "
            f"@{p.bookmaker_odd:<6.2f} {p.real_probability*100:>5.1f}% (fair @{p.fair_odd:.2f})  "
            f"{p.mathematical_edge*100:>+5.1f}%   {p.balanced_safety_score:>6.1f} ⭐"
        )

    print(f"\n❌ MERCATI BOCCIATI / TRAPPOLE SCARTATE ({len(rejected)} mercati eliminati dal filtro matematico):")
    print(f"{'Categoria':<18} {'Mercato / Selezione':<30} {'Quota':<7} {'Prob':<8} {'Motivo Scarto'}")
    print(f"{'-'*92}")
    for p in rejected[:8]:
        print(
            f"{p.market_category:<18} {p.market_name:<30} @{p.bookmaker_odd:<6.2f} "
            f"{p.real_probability*100:>5.1f}%  {p.rejection_reason or 'Non conforme'}"
        )

    print(f"\n=========================================================================================\n")


if __name__ == "__main__":
    main()

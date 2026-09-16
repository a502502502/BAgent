#!/usr/bin/env python3
"""
scripts/scan_special_combinations.py — Special Combinations Scanner CLI.

Scansiona e calcola le combinazioni ad altissima resilienza:
- Chance Mix a Matrice Unione (1X o Over 1.5, X2 o Over 1.5, Gol o Over 2.5);
- MultiGol Asimmetrico per Tempi (0-2 1°T & 1-3 2°T);
- Dutching Asimmetrico a Paracadute (Twin-Ticket Lock);
- Tripla Balistica Ortogonale.

Uso:
    python scripts/scan_special_combinations.py --match "Betis vs Getafe" --xg-home 1.45 --xg-away 0.85
    python scripts/scan_special_combinations.py --match "Manchester City vs Napoli" --xg-home 2.35 --xg-away 0.70
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.special_combinations_engine import SpecialCombinationsEngine

def print_banner(title: str):
    line = "=" * 85
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")

def main():
    parser = argparse.ArgumentParser(description="BAgent Special Combinations Scanner CLI")
    parser.add_argument("--match", type=str, required=True, help="Nome della partita (es. 'Betis vs Getafe')")
    parser.add_argument("--xg-home", type=float, default=1.50, help="xG attesi squadra casa")
    parser.add_argument("--xg-away", type=float, default=1.00, help="xG attesi squadra ospite")
    
    args = parser.parse_args()
    engine = SpecialCombinationsEngine()

    print_banner(f"🧬 SCANSIONE COMBINAZIONI SPECIALI & CHANCE MIX: {args.match}")
    print(f"Parametri Balistici: xG Casa = {args.xg_home:.2f} | xG Ospite = {args.xg_away:.2f} | xG Totali = {args.xg_home + args.xg_away:.2f}")

    specials = engine.scan_best_specials_for_match(args.match, args.xg_home, args.xg_away)
    if not specials:
        print("\nNessuna combinazione speciale soddisfa i criteri di super-resilienza (Prob >= 82% & Edge >= +5%).")
        return

    print(f"\nTrovate {len(specials)} formule ad altissima resilienza:\n")
    for idx, s in enumerate(specials, 1):
        icon = "💎" if s.resilience_rating == "QUASI_INFALLIBILE" else ("🛡️" if s.resilience_rating == "ACCIAIO" else "⭐")
        print(f"{idx}. {icon} {s.selection_name} [{s.resilience_rating}]")
        print(f"   • Dicitura Netwin:   '{s.netwin_market_label}'")
        print(f"   • Probabilità Reale: {s.real_probability:.1%} | Quota Minima Equa: @{s.fair_odd:.2f} | Quota Indicativa: @{s.estimated_bookmaker_odd:.2f}")
        print(f"   • Edge Matematico:   {s.mathematical_edge:+.1%}")
        print(f"   • Unico Rischio KO:  {s.single_losing_scenario}")
        print(f"   • Spiegazione:       {s.tactical_rationale}")
        if s.dutching_stake_split:
            sp = s.dutching_stake_split
            print(f"   • Ripartizione Stake (€10): Core €{sp['core_stake_eur']} (paga €{sp['payout_core_eur']}) | Paracadute €{sp['parachute_stake_eur']} (paga €{sp['payout_parachute_eur']})")
        print("-" * 85)

if __name__ == "__main__":
    main()

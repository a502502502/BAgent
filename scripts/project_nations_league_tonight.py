"""Proiezioni quantitative e mercati per le partite di Nations League di stasera (05/10/2026)."""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.analysis.match_market_optimizer import MatchMarketOptimizer
from services.analysis.xg_poisson_engine import QuantitativeEngine

nl_matches = [
    ("Francia", "Belgio", "Francia vs Belgio"),
    ("Italia", "Turchia", "Italia vs Turchia"),
    ("Bosnia Erzegovina", "Polonia", "Bosnia Erzegovina vs Polonia"),
    ("Ucraina", "Ungheria", "Ucraina vs Ungheria"),
    ("Irlanda Del Nord", "Georgia", "Irlanda Del Nord vs Georgia"),
    ("Cipro", "Lettonia", "Cipro vs Lettonia"),
    ("Montenegro", "Armenia", "Montenegro vs Armenia"),
]

optimizer = MatchMarketOptimizer()
engine = QuantitativeEngine()

print("=" * 80)
print("🇪🇺 PROIEZIONI NATIONS LEAGUE — LUNEDÌ 05 OTTOBRE 2026 (ORE 20:45)")
print("=" * 80)

for home, away, label in nl_matches:
    print(f"\n⚽ MATCH: {label}")
    print("-" * 80)
    try:
        scan = optimizer.scan(label, home, away)
        print(
            f"📊 Lambda: {scan.home_team} {scan.lambda_home:.2f} vs {scan.away_team} {scan.lambda_away:.2f} (rho: {scan.rho:+.3f})\n"
            f"⛳ Corner attesi: {scan.corner_home:.2f} vs {scan.corner_away:.2f} | 🟨 Cartellini attesi: {scan.card_home:.2f} vs {scan.card_away:.2f}\n"
            f"Campione fit: {scan.sample_home} partite casa, {scan.sample_away} partite ospite"
        )

        sweet = optimizer.sweet_spot()
        if sweet:
            print("\n  ⭐ SWEET SPOT (P >= 70%, Quota 1.25-1.80, Edge > 0):")
            for m in sweet:
                edge_str = f"+{m.edge*100:.1f}%" if m.edge and m.edge > 0 else f"{m.edge*100:.1f}%" if m.edge else "N/A"
                print(f"     • {m.market:<32} Quota: {m.odd:<5.2f} Fair: {m.fair_odd:<5.2f} P: {m.probability*100:>5.1f}% Edge: {edge_str} ({m.resilience})")

        # Top probabilità
        top = [m for m in optimizer.get_highest_probability_markets(min_odd=1.20, limit=6) if m.probability >= 0.70]
        if top:
            print("\n  🛡️ TOP RESILIENTI (P >= 70%):")
            for m in top:
                edge_str = f"+{m.edge*100:.1f}%" if m.edge and m.edge > 0 else f"{m.edge*100:.1f}%" if m.edge else "N/A"
                odd_str = f"{m.odd:.2f}" if m.odd else "-"
                print(f"     • {m.market:<32} Quota: {odd_str:<5} Fair: {m.fair_odd:<5.2f} P: {m.probability*100:>5.1f}% Edge: {edge_str} ({m.resilience})")

    except Exception as e:
        print(f"Calcolo non riuscito: {e}")

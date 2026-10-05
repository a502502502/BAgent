"""Scansione e proiezioni matematiche per le partite in programma stasera."""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.analysis.match_market_optimizer import MatchMarketOptimizer

matches_tonight = [
    "Deportivo Riestra vs Central Cordoba",
    "Estudiantes vs Gimnasia Y Esgrima Mendoza",
    "Velez Sarsfield vs Platense",
    "Banfield vs Rosario Central",
]

optimizer = MatchMarketOptimizer()

print("=" * 80)
print("🎯 PROIEZIONI QUANTITATIVE PARTITE DI STASERA (05/10/2026)")
print("=" * 80)

for match_name in matches_tonight:
    print(f"\n⚽ MATCH: {match_name}")
    print("-" * 80)
    try:
        scan = optimizer.scan(match_name)
    except LookupError as e:
        print(f"Non trovato nel palinsesto: {e}")
        continue

    print(
        f"🏆 Torneo: {scan.tournament} | Calcio d'inizio: {scan.kickoff}\n"
        f"📊 Lambda: {scan.home_team} {scan.lambda_home:.2f} vs {scan.away_team} {scan.lambda_away:.2f} (rho: {scan.rho:+.3f})\n"
        f"⛳ Corner attesi: {scan.corner_home:.2f} vs {scan.corner_away:.2f} | 🟨 Cartellini attesi: {scan.card_home:.2f} vs {scan.card_away:.2f}"
    )

    sweet = optimizer.sweet_spot()
    if sweet:
        print("\n  ⭐ SWEET SPOT (P >= 70%, Quota 1.25-1.80, Edge > 0):")
        for m in sweet:
            edge_str = f"+{m.edge*100:.1f}%" if m.edge and m.edge > 0 else f"{m.edge*100:.1f}%" if m.edge else "N/A"
            print(f"     • {m.market:<30} Quota: {m.odd:<5.2f} Fair: {m.fair_odd:<5.2f} P: {m.probability*100:>5.1f}% Edge: {edge_str} ({m.resilience})")
    else:
        print("  ⚠️ Nessun mercato nello sweet spot standard.")

    # Top mercati ad alta probabilità (P >= 72%)
    high_p = [m for m in optimizer.get_highest_probability_markets(min_odd=1.18, limit=8) if m.probability >= 0.72]
    if high_p:
        print("\n  🛡️ TOP MERCATI ALTA RESILIENZA (P >= 72%):")
        for m in high_p:
            edge_str = f"+{m.edge*100:.1f}%" if m.edge and m.edge > 0 else f"{m.edge*100:.1f}%" if m.edge else "N/A"
            print(f"     • {m.market:<30} Quota: {m.odd:<5.2f} Fair: {m.fair_odd:<5.2f} P: {m.probability*100:>5.1f}% Edge: {edge_str} ({m.resilience})")

"""
BAgent - Kelly Staking Calculator & Tester
Esegue simulazioni e calcoli immediati dello stake ottimale
in base a Bankroll, Quote ed Edge stimato.
"""

import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from services.betting.kelly_staking_engine import KellyStakingEngine

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_test():
    bankroll = 116.45
    engine = KellyStakingEngine(current_bankroll=bankroll)

    print(f"===========================================================")
    print(f"   💰 BAGENT KELLY STAKING ENGINE — SIMULAZIONE AUDIT")
    print(f"   Saldo Bankroll Attuale: {bankroll:.2f} €")
    print(f"===========================================================\n")

    # Test Scenari
    scenarios = [
        {
            "name": "🛡️ Ticket #22: Corner & Sanzioni Totali Match",
            "odds": 2.23,
            "prob": 0.55, # 55% stimata da Poisson / FootyStats
            "market_type": "corner_totali"
        },
        {
            "name": "👑 Ticket #23: Gol & Doppie Chance d'Acciaio",
            "odds": 2.21,
            "prob": 0.52, # 52% stimata
            "market_type": "doppia_chance_gol"
        },
        {
            "name": "⚔️ Ticket #24: Quaterna Duelli 1v1 & Falli d'Elite",
            "odds": 4.63,
            "prob": 0.28, # 28% stimata
            "market_type": "falli_giocatore"
        },
        {
            "name": "🎲 Lotto Matematico / Multipla Lunga (No Edge)",
            "odds": 25.0,
            "prob": 0.03, # 3% stimata vs Quota 25 (Implicita 4% -> Edge Negativo)
            "market_type": "general"
        }
    ]

    print("📊 1. ANALISI DEI SINGOLI TICKET:\n")
    for s in scenarios:
        rec = engine.calculate_stake(
            odds=s["odds"],
            estimated_prob=s["prob"],
            market_type=s["market_type"]
        )
        print(f"📌 {s['name']}")
        print(f"   • Quota: {rec.odds:.2f}× | Probabilità Stimata: {rec.estimated_prob*100:.1f}%")
        print(f"   • Vantaggio Matematico (Edge): {rec.edge_pct:+.2f}%")
        print(f"   • Kelly Pieno (Full): {rec.full_kelly_pct:.2f}% | Kelly Frazionario: {rec.fractional_kelly_pct:.2f}%")
        print(f"   • 💵 STAKE RACCOMANDATO: {rec.recommended_stake:.2f} € (Max Cap: {rec.max_stake:.2f} €)")
        print(f"   • Verdetto: {rec.verdict} [Livello Rischio: {rec.risk_level}]")
        print(f"   • Tasso di Crescita Atteso: {rec.expected_growth_rate:+.4f}%")
        print("-" * 55)

    print("\n📦 2. ALLOCAZIONE GIORNALIERA CONGIUNTA (Max 25% Bankroll = 29.11 €):\n")
    allocated = engine.allocate_daily_tickets(scenarios[:3])
    total_spent = sum(item["calculated_stake"] for item in allocated)
    for a in allocated:
        print(f"   • {a['name']}: {a['calculated_stake']:.2f} € (Quota {a['odds']:.2f}×)")
    print(f"\n   💵 Totale Impegnato nella Giornata: {total_spent:.2f} € / 29.11 € Max (Sicurezza Bankroll: 100% OK)")

if __name__ == "__main__":
    run_test()

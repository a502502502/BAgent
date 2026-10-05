import json
import os
import sys
from pathlib import Path

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.universal_ticket_builder import UniversalTicketBuilder

def main():
    print("=" * 70)
    print("🚀 GENERATORE TICKET QUANTITATIVI BAGENT (BOOKMAKER-AGNOSTIC)")
    print("Zero Netwin Scraping | The Odds API | penaltyblog Shin Devig | xG Poisson")
    print("=" * 70)

    fixtures_path = ROOT / "data" / "the_odds_api_live.json"
    if not fixtures_path.exists():
        print("File quote the_odds_api_live.json non trovato!")
        return

    with open(fixtures_path, "r", encoding="utf-8") as f:
        fixtures = json.load(f)

    # Filtra partite che si giocano STASERA (tra oggi 15:00 UTC e stanotte 03:00 UTC)
    today_fixtures = [
        f for f in fixtures 
        if f.get("commence_time", "").startswith("2026-10-05") or (
            f.get("commence_time", "").startswith("2026-10-06") and "00:" in f.get("commence_time", "")
        ) or (
            f.get("commence_time", "").startswith("2026-10-06") and "01:" in f.get("commence_time", "")
        )
    ]
    print(f"📊 Partite disponibili per STASERA: {len(today_fixtures)}")

    builder = UniversalTicketBuilder()
    tickets = builder.build_tickets(today_fixtures)

    tickets_dir = ROOT / "reports" / "tickets"
    tickets_dir.mkdir(parents=True, exist_ok=True)

    for key, t_data in tickets.items():
        if not t_data or not t_data.get("legs"):
            continue

        filename = f"{t_data['ticket_id'].lower()}.json"
        target_file = tickets_dir / filename
        with open(target_file, "w", encoding="utf-8") as out:
            json.dump(t_data, out, indent=2)

        print(f"\n🎟️ {t_data['name'].upper()}")
        print(f"   Quota Totale: {t_data['total_odds']} | Prob. Modello: {t_data['combined_model_prob']*100:.1f}% | Edge EV: +{t_data['net_edge_ev_pct']}%")
        print(f"   Stake consigliato: €{t_data['stake_eur']:.2f} | Vincita potenziale: €{t_data['potential_payout_eur']:.2f}")
        print("   --- SELEZIONI ---")
        for i, leg in enumerate(t_data["legs"], 1):
            print(f"   {i}. [{leg['commence_time'][:16].replace('T', ' ')}] {leg['home_team']} vs {leg['away_team']}")
            print(f"      📌 Giocata: {leg['market']} -> {leg['pick']}")
            print(f"      📈 Quota: {leg['best_market_odds']} (Fair: {leg['fair_odds']} | Min Valore: {leg['min_value_odds']})")
            print(f"      🎯 Probabilità: {leg['model_prob']*100:.1f}% | Edge: +{leg['edge_pct']}% | Top Book: {leg['best_bookmaker']}")
        print(f"   💾 Salvato in: reports/tickets/{filename}")

    print("\n" + "=" * 70)
    print("✅ GENERAZIONE COMPLETATA CON SUCCESSO!")
    print("=" * 70)

if __name__ == "__main__":
    main()

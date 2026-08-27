"""
BAgent - Dropping Odds Tracker & CLI Monitor
Monitora le variazioni di quota sui mercati europei ed emette alert
quando gli scommettitori istituzionali (Smart Money) muovono le linee.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from services.betting.dropping_odds_detector import DroppingOddsDetector

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_simulation():
    detector = DroppingOddsDetector()

    print("================================================================================")
    print("   📉 BAGENT DROPPING ODDS & CLOSING LINE VALUE (CLV) DETECTOR")
    print("   Tracking Flussi Finanziari & Smart Money sui Mercati Internazionali")
    print("================================================================================\n")

    # Scenari di mercato reali odierni (27 Agosto 2026)
    market_events = [
        {
            "event_id": "uecl_hapoel_ata",
            "match": "Hapoel Tel Aviv vs Atalanta",
            "tournament": "UEFA Conference League",
            "market": "1X2 (Esito Finale)",
            "selection": "2 (Atalanta)",
            "opening": 1.70,
            "current": 1.45, # Crollo del 14.7% per rientro De Ketelaere/Scamacca
            "bookmakers": 8,
            "closing": 1.40
        },
        {
            "event_id": "laliga_bar_ath",
            "match": "FC Barcellona vs Athletic Club",
            "tournament": "LaLiga EA Sports",
            "market": "Combo Risultato & Gol",
            "selection": "1 + Over 2.5 Gol",
            "opening": 2.05,
            "current": 1.72, # Crollo del 16.1% per forma travolgente Barça
            "bookmakers": 12,
            "closing": 1.68
        },
        {
            "event_id": "uecl_part_get",
            "match": "Partizan Belgrado vs Getafe",
            "tournament": "UEFA Conference League",
            "market": "Cartellini Totali",
            "selection": "Over 3.5 Cartellini",
            "opening": 1.60,
            "current": 1.45, # Crollo del 9.4% (Smart Money su partita ruvida)
            "bookmakers": 6,
            "closing": 1.42
        },
        {
            "event_id": "uecl_vik_bri",
            "match": "Vikingur Reykjavik vs Brighton",
            "tournament": "UEFA Conference League",
            "market": "1X2 (Esito Finale)",
            "selection": "1 (Vikingur)",
            "opening": 8.50,
            "current": 10.50, # Quota in salita (+23.5% Drifting)
            "bookmakers": 7,
            "closing": 11.00
        }
    ]

    print("🔍 1. SCANSIONE MOVIMENTI DI QUOTA & SMART MONEY:\n")
    for ev in market_events:
        mov = detector.analyze_movement(
            event_id=ev["event_id"],
            match_name=ev["match"],
            tournament=ev["tournament"],
            market=ev["market"],
            selection=ev["selection"],
            opening_odds=ev["opening"],
            current_odds=ev["current"],
            bookmakers_count=ev["bookmakers"],
            closing_odds=ev.get("closing")
        )

        print(f"📌 {mov.match_name} ({mov.tournament})")
        print(f"   • Mercato: {mov.market} ➔ [{mov.selection}]")
        print(f"   • Apertura: {mov.opening_odds:.2f} ➔ Attuale: {mov.current_odds:.2f} (Crollo: {mov.drop_pct:+.2f}%)")
        print(f"   • Bookmaker Coinvolti: {mov.bookmakers_count}")
        print(f"   • Segnale: {mov.signal_strength}")
        if mov.clv_pct is not None:
            print(f"   • Closing Line Value (CLV): {mov.clv_pct:+.2f}% ({'✅ Beat the Line' if mov.clv_pct > 0 else '❌ Sotto Linea'})")
        print(f"   • Analisi: {mov.notes}")
        print("-" * 75)

    print("\n📱 2. ANTEPRIMA ALERT TELEGRAM GENERATO PER SMART MONEY:\n")
    for k, mov in detector.tracked_events.items():
        tg_msg = detector.format_telegram_alert(mov)
        if tg_msg:
            print(tg_msg)
            print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    run_simulation()

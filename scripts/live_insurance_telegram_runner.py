"""
BAgent - Live Insurance & Dutching Tester
Esegue simulazioni di copertura in tempo reale sui nostri ticket aperti
(Ticket #31, #32, #33) e genera gli alert formattati per Telegram.
"""

import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from services.betting.one_click_live_insurance_engine import OneClickLiveInsuranceEngine, TicketLiveStatus

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_test():
    engine = OneClickLiveInsuranceEngine()

    print("================================================================================")
    print("   🛡️ BAGENT ONE-CLICK LIVE DUTCHING & INSURANCE ENGINE")
    print("   Calcolo Automatico Coperture Matematiche (Break-Even & Profit-Lock)")
    print("================================================================================\n")

    # Scenario 1: Ticket #31 (Gol & Doppie Chance) — Atalanta e Braga hanno vinto, manca Barcellona-Athletic
    # In Barcellona-Athletic siamo al 75' sul 1-0 (abbiamo 1X + Over 1.5). C'è il rischio di 1-0 finale (Under 1.5).
    # Copertura su "Risultato Esatto 1-0 Finale" @ 3.40 per proteggere i 20€ di stake
    hedges_t31 = engine.calculate_hedges(
        initial_stake=20.00,
        potential_payout=44.20,
        hedge_odds=3.40,
        hedge_market="Risultato Esatto Finale",
        hedge_selection="1-0 Barcellona"
    )

    status_t31 = TicketLiveStatus(
        ticket_id="TICKET_31_LIVE",
        ticket_name="👑 Ticket #31: Gol & Doppie Chance d'Acciaio",
        initial_stake_eur=20.00,
        potential_payout_eur=44.20,
        total_legs=3,
        legs_won=2, # Atalanta ✅, Braga ✅
        legs_pending=1, # Barcellona in corso
        critical_match="FC Barcellona vs Athletic Club",
        current_minute=75,
        current_score="1-0 (Barça)",
        hedge_options=hedges_t31
    )

    alert_msg = engine.generate_telegram_insurance_alert(status_t31)
    print("📱 ANTEPRIMA ALERT TELEGRAM GENERATO:\n")
    print(alert_msg)

if __name__ == "__main__":
    run_test()

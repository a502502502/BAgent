#!/usr/bin/env python3
"""
Test Netwin Automator & Telegram 1-Click Approval
Invia un ticket di test su Telegram con pulsanti interattivi di approvazione
e avvia l'ascolto dei callback.

Uso: python3 scripts/test_netwin_automator.py
"""

import time
import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from services.telegram.interactive_bot import TelegramInteractiveBot

# Ticket di Test (Sabato 22 Agosto - Cassaforte)
TEST_TICKET_ID = f"T14_{int(time.time())}"
TEST_SELECTIONS = [
    {"match": "Brentford", "market": "UNDER_OVER", "pick": "Over 1.5"},
    {"match": "Genoa", "market": "DOPPIA_CHANCE_OU", "pick": "X2 + Over 1.5"},
    {"match": "Inter", "market": "DOPPIA_CHANCE_OU", "pick": "1X + Over 1.5"},
    {"match": "Real Madrid", "market": "1X2", "pick": "2"},
]

CARD_TEXT = (
    f"📋 <b>TICKET #15 — CASSAFORTE D'ACCIAIO (Sabato 22 Agosto)</b>\n"
    f"━━━━━━━━━━━━━━━━━━━━━\n"
    f"• 🏴󠁧󠁢󠁥󠁮󠁧󠁿 <b>Brentford vs Tottenham</b> (18:30)\n"
    f"   └ 🎯 Over 1.5 Gol @1.22\n\n"
    f"• 🇮🇹 <b>Genoa vs Napoli</b> (18:30)\n"
    f"   └ 🎯 X2 + Over 1.5 Gol @1.34\n\n"
    f"• 🇮🇹 <b>Inter vs Monza</b> (20:45)\n"
    f"   └ 🎯 1X + Over 1.5 Gol @1.25\n\n"
    f"• 🇪🇸 <b>Espanyol vs Real Madrid</b> (21:30)\n"
    f"   └ 🎯 1X2: 2 @1.32\n"
    f"━━━━━━━━━━━━━━━━━━━━━\n"
    f"📊 <b>Quota Totale</b>: <b>2.70×</b> (con Bonus Netwin: <b>~3.10×</b>)\n"
    f"💰 <b>Stake</b>: <b>20.00 €</b> ➔ <b>Vincita Potenziale: ~62.00 €</b>\n\n"
    f"⚡ <i>Premi un pulsante qui sotto per autorizzare l'inserimento:</i>"
)

def main():
    print("=" * 70)
    print("🤖 Test Netwin 1-Click Automator & Telegram Interactive Bot")
    print("=" * 70)

    bot = TelegramInteractiveBot()
    
    # Registra il ticket
    bot.register_ticket(
        ticket_id=TEST_TICKET_ID,
        selections=TEST_SELECTIONS,
        stake=20.0,
        bet_mode="MULTIPLE",
    )

    # Invia la scheda con pulsanti interattivi
    print("Inoltro scheda interattiva su Telegram...")
    bot.send_ticket_with_buttons(
        ticket_id=TEST_TICKET_ID,
        card_text=CARD_TEXT,
        stake=20.0,
    )
    print("✅ Messaggio con pulsanti inviato su Telegram (@A502502_bot)!")
    print("In ascolto di eventuali clic (Ctrl+C per terminare)...")
    
    try:
        bot.start_polling()
    except KeyboardInterrupt:
        print("\nTest terminato.")

if __name__ == "__main__":
    main()

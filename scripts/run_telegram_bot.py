"""
scripts/run_telegram_bot.py — Avvio del Bot Telegram Interattivo BAgent (@A502502_bot).
Invia il menu iniziale all'utente e si mette in ascolto per calcolare qualsiasi partita ricevuta in chat.
"""

import os
import sys
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.telegram.telegram_sentinel import TelegramSentinel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

if __name__ == "__main__":
    bot = TelegramSentinel()
    # Invia il menu principale all'utente per confermare l'avvio
    bot._send_main_menu()
    logging.info("🤖 BAgent Telegram Bot attivo in ascolto su @A502502_bot...")
    try:
        bot.start_listening()
    except KeyboardInterrupt:
        bot.stop_listening()
        logging.info("Bot arrestato.")

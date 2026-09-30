#!/usr/bin/env python3
"""
BAgent Auto-Telegram Tool v1.0
Automatizza la creazione del servizio di notifica Telegram integrato.
"""

import os
from pathlib import Path
import shutil
from datetime import datetime

TELEGRAM_FILES = {
    "services/notifications/telegram_service.py": '''import requests
import logging
from utils.logger import logger
from domain.models import MarketData
from typing import List

class TelegramService:
    def __init__(self, token: str = None, chat_id: str = None):
        # In produzione, usa variabili d'ambiente o un file .env
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        
        if not self.token or not self.chat_id:
            logger.warning("⚠️ Token o Chat ID mancanti. Le notifiche Telegram saranno disattivate.")

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Invia un messaggio formattato su Telegram."""
        if not self.token: return False
        
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info(f"📤 Notifica Telegram inviata con successo.")
            return True
        except Exception as e:
            logger.error(f"❌ Errore invio Telegram: {e}")
            return False

    def send_ticket_alert(self, ticket_name: str, markets: List[MarketData], total_quota: float):
        """Formatta e invia una nuova schedina certificata."""
        header = f"🎯 *NUOVA SCHEDINA CERTIFICATA: {ticket_name}*\n"
        body = ""
        for m in markets:
            body += f"🔹 {m.market_name} @ `{m.quota}` (Edge: {m.edge:.2%})\n"
        
        footer = f"\n💰 *Quota Totale:* `{total_quota:.2f}x`\n🛡️ *Validata da StrictTicketPipeline*"
        
        full_message = header + body + footer
        self.send_message(full_message)

    def send_siege_alert(self, match_info: str, opportunities: List[MarketData]):
        """Invia un'allerta urgente dal Siege Engine."""
        header = f"🚨 *ALLERTA ASSEDIO LIVE!* 🚨\n🏟️ {match_info}\n"
        body = ""
        for opp in opportunities:
            body += f"⚡ {opp.market_name} @ `{opp.quota}`\n"
        
        self.send_message(header + body)
''',

    "config/settings_example.py": '''# Esempio di configurazione per le variabili d'ambiente
# Rinomina questo file in settings.py e inserisci i tuoi dati reali

TELEGRAM_BOT_TOKEN = "IL_TUO_TOKEN_QUI"
TELEGRAM_CHAT_ID = "LA_TUA_CHAT_ID_QUI"
FOOTYSTATS_API_KEY = "LA_TUA_API_KEY_QUI"
DB_PATH = "storage/bagent.db"
''',

    "scripts/start_telegram_poller.py": '''import time
from services.notifications.telegram_service import TelegramService
from services.live.siege_engine import SiegeEngine
from utils.logger import logger

def main():
    logger.info("🤖 Avvio del Telegram Poller & Live Monitor...")
    bot = TelegramService()
    engine = SiegeEngine()
    
    # Simulazione di un ciclo di monitoraggio live
    while True:
        # Qui andrebbe la logica reale di fetching dei match live
        # Per demo, simuliamo un trigger di assedio
        logger.info("🔍 Scansione match live in corso...")
        
        # Esempio: se ci fosse un match in assedio
        # opportunities = engine.check_siege_trigger(...)
        # if opportunities:
        #     bot.send_siege_alert("Real Madrid vs Underdog", opportunities)
            
        time.sleep(60) # Polling ogni 60 secondi come da Regola

if __name__ == "__main__":
    main()
'''
}

def main():
    print("📱 Avvio di BAgent Auto-Telegram Tool v1.0...")
    
    backup_dir = Path(f"backup_telegram_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)

    for relative_path, content in TELEGRAM_FILES.items():
        file_path = Path(relative_path)
        if file_path.exists():
            shutil.copy2(file_path, backup_dir / relative_path.replace("/", "_"))
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Creato modulo Telegram: {relative_path}")

    print("\n" + "="*60)
    print("📲 INTEGRAZIONE TELEGRAM COMPLETATA!")
    print("="*60)
    print("Per attivare il bot:")
    print("1. Crea un bot su Telegram con @BotFather e ottieni il Token.")
    print("2. Ottieni la tua Chat ID (puoi usare @userinfobot).")
    print("3. Inseriscili in config/settings.py (copia da settings_example.py).")
    print("4. Esegui: python scripts/start_telegram_poller.py")
    print("="*60)

if __name__ == "__main__":
    main()
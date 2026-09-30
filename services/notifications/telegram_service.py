import requests
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
        header = f"🎯 *NUOVA SCHEDINA CERTIFICATA: {ticket_name}*
"
        body = ""
        for m in markets:
            body += f"🔹 {m.market_name} @ `{m.quota}` (Edge: {m.edge:.2%})
"
        
        footer = f"
💰 *Quota Totale:* `{total_quota:.2f}x`
🛡️ *Validata da StrictTicketPipeline*"
        
        full_message = header + body + footer
        self.send_message(full_message)

    def send_siege_alert(self, match_info: str, opportunities: List[MarketData]):
        """Invia un'allerta urgente dal Siege Engine."""
        header = f"🚨 *ALLERTA ASSEDIO LIVE!* 🚨
🏟️ {match_info}
"
        body = ""
        for opp in opportunities:
            body += f"⚡ {opp.market_name} @ `{opp.quota}`
"
        
        self.send_message(header + body)

from __future__ import annotations
import os
import re
import requests
import logging
from typing import List

from services.telegram.credentials import get_telegram_credentials
from domain.models import MarketData

logger = logging.getLogger("TelegramService")

EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff]"
    r"|[\u2600-\u26ff]"
    r"|[\u2700-\u27bf]"
    r"|[\u2300-\u23ff]"
    r"|[\u2b50-\u2b55]"
    r"|[\u200d\ufe0f]"
    , flags=re.UNICODE
)


def clean_telegram_text(text: str) -> str:
    """Rimuove rigorosamente qualsiasi emoji e simbolo decorativo dal testo."""
    if not text:
        return ""
    cleaned = EMOJI_PATTERN.sub("", text)
    cleaned = cleaned.replace("━", "-").replace("👉", "->").replace("👇", "").replace("•", "-")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


class TelegramService:
    def __init__(self, token: str = None, chat_id: str = None):
        resolved_token, resolved_chat = get_telegram_credentials(token, chat_id)
        self.token = resolved_token
        self.chat_id = resolved_chat
        self.base_url = f"https://api.telegram.org/bot{self.token}"

        if not self.token or not self.chat_id:
            logger.warning("Token o Chat ID mancanti. Le notifiche Telegram saranno disattivate.")

    def send_message(self, text: str, parse_mode: str = "Markdown") -> bool:
        """Invia un messaggio formattato su Telegram senza emoji."""
        if not self.token or not self.chat_id:
            return False

        cleaned = clean_telegram_text(text)
        if not cleaned:
            return False

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": cleaned,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Notifica Telegram inviata con successo.")
            return True
        except Exception as e:
            logger.error(f"Errore invio Telegram: {e}")
            return False

    def send_ticket_alert(self, ticket_name: str, markets: List[MarketData], total_quota: float):
        """Formatta e invia una nuova schedina certificata."""
        header = f"*NUOVA SCHEDINA CERTIFICATA: {ticket_name}*\n\n"
        body = ""
        for m in markets:
            body += f"- {m.market_name} @ `{m.quota}` (Edge: {m.edge:.2%})\n"

        footer = f"\n*Quota Totale:* `{total_quota:.2f}x`\n*Validata da StrictTicketPipeline*"
        full_message = header + body + footer
        self.send_message(full_message)

    def send_siege_alert(self, match_info: str, opportunities: List[MarketData]):
        """Invia un'allerta urgente dal Siege Engine."""
        header = f"*ALLERTA ASSEDIO LIVE*\nPartita: {match_info}\n\n"
        body = ""
        for opp in opportunities:
            body += f"- {opp.market_name} @ `{opp.quota}`\n"

        self.send_message(header + body)

"""
Telegram Interactive Bot — Gestore 1-Click Approval & Callback Dispatcher
Ascolta i clic sui pulsanti inline di Telegram ed esegue l'automazione Netwin
in tempo reale, restituendo ricevute e codici di prenotazione.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any, Optional

import requests

from services.betting.netwin_automator import NetwinAutomator
from services.telegram.credentials import get_telegram_credentials

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("TelegramInteractiveBot")


class TelegramInteractiveBot:
    """
    Bot Telegram con supporto a Inline Keyboards e ascolto long-polling di CallbackQuery.
    """

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token, self.chat_id = get_telegram_credentials(token, chat_id)
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.running = False
        self._last_update_id = 0
        self.ticket_registry: dict[str, dict] = {}

    def register_ticket(self, ticket_id: str, selections: list[dict], stake: float, bet_mode: str = "MULTIPLE"):
        """Registra un ticket in memoria per l'esecuzione tramite callback."""
        self.ticket_registry[ticket_id] = {
            "selections": selections,
            "stake": stake,
            "bet_mode": bet_mode,
            "status": "PENDING",
        }
        logger.info(f"Ticket #{ticket_id} registrato nel bot Telegram.")

    def send_ticket_with_buttons(self, ticket_id: str, card_text: str, stake: float):
        """Invia su Telegram una scheda ticket con pulsanti interattivi 1-Click."""
        reply_markup = {
            "inline_keyboard": [
                [
                    {
                        "text": f"🟢 PIAZZA ORA SU NETWIN ({stake:.2f} €)",
                        "callback_data": f"place_{ticket_id}",
                    }
                ],
                [
                    {
                        "text": "📋 GENERA CODICE PRENOTAZIONE",
                        "callback_data": f"book_{ticket_id}",
                    },
                    {
                        "text": "❌ ANNULLA",
                        "callback_data": f"cancel_{ticket_id}",
                    }
                ]
            ]
        }

        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": card_text,
            "parse_mode": "HTML",
            "reply_markup": reply_markup,
        }

        try:
            r = requests.post(url, json=payload, timeout=12)
            if r.status_code == 200:
                logger.info(f"Scheda interattiva inviata per Ticket #{ticket_id}")
            else:
                logger.warning(f"Errore invio Telegram: {r.status_code} - {r.text}")
        except Exception as e:
            logger.error(f"Errore invio messaggio interattivo: {e}")

    def answer_callback(self, callback_query_id: str, text: str = "", show_alert: bool = False):
        """Risponde al callback per rimuovere lo stato di caricamento dal pulsante Telegram."""
        url = f"{self.base_url}/answerCallbackQuery"
        try:
            requests.post(
                url,
                json={
                    "callback_query_id": callback_query_id,
                    "text": text,
                    "show_alert": show_alert,
                },
                timeout=6,
            )
        except Exception as e:
            logger.debug(f"Errore answerCallbackQuery: {e}")

    def edit_message(self, message_id: int, new_text: str, remove_buttons: bool = True):
        """Aggiorna il testo di un messaggio Telegram per mostrare l'avanzamento."""
        url = f"{self.base_url}/editMessageText"
        payload = {
            "chat_id": self.chat_id,
            "message_id": message_id,
            "text": new_text,
            "parse_mode": "HTML",
        }
        if not remove_buttons:
            # Mantieni o aggiorna tastiera se necessario
            pass

        try:
            requests.post(url, json=payload, timeout=8)
        except Exception as e:
            logger.debug(f"Errore editMessageText: {e}")

    def send_photo(self, photo_path: str, caption: str = ""):
        """Invia uno screenshot o immagine della ricevuta scommessa."""
        url = f"{self.base_url}/sendPhoto"
        try:
            with open(photo_path, "rb") as f:
                requests.post(
                    url,
                    data={"chat_id": self.chat_id, "caption": caption, "parse_mode": "HTML"},
                    files={"photo": f},
                    timeout=20,
                )
            logger.info(f"Ricevuta fotografica inviata su Telegram: {photo_path}")
        except Exception as e:
            logger.error(f"Errore invio foto: {e}")

    def handle_callback_query(self, query: dict):
        """Elabora il clic dell'utente su un pulsante inline."""
        query_id = query.get("id")
        data = query.get("data", "")
        message = query.get("message", {})
        message_id = message.get("message_id")
        orig_text = message.get("text", "")

        logger.info(f"Pulsante premuto: '{data}'")

        if data.startswith("place_"):
            ticket_id = data.replace("place_", "")
            self.answer_callback(
                query_id,
                text="📋 Prenotazione (niente soldi): genero il codice a 6 cifre...",
            )
            self.edit_message(
                message_id,
                f"{orig_text}\n\n⏳ <b>GENERAZIONE CODICE PRENOTAZIONE IN CORSO...</b>",
            )
            threading.Thread(
                target=self._execute_booking,
                args=(ticket_id, message_id, orig_text),
                daemon=True,
            ).start()

        elif data.startswith("book_"):
            ticket_id = data.replace("book_", "")
            self.answer_callback(query_id, text="📋 Generazione codice di prenotazione...")
            self.edit_message(message_id, f"{orig_text}\n\n⏳ <b>GENERAZIONE CODICE PRENOTAZIONE IN CORSO...</b>")

            threading.Thread(
                target=self._execute_booking,
                args=(ticket_id, message_id, orig_text),
                daemon=True,
            ).start()

        elif data.startswith("cancel_"):
            self.answer_callback(query_id, text="❌ Operazione annullata.")
            self.edit_message(message_id, f"{orig_text}\n\n❌ <i>Piazzamento annullato dall'utente.</i>")

    def _execute_booking(self, ticket_id: str, message_id: int, orig_text: str):
        """Worker: carrello completo + codice prenotazione a 6 cifre (niente soldi)."""
        ticket = self.ticket_registry.get(ticket_id)
        if not ticket:
            self.edit_message(message_id, f"{orig_text}\n\n⚠️ <i>Errore: Ticket scaduto o non trovato.</i>")
            return

        automator = NetwinAutomator(headless=True)
        try:
            res = automator.build_ticket_and_book(
                selections=ticket["selections"],
                stake=ticket["stake"],
            )
            code = res.get("booking_code")
            complete = (
                res.get("success")
                and code
                and res.get("events_added") == res.get("total_events")
            )
            if complete:
                code_msg = (
                    f"{orig_text}\n\n"
                    f"📋 <b>CODICE PRENOTAZIONE NETWIN GENERATO!</b>\n"
                    f"🔑 <b>Codice</b>: <code>{code}</code>\n"
                    f"📊 Eventi: <b>{res.get('events_added')}/{res.get('total_events')}</b>\n\n"
                    f"💡 <i>Caricalo su Netwin → Schedina → Codice → Carica. Nessun importo è stato giocato.</i>"
                )
                self.edit_message(message_id, code_msg)
            else:
                self.edit_message(
                    message_id,
                    f"{orig_text}\n\n⚠️ <i>Impossibile estrarre il codice: {res.get('error')}</i>",
                )
        except Exception as e:
            logger.error("Errore generazione codice: %s", e)
            self.edit_message(message_id, f"{orig_text}\n\n❌ <i>Errore: {e}</i>")

    def start_polling(self):
        """Avvia il loop di ascolto continuo per i pulsanti Telegram."""
        self.running = True
        logger.info(f"=== Telegram Interactive Listener Avviato (@A502502_bot) ===")

        while self.running:
            try:
                url = f"{self.base_url}/getUpdates"
                params = {"offset": self._last_update_id + 1, "timeout": 25}
                r = requests.get(url, params=params, timeout=30)
                
                if r.status_code == 200:
                    data = r.json()
                    updates = data.get("result", [])
                    for u in updates:
                        self._last_update_id = u.get("update_id", self._last_update_id)
                        if "callback_query" in u:
                            self.handle_callback_query(u["callback_query"])
                time.sleep(1)
            except Exception as e:
                logger.debug(f"Polling warning: {e}")
                time.sleep(3)


if __name__ == "__main__":
    bot = TelegramInteractiveBot()
    bot.start_polling()

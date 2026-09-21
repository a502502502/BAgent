"""
services/telegram/telegram_sentinel.py — Notifiche Push Telegram Bidirezionali (Pilastro 3).

Gestisce l'invio proattivo di:
- Master Ticket con tastiera inline per approvazione 1-Click
- Esecuzione automatica in background di NetwinAutomator al tocco del pulsante
- Alert In-Play dedicati (Bagel collapse, Red cards, Chiusure matematiche Lock Over)
- Supporta sia chiamate HTTP native (requests) che python-telegram-bot se presente.
"""

from __future__ import annotations
import os
import time
import uuid
import json
import logging
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests

logger = logging.getLogger("TelegramSentinel")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")


class TelegramSentinel:
    """
    Dispatcher centralizzato di notifiche push e listener per approvazioni 1-click su smartphone.
    """

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or TELEGRAM_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        
        # Registro dei ticket attivi in attesa di approvazione
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self._is_listening = False

    def send_message(self, text: str, parse_mode: str = "HTML", reply_markup: Optional[Dict[str, Any]] = None) -> bool:
        """Invia un messaggio di testo formattato con eventuale tastiera inline."""
        if not self.token or not self.chat_id:
            logger.warning("Telegram Token o Chat ID mancanti.")
            return False
        
        payload: Dict[str, Any] = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            resp = requests.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
            if resp.status_code == 200:
                logger.info("Notifica Telegram inviata con successo.")
                return True
            logger.error(f"Errore Telegram ({resp.status_code}): {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Eccezione durante l'invio Telegram: {e}")
            return False

    def send_master_ticket(
        self,
        ticket_name: str,
        selections: List[Dict[str, Any]],
        total_odds: float,
        stake_eur: float,
        potential_win_eur: float,
        bankroll_current: float,
        notes: str = ""
    ) -> bool:
        """Invia la scheda completa del Master Ticket con pulsanti 1-Click."""
        ticket_id = str(uuid.uuid4())[:8]
        
        self.active_tickets[ticket_id] = {
            "id": ticket_id,
            "name": ticket_name,
            "selections": selections,
            "stake": stake_eur,
            "total_odds": total_odds,
            "potential_win": potential_win_eur
        }

        lines = [
            f"🎟️ <b>BAGENT — MASTER TICKET CERTIFICATO</b>",
            f"📌 <b>{ticket_name.upper()}</b> [ID: <code>{ticket_id}</code>]",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]

        for idx, sel in enumerate(selections, 1):
            match = sel.get("match", "Partita")
            market = sel.get("market", "Mercato")
            odd = sel.get("netwin_odds") or sel.get("odd", 1.0)
            edge = sel.get("edge_pct", 0.0)
            tournament = sel.get("tournament", "")
            lines.append(f"<b>{idx}. {match}</b> ({tournament})")
            lines.append(f"   🎯 <i>{market}</i> @ <b>{odd:.2f}</b> [Edge: +{edge:.1f}%]")

        lines.extend([
            f"━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📊 <b>Quota Totale:</b> <code>@{total_odds:.2f}</code>",
            f"💰 <b>Puntata (Kelly):</b> <code>€ {stake_eur:.2f}</code> (Bankroll: €{bankroll_current:.2f})",
            f"🏆 <b>Vincita Potenziale:</b> <code>€ {potential_win_eur:.2f}</code>",
            f"🛡️ <i>Tutti gli eventi hanno superato gli Hard Gates di BAgent</i>"
        ])

        if notes:
            lines.append(f"\n💡 <i>{notes}</i>")

        # Tastiera Inline 1-Click
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "🚀 PRENOTA SU NETWIN", "callback_data": f"book_ticket_{ticket_id}"},
                    {"text": "❌ IGNORA", "callback_data": f"ignore_ticket_{ticket_id}"}
                ]
            ]
        }

        return self.send_message("\n".join(lines), reply_markup=reply_markup)

    # =========================================================================
    # 🚨 LIVE ALERTS (Integrazione LiveMomentumSentinel)
    # =========================================================================

    def send_bagel_alert(self, match: str, player_down: str, comeback_prob: float, surface: str = "clay"):
        """Alert per crollo post-bagel (6-0/0-6) nel tennis."""
        text = (
            f"🚨 <b>ALLERTA BAGEL / CROLLO TENNIS</b>\n\n"
            f"🎾 <b>{match}</b> ({surface.capitalize()})\n"
            f"⚠️ <b>{player_down}</b> ha subito un 6-0 o 0-6.\n"
            f"📉 Probabilità di rimonta stimata: <b>{comeback_prob:.1%}</b>\n\n"
            f"💡 <i>Valutare live sniping sul favorito o hedge se in posizione.</i>"
        )
        return self.send_message(text)

    def send_red_card_alert(self, match: str, team_with_red: str, minute: int, xg_home_adj: float, xg_away_adj: float):
        """Alert per cartellino rosso nel calcio con xG ricalcolati."""
        text = (
            f"🟥 <b>ALLERTA ESPULSIONE LIVE</b>\n\n"
            f"⚽ <b>{match}</b> al {minute}'\n"
            f"⚠️ Cartellino rosso per: <b>{team_with_red}</b>\n"
            f"📊 Rate xG Ricalibrati: Casa {xg_home_adj:.2f} - Ospite {xg_away_adj:.2f}\n\n"
            f"💡 <i>Opportunità di sniping su favorito sotto o Under in-play.</i>"
        )
        return self.send_message(text)

    def send_lock_alert(self, match: str, bet_type: str, current_state: str, message: str):
        """Alert per chiusura matematica anticipata (es. Over 18.5 al 1° set)."""
        text = (
            f"🔒 <b>CHIUSURA MATEMATICA RILEVATA (CASSA GARANTITA)</b>\n\n"
            f"📌 <b>{match}</b>\n"
            f"🎯 Giocata: <b>{bet_type}</b>\n"
            f"📊 Stato attuale: <code>{current_state}</code>\n\n"
            f"✅ <i>{message}</i>"
        )
        return self.send_message(text)

    # =========================================================================
    # ⚙️ LISTENER AUTOMATICO 1-CLICK (HTTP Polling nativo)
    # =========================================================================

    def _execute_netwin_booking_sync(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue NetwinAutomator in background per prenotare il ticket."""
        from services.betting.netwin_automator import NetwinAutomator
        automator = NetwinAutomator(headless=True)
        try:
            build_result = automator.build_ticket(
                selections=ticket_data["selections"],
                bet_mode="MULTIPLE",
                fixed_stake=ticket_data.get("stake", 10.0)
            )
            if not build_result.get("success"):
                return {"success": False, "error": build_result.get("error", "Impossibile comporre il carrello")}

            booking_result = automator.generate_booking_code()
            if booking_result.get("success"):
                return {
                    "success": True,
                    "booking_code": booking_result["booking_code"],
                    "total_odds": build_result.get("total_odds", "N/A"),
                    "applied_stake": build_result.get("applied_stake", ticket_data.get("stake", 10.0))
                }
            else:
                return {"success": False, "error": booking_result.get("error", "Codice prenotazione non generato")}
        except Exception as e:
            logger.error(f"Errore prenotazione Netwin: {e}")
            return {"success": False, "error": str(e)}
        finally:
            automator.close()

    def _process_callback_query(self, query: Dict[str, Any]):
        """Gestisce il click sui bottoni inline da parte dell'utente."""
        query_id = query.get("id")
        data = query.get("data", "")
        message = query.get("message", {})
        message_id = message.get("message_id")
        chat_id = message.get("chat", {}).get("id", self.chat_id)

        # Rispondi subito alla callback per togliere l'animazione di caricamento
        requests.post(f"{self.api_url}/answerCallbackQuery", json={"callback_query_id": query_id}, timeout=5)

        if data.startswith("ignore_ticket_"):
            ticket_id = data.replace("ignore_ticket_", "")
            self.active_tickets.pop(ticket_id, None)
            requests.post(
                f"{self.api_url}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": "❌ <b>Ticket ignorato e rimosso dalla coda.</b>",
                    "parse_mode": "HTML"
                },
                timeout=5
            )
            return

        if data.startswith("book_ticket_"):
            ticket_id = data.replace("book_ticket_", "")
            ticket_data = self.active_tickets.get(ticket_id)

            if not ticket_data:
                requests.post(
                    f"{self.api_url}/editMessageText",
                    json={
                        "chat_id": chat_id,
                        "message_id": message_id,
                        "text": "⚠️ <b>Ticket scaduto o già elaborato.</b>",
                        "parse_mode": "HTML"
                    },
                    timeout=5
                )
                return

            # Feedback immediato su Telegram
            requests.post(
                f"{self.api_url}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": (
                        f"🔄 <b>Elaborazione in corso...</b>\n\n"
                        f"Sto avviando NetwinAutomator per il ticket: <code>{ticket_data['name']}</code>.\n"
                        f"Attendi circa 10-15 secondi per l'interazione con il browser Netwin."
                    ),
                    "parse_mode": "HTML"
                },
                timeout=5
            )

            # Esecuzione Playwright in background
            res = self._execute_netwin_booking_sync(ticket_data)

            if res.get("success"):
                confirm_text = (
                    f"✅ <b>PRENOTAZIONE AVVENUTA CON SUCCESSO!</b>\n\n"
                    f"🎟️ <b>Codice Prenotazione Netwin:</b> <code>{res['booking_code']}</code>\n"
                    f"📊 Quota Totale: <code>@{res['total_odds']}</code>\n"
                    f"💰 Stake Applicato: <code>€ {res['applied_stake']:.2f}</code>\n\n"
                    f"📸 Ricevuta e log salvati nella cartella <code>reports/receipts</code>."
                )
            else:
                confirm_text = (
                    f"❌ <b>ERRORE PRENOTAZIONE NETWIN</b>\n\n"
                    f"Motivo: <code>{res.get('error', 'Sconosciuto')}</code>\n\n"
                    f"💡 <i>Puoi prenotare manualmente o verificare il carrello.</i>"
                )

            self.send_message(confirm_text)
            self.active_tickets.pop(ticket_id, None)

    def start_listening(self):
        """Avvia il polling dei messaggi e callback Telegram (bloccante, eseguibile in thread)."""
        logger.info("🤖 Avvio Telegram Sentinel Listener (HTTP Long-Polling)...")
        self._is_listening = True
        offset = 0

        while self._is_listening:
            try:
                resp = requests.get(f"{self.api_url}/getUpdates", params={"offset": offset, "timeout": 20}, timeout=25)
                if resp.status_code == 200:
                    data = resp.json()
                    updates = data.get("result", [])
                    for u in updates:
                        offset = u["update_id"] + 1
                        if "callback_query" in u:
                            self._process_callback_query(u["callback_query"])
                time.sleep(1)
            except Exception as e:
                logger.debug(f"Errore durante polling Telegram: {e}")
                time.sleep(3)

    def stop_listening(self):
        """Ferma il listener di polling."""
        self._is_listening = False
        logger.info("Telegram Sentinel Listener arrestato.")

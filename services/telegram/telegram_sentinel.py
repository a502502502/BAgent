"""
services/telegram/telegram_sentinel.py — Notifiche Push Telegram Bidirezionali (Pilastro 3).

Gestisce l'invio proattivo di:
- Master Ticket Certificati del giorno (con quote, motivazione Sesto Senso e calcolo Kelly);
- Alert In-Play "Protocollo Assedio" (Regola #50) quando una piccola passa in vantaggio su una big;
- Report di Chiusura Cassa e Post-Mortem.
"""

from __future__ import annotations
import os
import requests
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger("TelegramSentinel")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")

class TelegramSentinel:
    """
    Dispatcher centralizzato di notifiche push verso lo smartphone dell'utente.
    """

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token = token or TELEGRAM_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Invia un messaggio di testo formattato."""
        if not self.token or not self.chat_id:
            logger.warning("Telegram Token o Chat ID mancanti.")
            return False
        
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        try:
            resp = requests.post(self.api_url, json=payload, timeout=10)
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
        """Invia la scheda completa del Master Ticket Certificato."""
        lines = [
            f"🎟️ <b>BAGENT — MASTER TICKET CERTIFICATO</b>",
            f"📌 <b>{ticket_name.upper()}</b>",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━"
        ]

        for idx, sel in enumerate(selections, 1):
            match = sel.get("match", "Partita")
            market = sel.get("market", "Mercato")
            odd = sel.get("odd", 1.0)
            edge = sel.get("edge", 0.0)
            tournament = sel.get("tournament", "")
            lines.append(f"<b>{idx}. {match}</b> ({tournament})")
            lines.append(f"   🎯 <i>{market}</i> @ <b>{odd:.2f}</b> [Edge: +{edge*100:.1f}%]")

        lines.extend([
            f"━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📊 <b>Quota Totale:</b> <code>@{total_odds:.2f}</code>",
            f"💰 <b>Puntata Consigliata:</b> <code>€ {stake_eur:.2f}</code> (Bankroll: €{bankroll_current:.2f})",
            f"🏆 <b>Vincita Potenziale:</b> <code>€ {potential_win_eur:.2f}</code>",
            f"🛡️ <i>Tutti gli eventi hanno superato gli 8 Hard Gates di BAgent</i>"
        ])

        if notes:
            lines.append(f"\n💡 <i>{notes}</i>")

        return self.send_message("\n".join(lines))

    def send_siege_alert(
        self,
        match_name: str,
        minute: int,
        score: str,
        underdog: str,
        favorite: str,
        recommended_markets: List[Dict[str, Any]]
    ) -> bool:
        """Invia l'allerta immediata 'Protocollo Assedio' (Regola #50)."""
        lines = [
            f"🚨 <b>ALLERTA PROTOCOLLO ASSEDIO (Regola #50)</b>",
            f"🏟️ <b>{match_name}</b>",
            f"⏱️ Minuto: <b>{minute}'</b> | Risultato: <b>{score}</b>",
            f"⚠️ <i>La sfavorita ({underdog}) è passata in vantaggio sulla big ({favorite})!</i>",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🔥 <b>MERCATI ASIMMETRICI ATTIVATI:</b>"
        ]

        for m in recommended_markets:
            market_name = m.get("name", "")
            odd = m.get("odd", 1.0)
            desc = m.get("desc", "")
            lines.append(f"• <b>{market_name}</b> @ <code>{odd:.2f}</code> ({desc})")

        lines.extend([
            f"━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"⚡ <i>Entra su Netwin e valuta l'ingresso in-play!</i>"
        ])

        return self.send_message("\n".join(lines))

    def send_post_mortem_report(
        self,
        ticket_id: str,
        outcome: str,
        profit_loss: float,
        new_balance: float,
        lessons: List[str]
    ) -> bool:
        """Invia il report post-partita con bilancio e apprendimento tattico."""
        emoji = "🎉" if outcome == "WON" else "📉"
        lines = [
            f"{emoji} <b>BAGENT — REPORT CHIUSURA TICKET #{ticket_id}</b>",
            f"Esito Finale: <b>{outcome}</b>",
            f"Variazione Netta: <b>€ {profit_loss:+.2f}</b>",
            f"Nuovo Saldo Bankroll: <b>€ {new_balance:.2f}</b>",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🧠 <b>LEZIONI TATTICHE POST-MORTEM:</b>"
        ]

        for l in lessons:
            lines.append(f"• <i>{l}</i>")

        return self.send_message("\n".join(lines))

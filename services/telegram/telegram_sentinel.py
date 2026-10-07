"""
services/telegram/telegram_sentinel.py — Notifiche Push Telegram Bidirezionali (Pilastro 3).

Gestisce l'invio proattivo di:
- Master Ticket con tastiera inline per approvazione 1-Click
- Esecuzione automatica in background di NetwinAutomator al tocco del pulsante
- Alert In-Play dedicati (Bagel collapse, Red cards, Chiusure matematiche Lock Over)
- Supporta sia chiamate HTTP native (requests) che python-telegram-bot se presente.

Regole applicate:
- Rigorosamente nessun emoji o simbolo decorativo nei messaggi Telegram e nei log.
- Filtro anti-flood e deduplicazione automatica dei messaggi.
- Sanitizzazione forzata di qualsiasi testo prima dell'invio.
"""

from __future__ import annotations
import os
import time
import uuid
import json
import re
import logging
import threading
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests

from services.telegram.credentials import get_telegram_credentials

logger = logging.getLogger("TelegramSentinel")

EMOJI_PATTERN = re.compile(
    r"[\U00010000-\U0010ffff]"  # Supplemental Multilingual Plane (emojis)
    r"|[\u2600-\u26ff]"          # Misc symbols
    r"|[\u2700-\u27bf]"          # Dingbats
    r"|[\u2300-\u23ff]"          # Misc Technical
    r"|[\u2b50-\u2b55]"          # Stars and symbols
    r"|[\u200d\ufe0f]"           # Zero-width joiner, emoji presentation
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


class TelegramSentinel:
    """
    Dispatcher centralizzato di notifiche push e listener per approvazioni 1-click su smartphone.
    """

    def __init__(self, token: Optional[str] = None, chat_id: Optional[str] = None):
        self.token, self.chat_id = get_telegram_credentials(token, chat_id)
        self.api_url = f"https://api.telegram.org/bot{self.token}"
        self.session = requests.Session()
        
        # Registro dei ticket attivi in attesa di approvazione
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self._is_listening = False
        self._recent_messages: Dict[str, float] = {}
        self._dedup_window_seconds = 60.0

    def send_message(
        self,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict[str, Any]] = None,
        chat_id: Optional[str] = None
    ) -> bool:
        """Invia un messaggio di testo formattato con tastiera inline facoltativa ed elimina gli emoji."""
        target_chat = chat_id or self.chat_id
        if not self.token or not target_chat:
            logger.warning("Telegram Token o Chat ID mancanti.")
            return False

        cleaned_text = clean_telegram_text(text)
        if not cleaned_text:
            return False

        now = time.time()
        dedup_key = f"{target_chat}:{cleaned_text[:120]}"
        last_sent = self._recent_messages.get(dedup_key, 0.0)
        if (now - last_sent) < self._dedup_window_seconds:
            logger.info("Messaggio duplicato recente scartato dalla sentinella anti-flood.")
            return False

        if len(self._recent_messages) > 100:
            self._recent_messages = {
                k: v for k, v in self._recent_messages.items() if (now - v) < self._dedup_window_seconds
            }

        payload: Dict[str, Any] = {
            "chat_id": target_chat,
            "text": cleaned_text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            resp = self.session.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
            if resp.status_code == 200:
                self._recent_messages[dedup_key] = now
                logger.info("Notifica Telegram inviata con successo.")
                return True
            logger.error(f"Errore Telegram ({resp.status_code}): {resp.text}")
            return False
        except Exception as e:
            logger.error(f"Eccezione durante invio Telegram: {e}")
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
            "BAGENT — MASTER TICKET CERTIFICATO",
            f"{ticket_name.upper()} [ID: <code>{ticket_id}</code>]",
            "-----------------------------------------"
        ]

        for idx, sel in enumerate(selections, 1):
            match = sel.get("match", "Partita")
            market = sel.get("market", "Mercato")
            odd = sel.get("netwin_odds") or sel.get("odd", 1.0)
            edge = sel.get("edge_pct", 0.0)
            tournament = sel.get("tournament", "")
            lines.append(f"<b>{idx}. {match}</b> ({tournament})")
            lines.append(f"   <i>{market}</i> @ <b>{odd:.2f}</b> [Edge: +{edge:.1f}%]")

        lines.extend([
            "-----------------------------------------",
            f"<b>Quota Totale:</b> <code>@{total_odds:.2f}</code>",
            f"<b>Puntata (Kelly):</b> <code>EUR {stake_eur:.2f}</code> (Bankroll: EUR {bankroll_current:.2f})",
            f"<b>Vincita Potenziale:</b> <code>EUR {potential_win_eur:.2f}</code>",
            "<i>Tutti gli eventi hanno superato gli Hard Gates di BAgent</i>"
        ])

        if notes:
            lines.append(f"\n<i>{notes}</i>")

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "PRENOTA SU NETWIN", "callback_data": f"book_ticket_{ticket_id}"},
                    {"text": "IGNORA", "callback_data": f"ignore_ticket_{ticket_id}"}
                ]
            ]
        }

        return self.send_message("\n".join(lines), reply_markup=reply_markup)

    def send_red_card_alert(self, match: str, team_with_red: str, minute: int, xg_home_adj: float, xg_away_adj: float):
        """Alert per cartellino rosso nel calcio con xG ricalcolati."""
        text = (
            f"ALLERTA ESPULSIONE LIVE\n\n"
            f"<b>{match}</b> al {minute}'\n"
            f"Cartellino rosso per: <b>{team_with_red}</b>\n"
            f"Rate xG Ricalibrati: Casa {xg_home_adj:.2f} - Ospite {xg_away_adj:.2f}\n\n"
            f"<i>Opportunita di sniping su favorito sotto o Under in-play.</i>"
        )
        return self.send_message(text)

    def send_lock_alert(self, match: str, bet_type: str, current_state: str, message: str):
        """Alert per chiusura matematica anticipata."""
        text = (
            f"CHIUSURA MATEMATICA RILEVATA (CASSA GARANTITA)\n\n"
            f"Partita: <b>{match}</b>\n"
            f"Giocata: <b>{bet_type}</b>\n"
            f"Stato attuale: <code>{current_state}</code>\n\n"
            f"<i>{message}</i>"
        )
        return self.send_message(text)

    def _execute_netwin_booking_sync(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Esegue NetwinAutomator v2.0 in background per prenotare il ticket e ottenere il codice."""
        from services.betting.netwin_automator import NetwinAutomator
        automator = NetwinAutomator(headless=True)
        try:
            selections = ticket_data.get("legs") or ticket_data.get("selections") or []
            stake = float(ticket_data.get("stake", 25.0))
            book_res = automator.build_ticket_and_book(selections=selections, stake=stake)
            return book_res
        except Exception as e:
            logger.error(f"Errore prenotazione Netwin: {e}")
            return {"success": False, "error": str(e)}
        finally:
            automator.close()

    def _calculate_and_send_match(self, home_team: str, away_team: str, chat_id: Optional[str] = None):
        """Calcola la partita con QuantitativeEngine e invia il pronostico formattato su Telegram."""
        from services.analysis.xg_poisson_engine import QuantitativeEngine
        target_chat = chat_id or self.chat_id

        h_lower = home_team.lower()
        a_lower = away_team.lower()

        is_arg = any(t in h_lower or t in a_lower for t in ["san lorenzo", "banfield", "estudiantes", "defensa", "boca", "river", "racing", "platense", "velez", "huracan", "lanus", "newell", "belgrano", "talleres", "central cordoba", "riestra", "sarmiento", "union", "argentinos", "tigre", "independiente", "godoy cruz"])
        is_bra = any(t in h_lower or t in a_lower for t in ["palmeiras", "atletico-mg", "galo", "botafogo", "gremio", "inter", "internacional", "vitoria", "sao paulo", "corinthians", "fortaleza", "cuiaba", "flamengo", "fluminense", "cruzeiro", "vasco", "bahia", "bragantino", "juventude", "criciuma", "atletico-go"])

        if is_arg:
            league = "Liga Profesional Argentina"
            xg_h, xg_a = 1.15, 0.73
            c_h, c_a = 4.8, 3.8
        elif is_bra:
            league = "Brasileirao Serie A"
            xg_h, xg_a = 1.65, 1.05
            c_h, c_a = 6.5, 4.8
        else:
            league = "Calcio Internazionale"
            xg_h, xg_a = 1.40, 1.00
            c_h, c_a = 5.2, 4.2

        qe = QuantitativeEngine(rho=-0.05)
        mat = qe.generate_score_matrix(xg_h, xg_a)

        import numpy as np
        gr = np.arange(mat.shape[0])
        grid = gr[:, None] + gr[None, :]

        p1 = float(np.tril(mat, -1).sum())
        px = float(np.diag(mat).sum())
        p2 = float(np.triu(mat, 1).sum())
        p1x = p1 + px

        pu25 = float(np.sum(mat[grid < 2.5]))
        po25 = float(np.sum(mat[grid > 2.5]))
        pu35 = float(np.sum(mat[grid < 3.5]))

        mask_1x_u35 = (gr[:, None] >= gr[None, :]) & (grid < 3.5)
        p1x_u35 = float(np.sum(mat[mask_1x_u35]))

        res_c = qe.analyze_corners(home_team, away_team, c_h, c_a, dispersion_factor=1.5)
        po85c = res_c["corner_markets"]["Over 8.5 Corner Totali"]["prob"]
        po75c = round(min(0.92, po85c + 0.08), 3)

        scores = []
        for i in range(7):
            for j in range(7):
                scores.append((f"{i}-{j}", mat[i][j]))
        scores.sort(key=lambda x: x[1], reverse=True)

        from services.odds.live_odds_service import LiveOddsService
        odds_svc = LiveOddsService()
        real_match_data = odds_svc.find_match_odds(home_team, away_team)
        real_odds = real_match_data.get("odds", {}) if real_match_data else {}

        if is_arg:
            best_val_name = "1X + Under 3.5 Gol"
            best_val_prob = p1x_u35
            best_safe_name = "Under 3.5 Gol"
            best_safe_prob = pu35
            real_val_odd = real_odds.get("Under 3.5", 0.0)
            real_safe_odd = real_odds.get("Under 3.5", 0.0)
        elif is_bra:
            best_val_name = "Over 7.5 Corner Totali"
            best_val_prob = po75c
            best_safe_name = "1X (Doppia Chance)"
            best_safe_prob = p1x
            real_val_odd = 0.0
            real_safe_odd = real_odds.get("1X", 0.0)
        else:
            best_val_name = "1X + Under 3.5 Gol"
            best_val_prob = p1x_u35
            best_safe_name = "Under 3.5 Gol"
            best_safe_prob = pu35
            real_val_odd = real_odds.get("Under 3.5", 0.0)
            real_safe_odd = real_odds.get("Under 3.5", 0.0)

        fair_val = round(1.0 / max(0.01, best_val_prob), 2)
        fair_safe = round(1.0 / max(0.01, best_safe_prob), 2)

        if real_val_odd and real_val_odd > 0:
            edge_val = (real_val_odd * best_val_prob) - 1.0
            edge_val_str = f"Edge Reale: <b>{'+' if edge_val>0 else ''}{edge_val*100:.1f}%</b> ({'EV+' if edge_val>0 else 'EV-'})"
            val_odd_display = f"Quota Reale: <b>@{real_val_odd:.2f}</b> (Equa: @{fair_val:.2f})"
            b = real_val_odd - 1.0
            kelly_pct = max(0.0, (b * best_val_prob - (1.0 - best_val_prob)) / max(0.01, b)) * 0.25
            kelly_str = f"{kelly_pct*100:.1f}% Bankroll (Kelly 25%)" if kelly_pct > 0 else "NO BET (Quota troppo bassa)"
        else:
            edge_val_str = "Quota Equa Minima: <b>@" + f"{fair_val:.2f}</b>"
            val_odd_display = f"Quota Equa (Fair): <b>@{fair_val:.2f}</b>"
            kelly_str = "Valutare con quota reale bookmaker"

        lines = [
            "<b>ANALISI QUANTITATIVA BAGENT</b>",
            f"<b>{home_team.upper()} vs {away_team.upper()}</b>",
            f"<i>{league}</i>",
            "-----------------------------------------",
            "<b>MIGLIOR GIOCATA A VALORE:</b>",
            f"Mercato: <b>{best_val_name}</b>",
            f"{val_odd_display}",
            f"Probabilita Reale: <b>{best_val_prob*100:.1f}%</b>",
            f"{edge_val_str}",
            f"Stake Consigliato: <b>{kelly_str}</b>",
            "",
            "<b>PARACADUTE PER MULTIPLA:</b>",
            f"Mercato: <b>{best_safe_name}</b> (Fair: @{fair_safe:.2f})",
            f"Safe Rate Reale: <b>{best_safe_prob*100:.1f}%</b>",
            "-----------------------------------------",
            "<b>MERCATI CHIAVE CALCOLATI:</b>",
            f"- 1: {p1*100:.1f}% | X: {px*100:.1f}% | 2: {p2*100:.1f}%",
            f"- 1X: {p1x*100:.1f}% (Fair: @{1/p1x:.2f})" + (f" | Reale: @{real_odds['1X']:.2f}" if real_odds.get('1X') else ""),
            f"- Under 2.5: {pu25*100:.1f}% | Over 2.5: {po25*100:.1f}%",
            f"- Under 3.5: {pu35*100:.1f}% (Fair: @{1/pu35:.2f})" + (f" | Reale: @{real_odds['Under 3.5']:.2f}" if real_odds.get('Under 3.5') else ""),
            f"- Over 8.5 Corner: {po85c*100:.1f}% (Fair: @{1/po85c:.2f})",
            "-----------------------------------------",
            "<b>TOP RISULTATI ESATTI:</b>",
            f"1. {scores[0][0]} ({scores[0][1]*100:.1f}%) | 2. {scores[1][0]} ({scores[1][1]*100:.1f}%) | 3. {scores[2][0]} ({scores[2][1]*100:.1f}%)"
        ]

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "Schedine Attive", "callback_data": "menu_tickets"},
                    {"text": "Menu Principale", "callback_data": "menu_main"}
                ]
            ]
        }

        self.send_message("\n".join(lines), reply_markup=reply_markup, chat_id=chat_id)

    def _send_main_menu(self, chat_id: Optional[str] = None):
        """Invia il menu principale interattivo."""
        text = (
            "<b>BAGENT — MOTORE QUANTITATIVO & QUOTE REALI</b>\n\n"
            "Tutti i mercati sono confrontati con il modello Dixon-Coles/NegBinomial "
            "per calcolare l'Edge Reale (+EV) e lo Stake Kelly (25%).\n\n"
            "1. <b>Scrivi qualsiasi match in chat:</b>\n"
            "   Esempio: <code>Dortmund vs Werder Brema</code>\n"
            "   Esempio: <code>Lens vs Lione</code>\n\n"
            "2. <b>Oppure seleziona un'opzione dal menu:</b>"
        )
        reply_markup = {
            "inline_keyboard": [
                [{"text": "Schedine Ufficiali Attive", "callback_data": "menu_tickets"}],
                [{"text": "Aggiorna Menu", "callback_data": "menu_main"}]
            ]
        }
        self.send_message(text, reply_markup=reply_markup, chat_id=chat_id)

    def _process_message(self, message: Dict[str, Any]):
        """Elabora i messaggi di testo inviati dall'utente al bot."""
        chat_id = str(message.get("chat", {}).get("id", self.chat_id))
        text = message.get("text", "").strip()

        if not text:
            return

        if text.lower() in ["/start", "/menu", "/help", "menu", "start", "aiuto"]:
            self._send_main_menu(chat_id)
            return

        lower_t = text.lower()
        if any(w in lower_t for w in ["schedin", "ticket", "weekend", "multipl", "portfolio", "bigliett", "pronostic"]):
            self._send_tickets_overview(chat_id)
            return

        if " vs " in lower_t or " - " in lower_t or lower_t.startswith("/calcola "):
            clean_t = text.replace("/calcola ", "").replace("/match ", "")
            if " vs " in clean_t.lower():
                parts = re.split(r'\s+vs\s+', clean_t, flags=re.IGNORECASE)
            elif " - " in clean_t:
                parts = clean_t.split(" - ")
            else:
                parts = clean_t.split()

            if len(parts) >= 2:
                home_team = parts[0].strip()
                away_team = parts[1].strip()
                self._calculate_and_send_match(home_team, away_team, chat_id)
                return

        self.send_message(
            f"Vuoi analizzare <b>{text}</b>?\n\n"
            f"Per calcolare un match, scrivi le due squadre separate da <b>vs</b>.\n"
            f"Esempio: <code>{text} vs Avversario</code>\n\n"
            f"Oppure seleziona un'opzione:",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "Menu Completo", "callback_data": "menu_main"}]
                ]
            }
        )

    def _send_tickets_overview(self, chat_id: Optional[str] = None):
        """Menu principale schedine con elenco dinamico dei ticket attivi correnti."""
        active_file = Path(__file__).resolve().parent.parent.parent / "data" / "active_user_tickets.json"
        active_tickets = []
        if active_file.exists():
            try:
                tickets = json.loads(active_file.read_text(encoding="utf-8"))
                active_tickets = [
                    t for t in tickets
                    if t.get("status") in ["PENDING", "WAITING_LINEUPS", "OPEN"] and not t.get("settled", False)
                ]
            except Exception:
                pass

        lines = [
            "<b>SCHEDINE UFFICIALI ATTIVE (BAGENT)</b>",
            "-----------------------------------------",
            f"Totale schedine attive in corso: {len(active_tickets)}",
            ""
        ]

        if not active_tickets:
            lines.append("Nessuna schedina attiva al momento.")
        else:
            for t in active_tickets:
                tid = t.get("ticket_id", "")
                title = t.get("title") or t.get("name") or tid
                st = t.get("status", "")
                odds = t.get("total_odds", "")
                stake = t.get("stake_eur", "")
                lines.append(f"• [{st}] <b>{title}</b>")
                lines.append(f"  ID: <code>{tid}</code> | Quota: @{odds} | Puntata: EUR {stake}")
                lines.append("")

        lines.append("Tocca un'opzione o visita il portale web per tutti i dettagli:")

        reply_markup = {
            "inline_keyboard": [
                [{"text": "Torna al Menu Principale", "callback_data": "menu_main"}]
            ]
        }
        self.send_message("\n".join(lines), reply_markup=reply_markup, chat_id=chat_id)

    def _process_callback_query(self, query: Dict[str, Any]):
        """Gestisce il click sui bottoni inline da parte dell'utente."""
        query_id = query.get("id")
        data = query.get("data", "")
        message = query.get("message", {})
        message_id = message.get("message_id")
        chat_id = str(message.get("chat", {}).get("id", self.chat_id))

        requests.post(f"{self.api_url}/answerCallbackQuery", json={"callback_query_id": query_id}, timeout=5)

        if data == "menu_main":
            self._send_main_menu(chat_id)
            return

        if data in ["menu_tickets", "tickets"]:
            self._send_tickets_overview(chat_id)
            return

        if data.startswith("calc_"):
            parts = data.replace("calc_", "").split("_")
            if len(parts) >= 2:
                self._calculate_and_send_match(parts[0], parts[1], chat_id)
                return

        if data.startswith("ignore_ticket_"):
            ticket_id = data.replace("ignore_ticket_", "")
            self.active_tickets.pop(ticket_id, None)
            requests.post(
                f"{self.api_url}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": "Ticket ignorato e rimosso dalla coda.",
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
                        "text": "Ticket scaduto o gia elaborato.",
                        "parse_mode": "HTML"
                    },
                    timeout=5
                )
                return

            requests.post(
                f"{self.api_url}/editMessageText",
                json={
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "text": (
                        f"GENERAZIONE CODICE NETWIN IN CORSO...\n\n"
                        f"Avvio NetwinAutomator per: <code>{ticket_data['name']}</code>.\n"
                        f"Attendi circa 10-15 secondi."
                    ),
                    "parse_mode": "HTML"
                },
                timeout=5
            )

            res = self._execute_netwin_booking_sync(ticket_data)

            complete = (
                res.get("success")
                and res.get("booking_code")
                and res.get("events_added") == res.get("total_events")
            )
            if complete:
                code = res["booking_code"]
                confirm_text = (
                    f"CODICE PRENOTAZIONE NETWIN GENERATO\n\n"
                    f"CODICE: <code>{code}</code>\n"
                    f"Eventi Inseriti: {res.get('events_added')} / {res.get('total_events')}\n"
                    f"Stake Applicato: EUR {res.get('stake', ticket_data.get('stake', 25.0)):.2f}\n\n"
                    f"COME CARICARE LA SCHEDINA:\n"
                    f"1. Apri Netwin.it (o app Netwin)\n"
                    f"2. Nel box Schedina 1, inserisci <code>{code}</code> nel campo Codice\n"
                    f"3. Clicca su Carica"
                )
            else:
                confirm_text = (
                    f"ERRORE PRENOTAZIONE NETWIN\n\n"
                    f"Motivo: <code>{res.get('error', 'Sconosciuto')}</code>\n\n"
                    f"Puoi verificare le quote e compilare la schedina manualmente."
                )

            self.send_message(confirm_text, chat_id=chat_id)
            self.active_tickets.pop(ticket_id, None)
            return

    def start_listening(self):
        """Avvia il polling dei messaggi e callback Telegram (bloccante, eseguibile in thread)."""
        logger.info("Avvio Telegram Sentinel Listener (HTTP Long-Polling)...")
        try:
            self.session.post(f"{self.api_url}/deleteWebhook", json={"drop_pending_updates": False}, timeout=10)
        except Exception as e:
            logger.warning(f"Errore deleteWebhook: {e}")

        self._is_listening = True
        offset = 0

        while self._is_listening:
            try:
                resp = self.session.get(f"{self.api_url}/getUpdates", params={"offset": offset, "timeout": 5}, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    updates = data.get("result", [])
                    for u in updates:
                        offset = u["update_id"] + 1
                        if "callback_query" in u:
                            logger.info(f"Ricevuta callback query: {u['callback_query'].get('data')}")
                            self._process_callback_query(u["callback_query"])
                        elif "message" in u:
                            logger.info(f"Ricevuto messaggio utente: {u['message'].get('text')}")
                            self._process_message(u["message"])
                elif resp.status_code == 409:
                    logger.warning("Conflitto 409 su getUpdates. Attesa rilascio connessione (3s)...")
                    time.sleep(3)
                else:
                    logger.warning(f"getUpdates status {resp.status_code}: {resp.text}")
                    time.sleep(2)
                time.sleep(0.3)
            except Exception as e:
                logger.debug(f"Errore durante polling Telegram: {e}")
                time.sleep(2)

    def stop_listening(self):
        """Ferma il listener di polling."""
        self._is_listening = False
        logger.info("Telegram Sentinel Listener arrestato.")

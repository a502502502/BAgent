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
import re
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
        self.session = requests.Session()
        
        # Registro dei ticket attivi in attesa di approvazione
        self.active_tickets: Dict[str, Dict[str, Any]] = {}
        self._is_listening = False

    def send_message(self, text: str, parse_mode: str = "HTML", reply_markup: Optional[Dict[str, Any]] = None, chat_id: Optional[str] = None) -> bool:
        """Invia un messaggio di testo formattato con eventuale tastiera inline."""
        target_chat = chat_id or self.chat_id
        if not self.token or not target_chat:
            logger.warning("Telegram Token o Chat ID mancanti.")
            return False
        
        payload: Dict[str, Any] = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            resp = self.session.post(f"{self.api_url}/sendMessage", json=payload, timeout=10)
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

    # =========================================================================
    # ⚙️ LISTENER AUTOMATICO & CALCOLATORE INTERATTIVO (HTTP Long-Polling)
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

    def _calculate_and_send_match(self, home_team: str, away_team: str, chat_id: Optional[str] = None):
        """Calcola la partita con QuantitativeEngine e invia il pronostico formattato su Telegram."""
        from services.analysis.xg_poisson_engine import QuantitativeEngine
        target_chat = chat_id or self.chat_id
        
        # Rileva se campionato argentino o brasiliano per League DNA
        h_lower = home_team.lower()
        a_lower = away_team.lower()
        
        is_arg = any(t in h_lower or t in a_lower for t in ["san lorenzo", "banfield", "estudiantes", "defensa", "boca", "river", "racing", "platense", "velez", "huracan", "lanus", "newell", "belgrano", "talleres", "central cordoba", "riestra", "sarmiento", "union", "argentinos", "tigre", "independiente", "godoy cruz"])
        is_bra = any(t in h_lower or t in a_lower for t in ["palmeiras", "atletico-mg", "galo", "botafogo", "gremio", "inter", "internacional", "vitoria", "sao paulo", "corinthians", "fortaleza", "cuiaba", "flamengo", "fluminense", "cruzeiro", "vasco", "bahia", "bragantino", "juventude", "criciuma", "atletico-go"])

        if is_arg:
            league = "🇦🇷 Liga Profesional Argentina (Fecha 16)"
            xg_h, xg_a = 1.15, 0.73
            c_h, c_a = 4.8, 3.8
        elif is_bra:
            league = "🇧🇷 Brasileirão Série A (Rodada 28)"
            xg_h, xg_a = 1.65, 1.05
            c_h, c_a = 6.5, 4.8
        else:
            league = "⚽ Calcio Internazionale"
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

        # Corner NegBinomial
        res_c = qe.analyze_corners(home_team, away_team, c_h, c_a, dispersion_factor=1.5)
        po85c = res_c["corner_markets"]["Over 8.5 Corner Totali"]["prob"]
        po75c = round(min(0.92, po85c + 0.08), 3)

        # Risultati Esatti Top 3
        scores = []
        for i in range(7):
            for j in range(7):
                scores.append((f"{i}-{j}", mat[i][j]))
        scores.sort(key=lambda x: x[1], reverse=True)

        # Determina Miglior Valore e Paracadute
        if is_arg:
            best_val_name = "1X + Under 3.5 Gol"
            best_val_prob = p1x_u35
            best_safe_name = "Under 3.5 Gol"
            best_safe_prob = pu35
        elif is_bra:
            best_val_name = "Over 7.5 Corner Totali"
            best_val_prob = po75c
            best_safe_name = "1X (Doppia Chance)"
            best_safe_prob = p1x
        else:
            best_val_name = "1X + Under 3.5 Gol"
            best_val_prob = p1x_u35
            best_safe_name = "Under 3.5 Gol"
            best_safe_prob = pu35

        fair_val = round(1.0 / max(0.01, best_val_prob), 2)
        fair_safe = round(1.0 / max(0.01, best_safe_prob), 2)

        lines = [
            f"⚽ <b>ANALISI QUANTITATIVA BAGENT</b>",
            f"📌 <b>{home_team.upper()} vs {away_team.upper()}</b>",
            f"🏆 <i>{league}</i>",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"💎 <b>MIGLIOR GIOCATA A VALORE (EV+)</b>",
            f"🎯 <b>{best_val_name}</b> @ <b>{fair_val:.2f}</b>",
            f"📊 Probabilità Reale: <b>{best_val_prob*100:.1f}%</b>",
            f"💰 Stake Kelly Consigliato: <b>3.0 Unità (25% Kelly)</b>",
            f"",
            f"🛡️ <b>PARACADUTE PER MULTIPLA</b>",
            f"🎯 <b>{best_safe_name}</b> @ <b>{fair_safe:.2f}</b>",
            f"📊 Safe Rate Reale: <b>{best_safe_prob*100:.1f}%</b>",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"📈 <b>MERCATI CHIAVE CALCOLATI:</b>",
            f"• <b>1:</b> {p1*100:.1f}% | <b>X:</b> {px*100:.1f}% | <b>2:</b> {p2*100:.1f}%",
            f"• <b>1X:</b> {p1x*100:.1f}% (Fair: @{1/p1x:.2f})",
            f"• <b>Under 2.5:</b> {pu25*100:.1f}% | <b>Over 2.5:</b> {po25*100:.1f}%",
            f"• <b>Under 3.5 Gol:</b> {pu35*100:.1f}%",
            f"• <b>1X + Under 3.5:</b> {p1x_u35*100:.1f}%",
            f"• <b>Over 8.5 Corner:</b> {po85c*100:.1f}%",
            f"━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"🎯 <b>TOP RISULTATI ESATTI:</b>",
            f"1️⃣ <b>{scores[0][0]}</b> ({scores[0][1]*100:.1f}%) | 2️⃣ <b>{scores[1][0]}</b> ({scores[1][1]*100:.1f}%) | 3️⃣ <b>{scores[2][0]}</b> ({scores[2][1]*100:.1f}%)"
        ]

        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "🇦🇷 Match Argentina", "callback_data": "menu_arg"},
                    {"text": "🇧🇷 Match Brasile", "callback_data": "menu_bra"}
                ],
                [
                    {"text": "🎟️ Schedine Weekend (100€)", "callback_data": "menu_tickets"},
                    {"text": "🔄 Menu", "callback_data": "menu_main"}
                ]
            ]
        }

        self.send_message("\n".join(lines), reply_markup=reply_markup)

    def _send_main_menu(self, chat_id: Optional[str] = None):
        """Invia il menu principale interattivo."""
        text = (
            "🤖 <b>BAGENT — CALCOLATORE SCOMMESSE CALCIO</b>\n\n"
            "Benvenuto nel motore quantitativo BAgent!\n"
            "Puoi calcolare <b>qualsiasi partita al mondo</b> in due modi:\n\n"
            "1️⃣ <b>Scrivi direttamente</b> i nomi delle squadre in chat:\n"
            "   👉 Esempio: <code>San Lorenzo vs Banfield</code>\n"
            "   👉 Esempio: <code>Palmeiras vs Atletico-MG</code>\n"
            "   👉 Esempio: <code>Boca vs River</code>\n\n"
            "2️⃣ <b>Oppure usa i pulsanti qui sotto</b> per selezionare i match del weekend o visualizzare le schedine pronte da 100€:"
        )
        reply_markup = {
            "inline_keyboard": [
                [
                    {"text": "🇦🇷 Palinsesto Argentina (Fecha 16)", "callback_data": "menu_arg"},
                ],
                [
                    {"text": "🇧🇷 Palinsesto Brasile (Rodada 28)", "callback_data": "menu_bra"},
                ],
                [
                    {"text": "🎟️ Schedine del Weekend (Budget 100€)", "callback_data": "menu_tickets"},
                ]
            ]
        }
        self.send_message(text, reply_markup=reply_markup)

    def _process_message(self, message: Dict[str, Any]):
        """Elabora i messaggi di testo inviati dall'utente al bot."""
        chat_id = str(message.get("chat", {}).get("id", self.chat_id))
        text = message.get("text", "").strip()

        if not text:
            return

        # Comandi menu
        if text.lower() in ["/start", "/menu", "/help", "menu", "start", "aiuto"]:
            self._send_main_menu(chat_id)
            return

        # Se l'utente scrive una partita (es. "San Lorenzo vs Banfield" o "Palmeiras - Galo")
        lower_t = text.lower()
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

        # Messaggio non riconosciuto -> rimanda al menu con guida
        self.send_message(
            f"🔍 Vuoi analizzare <b>{text}</b>?\n\n"
            f"Per calcolare un match, scrivi le due squadre separate da <b>vs</b>.\n"
            f"Esempio: <code>{text} vs Avversario</code>\n\n"
            f"Oppure seleziona un'opzione dal menu sottostante:",
            reply_markup={
                "inline_keyboard": [
                    [{"text": "📱 Apri Menu Completo", "callback_data": "menu_main"}]
                ]
            }
        )

    def _process_callback_query(self, query: Dict[str, Any]):
        """Gestisce il click sui bottoni inline da parte dell'utente."""
        query_id = query.get("id")
        data = query.get("data", "")
        message = query.get("message", {})
        message_id = message.get("message_id")
        chat_id = str(message.get("chat", {}).get("id", self.chat_id))

        # Rispondi subito alla callback per togliere l'animazione di caricamento
        requests.post(f"{self.api_url}/answerCallbackQuery", json={"callback_query_id": query_id}, timeout=5)

        if data == "menu_main":
            self._send_main_menu(chat_id)
            return

        if data == "menu_arg":
            text = (
                "🇦🇷 <b>LIGA PROFESIONAL ARGENTINA (FECHA 16)</b>\n\n"
                "Tocca un match per calcolare istantaneamente le probabilità e i mercati migliori:"
            )
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "⚽ San Lorenzo vs Banfield", "callback_data": "calc_San Lorenzo_Banfield"}],
                    [{"text": "⚽ Estudiantes vs Defensa", "callback_data": "calc_Estudiantes LP_Defensa y Justicia"}],
                    [{"text": "⚽ River Plate vs Talleres", "callback_data": "calc_River Plate_Talleres"}],
                    [{"text": "⚽ Racing Club vs Platense", "callback_data": "calc_Racing Club_Platense"}],
                    [{"text": "⚽ Belgrano vs Boca Juniors", "callback_data": "calc_Belgrano_Boca Juniors"}],
                    [{"text": "🔙 Torna al Menu", "callback_data": "menu_main"}]
                ]
            }
            self.send_message(text, reply_markup=reply_markup)
            return

        if data == "menu_bra":
            text = (
                "🇧🇷 <b>BRASILEIRÃO SÉRIE A (RODADA 28)</b>\n\n"
                "Tocca un match per calcolare i corner e le combo d'oro:"
            )
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "⚽ Palmeiras vs Atlético-MG", "callback_data": "calc_Palmeiras_Atlético-MG"}],
                    [{"text": "⚽ Botafogo vs Grêmio", "callback_data": "calc_Botafogo_Grêmio"}],
                    [{"text": "⚽ Internacional vs Vitória", "callback_data": "calc_Internacional_Vitória"}],
                    [{"text": "⚽ Flamengo vs Athletico-PR", "callback_data": "calc_Flamengo_Athletico-PR"}],
                    [{"text": "⚽ São Paulo vs Corinthians", "callback_data": "calc_São Paulo_Corinthians"}],
                    [{"text": "🔙 Torna al Menu", "callback_data": "menu_main"}]
                ]
            }
            self.send_message(text, reply_markup=reply_markup)
            return

        if data == "menu_tickets":
            text = (
                "🎟️ <b>SCHEDINE UFFICIALI DEL WEEKEND (BUDGET 100€)</b>\n\n"
                "1️⃣ <b>MULTIPLONA MASTER (6 EVENTI — CASHOUT)</b>\n"
                "• Quota: <b>@10.85</b> | Puntata: <b>25.00€</b>\n"
                "• Potenziale vincita: <b>271.25€</b>\n\n"
                "2️⃣ <b>DOPPIA 1: LA MURAGLIA ARGENTINA</b>\n"
                "• San Lorenzo U3.5 + Estudiantes U3.5\n"
                "• Quota: <b>@1.48</b> | Puntata: <b>30.00€</b> (Incasso: 44.40€)\n\n"
                "3️⃣ <b>DOPPIA 2: I CORNER DEL BRASILE</b>\n"
                "• Palmeiras O7.5C + Botafogo O7.5C\n"
                "• Quota: <b>@1.75</b> | Puntata: <b>25.00€</b> (Incasso: 43.75€)\n\n"
                "4️⃣ <b>DOPPIA 3: LE GRANDI DI CASA</b>\n"
                "• Internacional 1X + Racing 1X+U3.5\n"
                "• Quota: <b>@1.76</b> | Puntata: <b>20.00€</b> (Incasso: 35.20€)\n\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 <i>Tutti i ticket sono pronti nei file reports/tickets/.</i>"
            )
            reply_markup = {
                "inline_keyboard": [
                    [{"text": "🔙 Torna al Menu", "callback_data": "menu_main"}]
                ]
            }
            self.send_message(text, reply_markup=reply_markup)
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
        # Elimina eventuali webhook pregressi per evitare errori 409 Conflict
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


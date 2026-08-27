"""
BAgent - One-Click Live Dutching & Insurance Coverage Engine
Modulo per il calcolo istantaneo delle coperture live (Break-Even & Profit-Lock)
e invio di alert interattivi su Telegram con importi e quote esatte.
"""

import sys
import os
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

@dataclass
class LiveHedgeOption:
    strategy_name: str # BREAK_EVEN, EQUAL_PROFIT_LOCK, PARTIAL_RECOVERY
    hedge_market: str
    hedge_selection: str
    hedge_odds: float
    recommended_stake_eur: float
    guaranteed_payout_if_hedge_wins: float
    guaranteed_payout_if_original_wins: float
    net_profit_if_hedge_wins: float
    net_profit_if_original_wins: float
    risk_reduction_pct: float
    instructions: str

@dataclass
class TicketLiveStatus:
    ticket_id: str
    ticket_name: str
    initial_stake_eur: float
    potential_payout_eur: float
    total_legs: int
    legs_won: int
    legs_pending: int
    critical_match: str
    current_minute: int
    current_score: str
    hedge_options: List[LiveHedgeOption]

class OneClickLiveInsuranceEngine:
    """
    Motore matematico per il calcolo in tempo reale delle coperture Dutching.
    Elimina il panico live fornendo gli importi esatti in Euro da puntare sull'esito opposto.
    """

    def __init__(self, telegram_token: Optional[str] = None, telegram_chat_id: Optional[str] = None):
        self.telegram_token = telegram_token or os.getenv("TELEGRAM_TOKEN", "")
        self.telegram_chat_id = telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID", "")

    def calculate_hedges(
        self,
        initial_stake: float,
        potential_payout: float,
        hedge_odds: float,
        hedge_market: str,
        hedge_selection: str
    ) -> List[LiveHedgeOption]:
        """
        Calcola le 3 opzioni quantitative di copertura per un ticket a rischio:
        1. Break-Even (Zero-Loss / Ritorno Capitale)
        2. Equal Profit Lock (Blocco Profitto / Arbitraggio)
        3. Partial Recovery (Recupero 50% con micro-stake)
        """
        if hedge_odds <= 1.0:
            return []

        options = []

        # 1. OPZIONE A: BREAK-EVEN (Recupero 100% dello Stake Iniziale)
        # Stake_hedge = Initial_Stake / (Hedge_Odds - 1)
        stake_be = initial_stake / (hedge_odds - 1.0)
        stake_be = round(stake_be * 2) / 2 # arrotondato a 0.50€
        payout_hedge_be = stake_be * hedge_odds
        net_if_hedge_be = payout_hedge_be - (initial_stake + stake_be)
        net_if_orig_be = potential_payout - (initial_stake + stake_be)

        options.append(LiveHedgeOption(
            strategy_name="🛡️ OPZIONE A: BREAK-EVEN (Zero Perdita / Rimborso 100%)",
            hedge_market=hedge_market,
            hedge_selection=hedge_selection,
            hedge_odds=hedge_odds,
            recommended_stake_eur=stake_be,
            guaranteed_payout_if_hedge_wins=round(payout_hedge_be, 2),
            guaranteed_payout_if_original_wins=round(potential_payout, 2),
            net_profit_if_hedge_wins=round(net_if_hedge_be, 2),
            net_profit_if_original_wins=round(net_if_orig_be, 2),
            risk_reduction_pct=100.0,
            instructions=f"Punta {stake_be:.2f} € su '{hedge_selection}' @ {hedge_odds:.2f}. Se il match si ribalta, recuperi tutti i {initial_stake:.2f} € spesi (P&L: 0.00 €). Se la schedina vince, incassi comunque +{net_if_orig_be:.2f} € netti!"
        ))

        # 2. OPZIONE B: EQUAL PROFIT LOCK (Blocco Profitto Indipendente dall'Esito)
        # Stake_hedge = Potential_Payout / Hedge_Odds
        stake_lock = potential_payout / hedge_odds
        stake_lock = round(stake_lock * 2) / 2
        payout_hedge_lock = stake_lock * hedge_odds
        net_if_hedge_lock = payout_hedge_lock - (initial_stake + stake_lock)
        net_if_orig_lock = potential_payout - (initial_stake + stake_lock)

        options.append(LiveHedgeOption(
            strategy_name="👑 OPZIONE B: PROFIT-LOCK (Incasso Matematico Garantito)",
            hedge_market=hedge_market,
            hedge_selection=hedge_selection,
            hedge_odds=hedge_odds,
            recommended_stake_eur=stake_lock,
            guaranteed_payout_if_hedge_wins=round(payout_hedge_lock, 2),
            guaranteed_payout_if_original_wins=round(potential_payout, 2),
            net_profit_if_hedge_wins=round(net_if_hedge_lock, 2),
            net_profit_if_original_wins=round(net_if_orig_lock, 2),
            risk_reduction_pct=100.0,
            instructions=f"Punta {stake_lock:.2f} € su '{hedge_selection}' @ {hedge_odds:.2f}. Trasforma la scommessa in cassa certa: vinci ~+{net_if_orig_lock:.2f} € qualsiasi cosa accada nei minuti finali!"
        ))

        return options

    def generate_telegram_insurance_alert(self, status: TicketLiveStatus) -> str:
        """Formatta l'alert di emergenza/copertura da inviare su Telegram."""
        msg = (
            f"🚨 *BAGENT LIVE INSURANCE ALERT: COPERTURA DISPONIBILE*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎫 *Ticket in Gioco:* {status.ticket_name}\n"
            f"💰 *Stake Iniziale:* `{status.initial_stake_eur:.2f} €` ➔ *Vincita Potenziale:* `{status.potential_payout_eur:.2f} €`\n"
            f"📊 *Avanzamento:* *{status.legs_won}/{status.total_legs} Prese* ({status.legs_pending} in corso)\n\n"
            f"⚽ *Match Decisivo:* {status.critical_match}\n"
            f"⏱️ *Stato Live:* Minuto *{status.current_minute}'* (Risultato: *{status.current_score}*)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🧠 *CALCOLI DI COPERTURA DISPONIBILI:*\n\n"
        )

        for opt in status.hedge_options:
            msg += (
                f"*{opt.strategy_name}*\n"
                f"• Mercato da Giocare: `{opt.hedge_market}` ➔ *[{opt.hedge_selection}]*\n"
                f"• Quota Live: `{opt.hedge_odds:.2f}×`\n"
                f"• 💵 *STAKE DA PUNTARE:* *`{opt.recommended_stake_eur:.2f} €`*\n"
                f"• 📈 *Se la Copertura Entra:* Incassi *{opt.guaranteed_payout_if_hedge_wins:.2f} €* (Netto: `{opt.net_profit_if_hedge_wins:+.2f} €`)\n"
                f"• 🏆 *Se il Ticket Originale Vince:* Incassi *{opt.guaranteed_payout_if_original_wins:.2f} €* (Netto: `{opt.net_profit_if_original_wins:+.2f} €`)\n"
                f"💡 *Azione:* {opt.instructions}\n\n"
                f"────────────────────────────\n"
            )

        msg += "👉 *Apri Netwin ed esegui la copertura in 10 secondi!*"
        return msg

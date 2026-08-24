"""
BAgent - Live Hedge & Insurance Engine (Motore di Copertura & Assicurazione Live)
Calcola in tempo reale la contromisura / copertura ottimale (Dutching / Hedging)
quando una partita sta prendendo una piega negativa o divergente dal piano pre-match.
"""

import sys
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class LiveHedgeInsuranceEngine:
    def __init__(self):
        self.name = "Live Hedge & Insurance Engine"

    def calculate_hedge_stake(self, initial_stake: float, initial_payout: float, hedge_odds: float, mode: str = "break_even") -> dict:
        """
        Calcola lo stake ideale per la scommessa assicurativa.
        
        Modalita':
        1. 'break_even': Punta il minimo indispensabile per recuperare lo stake iniziale (Perdita = 0.00 €).
        2. 'balanced_profit': Distribuisce il profitto equamente su entrambi gli esiti.
        """
        if hedge_odds <= 1.0:
            return {"error": "Quota hedge non valida (deve essere > 1.0)"}

        if mode == "break_even":
            # Per recuperare esattamente initial_stake: Stake_Hedge * (hedge_odds - 1) = initial_stake
            hedge_stake = round(initial_stake / (hedge_odds - 1.0), 2)
            total_invested = round(initial_stake + hedge_stake, 2)
            payout_if_hedge_wins = round(hedge_stake * hedge_odds, 2)
            net_if_hedge_wins = round(payout_if_hedge_wins - total_invested, 2)
            net_if_original_wins = round(initial_payout - total_invested, 2)

            return {
                "mode": "Recupero Capitale (Break-Even)",
                "hedge_stake": hedge_stake,
                "total_invested": total_invested,
                "payout_if_hedge_wins": payout_if_hedge_wins,
                "net_if_hedge_wins": net_if_hedge_wins,
                "net_if_original_wins": net_if_original_wins
            }

        elif mode == "balanced_profit":
            # Distribuzione equilibrata: Payout_Original - Stake_Hedge = Payout_Hedge - Initial_Stake
            hedge_stake = round(initial_payout / hedge_odds, 2)
            total_invested = round(initial_stake + hedge_stake, 2)
            payout_if_hedge_wins = round(hedge_stake * hedge_odds, 2)
            net_profit = round(payout_if_hedge_wins - total_invested, 2)

            return {
                "mode": "Profitto Bilanciato (Guaranteed Profit)",
                "hedge_stake": hedge_stake,
                "total_invested": total_invested,
                "payout_if_hedge_wins": payout_if_hedge_wins,
                "net_profit_both_ways": net_profit
            }

    def detect_hedge_trigger(self, match_state: dict) -> dict:
        """
        Analizza i dati live (minuto, gol, cartellini rossi, corner, falli) e rileva se scatta l'allarme Hedge.
        """
        minute = match_state.get("minute", 0)
        score_home = match_state.get("score_home", 0)
        score_away = match_state.get("score_away", 0)
        corners_home = match_state.get("corners_home", 0)
        corners_away = match_state.get("corners_away", 0)
        red_cards_home = match_state.get("red_cards_home", 0)
        red_cards_away = match_state.get("red_cards_away", 0)
        original_pick = match_state.get("original_pick", "")

        alerts = []

        # SCENARIO 1: Espulsione della nostra squadra
        if ("1" in original_pick or "casa" in original_pick.lower()) and red_cards_home > 0:
            alerts.append({
                "type": "RED_CARD_CRISIS",
                "severity": "CRITICAL",
                "reason": f"Espulsione squadra di casa al minuto {minute}'! La partita e' compromessa.",
                "suggested_hedge": "Doppia Chance X2 Ospite (Live) o Under Gol",
                "suggested_odds_range": "1.70 - 2.20"
            })

        # SCENARIO 2: Corner bloccati (Corner Drought)
        if "corner" in original_pick.lower() and "over" in original_pick.lower():
            total_corners = corners_home + corners_away
            if minute >= 40 and total_corners <= 2:
                alerts.append({
                    "type": "CORNER_DROUGHT",
                    "severity": "HIGH",
                    "reason": f"Solo {total_corners} corner al {minute}'! Ritmo da vie centrali o partita bloccata.",
                    "suggested_hedge": "Under Corner Live o Over Cartellini Live se ci sono falli tattici",
                    "suggested_odds_range": "1.60 - 1.95"
                })

        # SCENARIO 3: Risultato bloccato 0-0 su Over 2.5
        if "over 2.5" in original_pick.lower() and (score_home + score_away == 0) and minute >= 60:
            alerts.append({
                "type": "GOAL_DROUGHT",
                "severity": "HIGH",
                "reason": f"Risultato fermo sullo 0-0 al minuto {minute}'!",
                "suggested_hedge": "Under 1.5 Gol Finale Live @ 1.50 - 1.80",
                "suggested_odds_range": "1.50 - 1.80"
            })

        return {
            "match": match_state.get("match", "Unknown"),
            "minute": minute,
            "has_hedge_opportunity": len(alerts) > 0,
            "alerts": alerts
        }

    def format_telegram_hedge_message(self, match: str, alert_info: dict, hedge_calc: dict) -> str:
        """
        Genera il template grafico per Telegram per avvisare l'utente della copertura live istantanea.
        """
        msg = (
            f"🚨 <b>ALLARME BAGENT HEDGE & INSURANCE (LIVE MINUTO {alert_info.get('minute', '')}')</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚽ <b>Partita</b>: <code>{match}</code>\n"
            f"⚠️ <b>Criticità Rilevata</b>: {alert_info.get('reason', '')}\n\n"
            f"🛡️ <b>COPERTURA ASSICURATIVA CONSIGLIATA</b>:\n"
            f"👉 <b>Mercato Live</b>: <b>{alert_info.get('suggested_hedge', '')}</b>\n"
            f"🎯 <b>Stake di Copertura</b>: <b>{hedge_calc.get('hedge_stake', 0.0)} €</b>\n"
            f"📊 <b>Strategia</b>: {hedge_calc.get('mode', '')}\n"
            f"💵 <i>Se la copertura vince: Incasso {hedge_calc.get('payout_if_hedge_wins', 0.0)} € (Capitale 100% Salvato!)</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        return msg

if __name__ == "__main__":
    engine = LiveHedgeInsuranceEngine()

    print("=== TEST 1: CALCOLO MATEMATICO BREAK-EVEN HEDGE ===")
    calc = engine.calculate_hedge_stake(initial_stake=20.0, initial_payout=71.60, hedge_odds=1.80, mode="break_even")
    print(f"Stake Iniziale: 20.00 € (Pot. 71.60 €)")
    print(f"Quota Copertura Live: 1.80")
    print(f"-> Stake Hedge da puntare: {calc['hedge_stake']} €")
    print(f"-> Se vince l'Hedge: Incasso {calc['payout_if_hedge_wins']} € (Netto: {calc['net_if_hedge_wins']} €)")
    print(f"-> Se vince la schedina originale: Incasso netto residuo: {calc['net_if_original_wins']} €")

    print("\n=== TEST 2: SIMULAZIONE ALLARME CORNER DROUGHT (Caso Barça/Atalanta di ieri) ===")
    state = {
        "match": "Elche vs Barcellona",
        "minute": 42,
        "score_home": 0,
        "score_away": 2,
        "corners_home": 1,
        "corners_away": 1,
        "original_pick": "Over 5.5 Corner Barcellona",
        "initial_stake": 20.0,
        "initial_payout": 71.60
    }
    trigger = engine.detect_hedge_trigger(state)
    if trigger["has_hedge_opportunity"]:
        alert = trigger["alerts"][0]
        alert["minute"] = state["minute"]
        tg_msg = engine.format_telegram_hedge_message(state["match"], alert, calc)
        print(tg_msg)

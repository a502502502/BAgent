"""
Live Momentum Sentinel & In-Play Gem Sniping Engine
Modelli in-play per il calcio: impatto di un'espulsione sul Poisson/xG,
fair value sul tempo residuo, lock anticipato e hedging.
"""

from __future__ import annotations
import math
import numpy as np
from scipy.stats import poisson
from typing import Dict, Any, List, Optional, Tuple

class LiveMomentumSentinel:
    """
    Sentinel in-play con modelli quantitativi per eventi critici e live trading.
    """

    def _calculate_red_card_impact(
        self,
        xg_home_pre: float,
        xg_away_pre: float,
        red_cards_home: int,
        red_cards_away: int
    ) -> Tuple[float, float]:
        """
        Calcola l'impatto dell'espulsione sui rate di xG (tasso/90 min).
        Riduce l'xG della squadra in 10 del 28% e concede un boost dell'8% all'avversario.
        """
        red_card_penalty = 0.28
        xg_home_rate = xg_home_pre
        xg_away_rate = xg_away_pre
        
        if red_cards_home > 0:
            xg_home_rate *= max(0.20, 1.0 - red_card_penalty * red_cards_home)
            xg_away_rate *= 1.08
        
        if red_cards_away > 0:
            xg_away_rate *= max(0.20, 1.0 - red_card_penalty * red_cards_away)
            xg_home_rate *= 1.08
        
        return xg_home_rate, xg_away_rate

    def _calculate_in_play_poisson(
        self,
        xg_home_rate: float,
        xg_away_rate: float,
        current_score_home: int,
        current_score_away: int,
        minute: int
    ) -> Dict[str, float]:
        """
        Calcola distribuzione Poisson condizionale sul tempo rimanente.
        Scala gli xG proporzionalmente al tempo residuo (90 - minute) / 90.
        """
        time_remaining_pct = max(0.0, (90.0 - min(90, minute)) / 90.0)
        xg_home_remaining = xg_home_rate * time_remaining_pct
        xg_away_remaining = xg_away_rate * time_remaining_pct
        
        max_goals = 10
        goals_range = np.arange(max_goals)
        
        # PMF Poisson per gol residui
        pmf_home = poisson.pmf(goals_range, max(0.01, xg_home_remaining))
        pmf_away = poisson.pmf(goals_range, max(0.01, xg_away_remaining))
        
        # Matrice congiunta gol residui
        joint_matrix = np.outer(pmf_home, pmf_away)
        
        prob_home_win = 0.0
        prob_draw = 0.0
        prob_away_win = 0.0
        prob_over_2_5 = 0.0
        prob_over_1_5 = 0.0
        
        for i in range(max_goals):
            for j in range(max_goals):
                final_home = current_score_home + i
                final_away = current_score_away + j
                prob = float(joint_matrix[i, j])
                
                if final_home > final_away:
                    prob_home_win += prob
                elif final_home == final_away:
                    prob_draw += prob
                else:
                    prob_away_win += prob
                
                total_goals = final_home + final_away
                if total_goals > 2.5:
                    prob_over_2_5 += prob
                if total_goals > 1.5:
                    prob_over_1_5 += prob
        
        return {
            "prob_home_win": round(prob_home_win, 3),
            "prob_draw": round(prob_draw, 3),
            "prob_away_win": round(prob_away_win, 3),
            "prob_over_2_5": round(prob_over_2_5, 3),
            "prob_over_1_5": round(prob_over_1_5, 3),
            "fair_odds_home": round(1.0 / max(0.01, prob_home_win), 2),
            "fair_odds_draw": round(1.0 / max(0.01, prob_draw), 2),
            "fair_odds_away": round(1.0 / max(0.01, prob_away_win), 2)
        }

    def _evaluate_lock_or_hedge(
        self,
        active_bet: str,
        current_state: Dict[str, Any],
        cashout_offer: Optional[float] = None,
        original_stake: float = 100.0
    ) -> Dict[str, Any]:
        """
        Valuta se la giocata è matematicamente chiusa o se conviene fare hedge/cashout.
        """
        bet_type = active_bet.lower()
        is_locked = False
        lock_message = ""
        
        if "over 18.5" in bet_type:
            total_games = current_state.get("total_games", 0)
            if total_games >= 19:
                is_locked = True
                lock_message = "OVER 18.5 CHIUSO: Incasso garantito!"
        
        elif "over 2.5" in bet_type:
            score = current_state.get("score", "0-0")
            parts = score.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                total_goals = int(parts[0]) + int(parts[1])
                if total_goals >= 3:
                    is_locked = True
                    lock_message = "OVER 2.5 CHIUSO: Incasso garantito!"
        
        elif "multigol 2-4" in bet_type:
            score = current_state.get("score", "0-0")
            parts = score.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                total_goals = int(parts[0]) + int(parts[1])
                if 2 <= total_goals <= 4:
                    is_locked = True
                    lock_message = "MULTIGOL 2-4 CHIUSO: Incasso garantito!"
        
        # Valutazione Cashout
        hedge_recommendation = "HOLD"
        hedge_reason = ""
        
        if cashout_offer is not None and not is_locked:
            guaranteed_profit = cashout_offer - original_stake
            prob_win = current_state.get("prob_win", 0.5)
            potential_win = original_stake * 1.80
            expected_value = prob_win * potential_win - original_stake
            
            if guaranteed_profit > expected_value * 0.80 and guaranteed_profit > 0:
                hedge_recommendation = "CASHOUT"
                hedge_reason = f"Cashout consigliato: profitto garantito €{guaranteed_profit:.2f} > 80% EV attesa (€{expected_value:.2f})."
            elif guaranteed_profit < 0:
                hedge_recommendation = "HOLD"
                hedge_reason = f"Cashout in perdita (€{guaranteed_profit:.2f}). Meglio attendere."
            else:
                hedge_recommendation = "HOLD"
                hedge_reason = "EV attesa superiore al cashout offerto. Mantieni la posizione."
        
        return {
            "is_locked": is_locked,
            "lock_message": lock_message,
            "hedge_recommendation": hedge_recommendation,
            "hedge_reason": hedge_reason,
            "cashout_analysis": {
                "cashout_offer": cashout_offer,
                "guaranteed_profit": (cashout_offer - original_stake) if cashout_offer is not None else 0.0,
                "recommendation": hedge_recommendation
            }
        }

    def analyze_football_live_state(
        self,
        home_team: str,
        away_team: str,
        score: str,
        minute: int,
        xg_home_pre: float = 1.5,
        xg_away_pre: float = 1.2,
        red_cards_home: int = 0,
        red_cards_away: int = 0,
        active_bet: Optional[str] = None,
        cashout_offer: Optional[float] = None,
        original_stake: float = 100.0
    ) -> Dict[str, Any]:
        """
        Analizza lo stato live di una partita di calcio con modelli quantitativi.
        """
        alerts = []
        parts = score.split("-")
        if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
            return {"error": "Invalid score format"}
        
        current_home = int(parts[0])
        current_away = int(parts[1])

        # 1. Rate xG modificato per espulsioni (senza doppio scaling temporale)
        xg_home_rate, xg_away_rate = self._calculate_red_card_impact(
            xg_home_pre=xg_home_pre,
            xg_away_pre=xg_away_pre,
            red_cards_home=red_cards_home,
            red_cards_away=red_cards_away
        )
        
        if red_cards_home > 0 or red_cards_away > 0:
            team_with_red = home_team if red_cards_home > 0 else away_team
            alerts.append({
                "type": "RED_CARD_IMPACT",
                "severity": "CRITICAL",
                "message": f"Rosso per {team_with_red}. Rate xG/90': {xg_home_rate:.2f} - {xg_away_rate:.2f}",
                "xg_adjustment": {
                    "home": xg_home_rate,
                    "away": xg_away_rate
                }
            })

        # 2. Distribuzione Poisson condizionale sul tempo residuo
        in_play_probs = self._calculate_in_play_poisson(
            xg_home_rate=xg_home_rate,
            xg_away_rate=xg_away_rate,
            current_score_home=current_home,
            current_score_away=current_away,
            minute=minute
        )

        # 3. Live Sniping: Favorito sotto nel primo tempo
        is_sniping_opportunity = False
        if minute <= 45 and current_away > current_home:
            is_sniping_opportunity = True
            alerts.append({
                "type": "LIVE_SNIPING_OPPORTUNITY",
                "severity": "HIGH",
                "message": f"{home_team} sotto {score} al {minute}'. Fair odds 1: {in_play_probs['fair_odds_home']}"
            })

        # 4. Valutazione Lock o Hedge
        current_state = {
            "score": score,
            "total_games": current_home + current_away,
            "prob_win": in_play_probs["prob_home_win"] if "1" in (active_bet or "") else in_play_probs["prob_away_win"]
        }
        
        lock_hedge_analysis = self._evaluate_lock_or_hedge(
            active_bet=active_bet or "",
            current_state=current_state,
            cashout_offer=cashout_offer,
            original_stake=original_stake
        )
        
        if lock_hedge_analysis["is_locked"]:
            alerts.append({
                "type": "BET_LOCKED",
                "severity": "INFO",
                "message": lock_hedge_analysis["lock_message"]
            })
        
        if lock_hedge_analysis["hedge_recommendation"] == "CASHOUT":
            alerts.append({
                "type": "CASHOUT_RECOMMENDED",
                "severity": "HIGH",
                "message": lock_hedge_analysis["hedge_reason"]
            })

        return {
            "match": f"{home_team} vs {away_team}",
            "score": score,
            "minute": minute,
            "red_cards": {"home": red_cards_home, "away": red_cards_away},
            "xg_rates": {"home": round(xg_home_rate, 2), "away": round(xg_away_rate, 2)},
            "in_play_probabilities": in_play_probs,
            "is_sniping_opportunity": is_sniping_opportunity,
            "lock_hedge_analysis": lock_hedge_analysis,
            "alerts": alerts
        }

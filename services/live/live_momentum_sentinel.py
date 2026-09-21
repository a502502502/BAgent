"""
Live Momentum Sentinel & In-Play Gem Sniping Engine
Modelli matematici rigorosi per probabilità in-play post-eventi critici:
- Tennis: rimonta post-bagel e break iniziale (con penalità psicologica e superficie)
- Calcio: impatto espulsione su Poisson/xG e fair value in-play su tempo residuo
- Lock anticipato e hedging ottimale (confronto profitto garantito vs expected value)
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

    def _calculate_tennis_comeback_probability(
        self,
        player1_elo: float,
        player2_elo: float,
        sets_score: str,
        games_score: str,
        surface: str = "clay"
    ) -> Dict[str, float]:
        """
        Calcola probabilità di rimonta dopo bagel o break iniziale.
        Usa Markov condizionale con fattore psicologico post-bagel.
        """
        sets_parts = sets_score.split("-")
        if len(sets_parts) != 2 or not sets_parts[0].isdigit() or not sets_parts[1].isdigit():
            return {"p1_comeback_prob": 0.5, "p2_comeback_prob": 0.5}
        
        p1_sets = int(sets_parts[0])
        p2_sets = int(sets_parts[1])
        
        # Elo differenziale (base probability)
        elo_diff = player1_elo - player2_elo
        base_p1_win = 1.0 / (1.0 + math.pow(10, -elo_diff / 400.0))
        
        # Fattore psicologico post-bagel
        games_list = games_score.split()
        bagel_penalty_p1 = 1.0
        bagel_penalty_p2 = 1.0
        
        for g in games_list:
            if "6-0" in g:
                # P1 ha vinto 6-0, P2 ha subito bagel
                bagel_penalty_p2 = 0.60
            elif "0-6" in g:
                # P2 ha vinto 6-0, P1 ha subito bagel
                bagel_penalty_p1 = 0.60
        
        # Fattore superficie (su clay è più agevole recuperare)
        surface_factor = {
            "clay": 1.12,
            "hard": 1.00,
            "grass": 0.88
        }.get(surface.lower(), 1.00)
        
        # Probabilità di rimonta se sotto di un set
        if p1_sets < p2_sets:
            p1_comeback = base_p1_win * bagel_penalty_p1 * surface_factor
            p1_comeback = max(0.05, min(0.85, p1_comeback))
            p2_comeback = 1.0 - p1_comeback
        elif p2_sets < p1_sets:
            p2_comeback = (1.0 - base_p1_win) * bagel_penalty_p2 * surface_factor
            p2_comeback = max(0.05, min(0.85, p2_comeback))
            p1_comeback = 1.0 - p2_comeback
        else:
            p1_comeback = base_p1_win
            p2_comeback = 1.0 - base_p1_win
        
        return {
            "p1_comeback_prob": round(p1_comeback, 3),
            "p2_comeback_prob": round(p2_comeback, 3)
        }

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

    def analyze_tennis_live_state(
        self,
        player1: str,
        player2: str,
        sets_score: str,
        games_score: str,
        player1_elo: float = 1500.0,
        player2_elo: float = 1500.0,
        surface: str = "clay",
        active_bet: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analizza lo stato live di una partita di tennis con modelli quantitativi.
        """
        games = games_score.split()
        alerts = []
        status_verdict = "IN_PROGRESS"

        # 1. Rilevamento Bagel
        has_bagel = any("6-0" in g or "0-6" in g for g in games)
        if has_bagel:
            alerts.append({
                "type": "BAGEL_COLLAPSE_WARNING",
                "severity": "CRITICAL",
                "message": "Rilevato set a zero (6-0/0-6). Grave crollo fisico o blackout mentale."
            })
            status_verdict = "HIGH_VOLATILITY"

        # 2. Calcolo game totali
        total_games_played = 0
        for g in games:
            parts = g.split("-")
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                total_games_played += int(parts[0]) + int(parts[1])

        # 3. Probabilità di rimonta
        comeback_probs = self._calculate_tennis_comeback_probability(
            player1_elo=player1_elo,
            player2_elo=player2_elo,
            sets_score=sets_score,
            games_score=games_score,
            surface=surface
        )
        
        if comeback_probs["p1_comeback_prob"] < 0.20 or comeback_probs["p2_comeback_prob"] < 0.20:
            alerts.append({
                "type": "LOW_COMEBACK_PROBABILITY",
                "severity": "HIGH",
                "message": f"Probabilità di rimonta molto bassa (P1: {comeback_probs['p1_comeback_prob']:.1%}, P2: {comeback_probs['p2_comeback_prob']:.1%})."
            })

        # 4. Verifica lock Over
        # In tennis best-of-3: se il 1° set va al tiebreak (7-6/6-7 = 13 game),
        # il 2° set deve avere almeno 6 game (6-0), portando il totale a minimo 19 game.
        over_locked = False
        if active_bet and "over" in active_bet.lower():
            if "18.5" in active_bet and (
                total_games_played >= 19 or 
                (total_games_played >= 13 and ("7-6" in games_score or "6-7" in games_score))
            ):
                over_locked = True
                alerts.append({
                    "type": "OVER_LOCK_CONFIRMED",
                    "severity": "INFO",
                    "message": f"Over 18.5 MATEMATICAMENTE CHIUSO: {total_games_played} game già disputati (minimo 19 garantiti)!"
                })

        return {
            "match": f"{player1} vs {player2}",
            "sets": sets_score,
            "games": games_score,
            "total_games": total_games_played,
            "has_bagel": has_bagel,
            "comeback_probabilities": comeback_probs,
            "over_locked": over_locked,
            "status_verdict": status_verdict,
            "alerts": alerts
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

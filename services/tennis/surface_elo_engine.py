"""
Surface-Adjusted Tennis Elo & Form Engine with Markov Chain Modeling
Calcola rating Elo separati per superficie, con decadimento stamina dinamico
e modellazione rigorosa punto → game → set → match tramite Catene di Markov.
"""

from __future__ import annotations
import math
import numpy as np
from typing import Dict, Any, Optional, Tuple, List

class SurfaceEloEngine:
    """
    Motore quantitativo tennis con Markov Chain gerarchica per distribuzioni esatte:
    Punto → Game → Set → Match + Convoluzione discreta per Totale Game e Handicap.
    """
    
    BASE_ELO = 1500.0
    K_FACTOR = 32.0

    def __init__(self):
        self.player_database: Dict[str, Dict[str, Any]] = {
            "Arantxa Rus": {
                "age": 33,
                "clay": 1580.0,
                "hard": 1540.0,
                "stamina_score": 0.65,
                "recent_win_rate_30d": 0.42
            },
            "Mia Ristic": {
                "age": 19,
                "clay": 1560.0,
                "hard": 1510.0,
                "stamina_score": 0.92,
                "recent_win_rate_30d": 0.75
            },
            "Isabella Shinikova": {
                "age": 32,
                "clay": 1490.0,
                "hard": 1610.0,
                "stamina_score": 0.78,
                "recent_win_rate_30d": 0.68
            },
            "Aysegul Mert": {
                "age": 20,
                "clay": 1420.0,
                "hard": 1450.0,
                "stamina_score": 0.80,
                "recent_win_rate_30d": 0.40
            },
            "Florian Broska": {
                "age": 26,
                "clay": 1595.0,
                "hard": 1570.0,
                "stamina_score": 0.88,
                "recent_win_rate_30d": 0.72
            },
            "Federico Arnaboldi": {
                "age": 24,
                "clay": 1530.0,
                "hard": 1490.0,
                "stamina_score": 0.82,
                "recent_win_rate_30d": 0.50
            },
            "Polona Hercog": {
                "age": 33,
                "clay": 1600.0,
                "hard": 1510.0,
                "stamina_score": 0.70,
                "recent_win_rate_30d": 0.60
            },
            "Leyre Romero Gormaz": {
                "age": 22,
                "clay": 1590.0,
                "hard": 1500.0,
                "stamina_score": 0.89,
                "recent_win_rate_30d": 0.65
            }
        }

    def get_player_profile(self, name: str) -> Dict[str, Any]:
        """Recupera o stima il profilo del giocatore."""
        for k, v in self.player_database.items():
            if k.lower() in name.lower() or name.lower() in k.lower():
                return v
        return {
            "age": 26,
            "clay": self.BASE_ELO,
            "hard": self.BASE_ELO,
            "stamina_score": 0.80,
            "recent_win_rate_30d": 0.50
        }

    def _elo_to_match_prob(self, elo1: float, elo2: float) -> Tuple[float, float]:
        """Converte differenza Elo in probabilità di vittoria match."""
        diff = elo1 - elo2
        p1 = 1.0 / (1.0 + math.pow(10, -diff / 400.0))
        return p1, 1.0 - p1

    def _match_prob_to_service_prob(self, match_prob: float, surface: str) -> float:
        """
        Trasforma probabilità di vittoria match in probabilità di vincita al singolo punto di battuta.
        Usa fattore superficie-specifico (grass > hard > clay per P_serv).
        """
        surface_factor = {
            "clay": 0.55,
            "hard": 0.65,
            "grass": 0.75
        }.get(surface.lower(), 0.60)
        
        p_serv = 0.5 + (match_prob - 0.5) * surface_factor
        return max(0.45, min(0.85, p_serv))

    def _markov_game_prob(self, p_serv: float) -> float:
        """
        Calcola la probabilità di vittoria del game al servizio tramite formula chiusa Markov (Barnett & Clarke).
        Include probabilità da deuce come serie geometrica: p^2 / (1 - 2*p*q).
        """
        p = p_serv
        q = 1.0 - p
        p_win_no_deuce = p**4 * (1.0 + 4.0*q + 10.0*(q**2))
        p_deuce = 20.0 * (p**3) * (q**3)
        denom = 1.0 - 2.0*p*q
        p_win_from_deuce = (p**2) / denom if denom > 0 else 0.5
        return float(p_win_no_deuce + p_deuce * p_win_from_deuce)

    def _markov_set_distribution(
        self, 
        p1_hold: float, 
        p2_hold: float
    ) -> Dict[str, Any]:
        """
        Calcola la distribuzione esatta dei punteggi del set (6-0, 6-1, ..., 7-6) e dei game totali.
        Alterna rigorosamente il battitore a ogni game (k pari: P1 batte, k dispari: P2 batte),
        garantendo la conservazione esatta della massa probabilistica (somma = 1.0000).
        """
        dp = np.zeros((8, 8), dtype=float)
        dp[0, 0] = 1.0
        set_results: Dict[Tuple[int, int], float] = {}

        for k in range(13):
            for i in range(min(k + 1, 8)):
                j = k - i
                if j >= 8 or dp[i, j] == 0:
                    continue

                # Set concluso prima del tiebreak
                if (i == 6 and j <= 4) or (i == 7 and j == 5) or (j == 6 and i <= 4) or (j == 7 and i == 5):
                    set_results[(i, j)] = set_results.get((i, j), 0.0) + dp[i, j]
                    continue

                # Tiebreak a 6-6
                if i == 6 and j == 6:
                    p_tb = (p1_hold + (1.0 - p2_hold)) / 2.0
                    set_results[(7, 6)] = set_results.get((7, 6), 0.0) + dp[i, j] * p_tb
                    set_results[(6, 7)] = set_results.get((6, 7), 0.0) + dp[i, j] * (1.0 - p_tb)
                    continue

                # Alternanza servizio: k pari P1 batte, k dispari P2 batte
                p_p1_wins_game = p1_hold if (k % 2 == 0) else (1.0 - p2_hold)
                p_p2_wins_game = 1.0 - p_p1_wins_game

                if i + 1 <= 7:
                    dp[i + 1, j] += dp[i, j] * p_p1_wins_game
                if j + 1 <= 7:
                    dp[i, j + 1] += dp[i, j] * p_p2_wins_game

        # Distribuzione game per set (indice 0..13)
        games_dist = np.zeros(14, dtype=float)
        for (i, j), prob in set_results.items():
            games_dist[i + j] += prob

        p1_win_set = sum(p for (i, j), p in set_results.items() if i > j)
        p2_win_set = sum(p for (i, j), p in set_results.items() if j > i)

        return {
            "set_results": {f"{i}-{j}": p for (i, j), p in set_results.items()},
            "set_results_tuple": set_results,
            "games_distribution": games_dist,
            "p1_win_set": p1_win_set,
            "p2_win_set": p2_win_set
        }

    def _apply_fatigue_decay(
        self, 
        p_serv: float, 
        age: int, 
        stamina: float, 
        set_number: int
    ) -> float:
        """
        Applica penalità dinamica su P_serv per veterani nei set successivi.
        Penalità progressiva: Set 2 < Set 3 (simula affaticamento e rischio bagel).
        """
        if age < 32 or stamina >= 0.75:
            return p_serv
        
        base_penalty = (1.0 - stamina) * 0.18
        set_multiplier = {2: 1.0, 3: 2.2}.get(set_number, 1.0)
        penalty = base_penalty * set_multiplier
        return max(0.40, p_serv * (1.0 - penalty))

    def calculate_match_odds(
        self,
        player1: str,
        player2: str,
        surface: str = "clay",
        best_of: int = 3
    ) -> Dict[str, Any]:
        """
        Calcola probabilità e quote eque (Fair Odds) per:
        - Vincitore Testa a Testa (P1 / P2)
        - Over / Under 18.5 e 21.5 Game Totali (via convoluzione discreta)
        - Handicap Game (-2.5 / +2.5)
        - Probabilità 3 Set
        - Warning su crolli fisici / veterani
        """
        p1 = self.get_player_profile(player1)
        p2 = self.get_player_profile(player2)

        s_key = surface.lower()
        if s_key not in ["clay", "hard", "grass"]:
            s_key = "clay"

        # Elo aggiustato per forma recente
        elo1 = p1.get(s_key, self.BASE_ELO)
        elo2 = p2.get(s_key, self.BASE_ELO)
        form_adj1 = (p1.get("recent_win_rate_30d", 0.5) - 0.5) * 80.0
        form_adj2 = (p2.get("recent_win_rate_30d", 0.5) - 0.5) * 80.0
        adj_elo1 = elo1 + form_adj1
        adj_elo2 = elo2 + form_adj2

        # Probabilità match base
        p1_match_prob, p2_match_prob = self._elo_to_match_prob(adj_elo1, adj_elo2)

        # Stima P_serv base per giocatore
        p1_serv_base = self._match_prob_to_service_prob(p1_match_prob, surface)
        p2_serv_base = self._match_prob_to_service_prob(p2_match_prob, surface)

        age1, stamina1 = p1.get("age", 25), p1.get("stamina_score", 0.8)
        age2, stamina2 = p2.get("age", 25), p2.get("stamina_score", 0.8)

        # Set 1 (senza fatica)
        p1_hold_s1 = self._markov_game_prob(p1_serv_base)
        p2_hold_s1 = self._markov_game_prob(p2_serv_base)
        s1_data = self._markov_set_distribution(p1_hold_s1, p2_hold_s1)

        # Set 2 (con fatica)
        p1_serv_s2 = self._apply_fatigue_decay(p1_serv_base, age1, stamina1, 2)
        p2_serv_s2 = self._apply_fatigue_decay(p2_serv_base, age2, stamina2, 2)
        p1_hold_s2 = self._markov_game_prob(p1_serv_s2)
        p2_hold_s2 = self._markov_game_prob(p2_serv_s2)
        s2_data = self._markov_set_distribution(p1_hold_s2, p2_hold_s2)

        # Set 3 (con fatica accentuata)
        p1_serv_s3 = self._apply_fatigue_decay(p1_serv_base, age1, stamina1, 3)
        p2_serv_s3 = self._apply_fatigue_decay(p2_serv_base, age2, stamina2, 3)
        p1_hold_s3 = self._markov_game_prob(p1_serv_s3)
        p2_hold_s3 = self._markov_game_prob(p2_serv_s3)
        s3_data = self._markov_set_distribution(p1_hold_s3, p2_hold_s3)

        p1_s1 = s1_data["p1_win_set"]
        p1_s2 = s2_data["p1_win_set"]
        p1_s3 = s3_data["p1_win_set"]

        # Probabilità di chiusura match (Best of 3)
        p_2_0 = p1_s1 * p1_s2
        p_0_2 = (1.0 - p1_s1) * (1.0 - p1_s2)
        p_2_1 = (p1_s1 * (1.0 - p1_s2) + (1.0 - p1_s1) * p1_s2) * p1_s3
        p_1_2 = (p1_s1 * (1.0 - p1_s2) + (1.0 - p1_s1) * p1_s2) * (1.0 - p1_s3)

        prob_p1_wins = p_2_0 + p_2_1
        prob_p2_wins = p_0_2 + p_1_2
        prob_three_sets = p_2_1 + p_1_2

        # Convoluzione discreta esatta per la distribuzione dei Game Totali
        g1 = s1_data["games_distribution"]
        g2 = s2_data["games_distribution"]
        g3 = s3_data["games_distribution"]

        g_2sets = np.convolve(g1, g2)
        g_3sets = np.convolve(g_2sets, g3)

        g_match = np.zeros(len(g_3sets), dtype=float)
        g_match[:len(g_2sets)] += (p_2_0 + p_0_2) * g_2sets
        g_match += (p_2_1 + p_1_2) * g_3sets

        prob_over_18_5 = float(np.sum(g_match[19:]))
        prob_over_21_5 = float(np.sum(g_match[22:]))

        # Convoluzione esatta per Handicap Game (-2.5 / +2.5)
        # Differenziale scarto (i - j) per set
        OFFSET = 20
        d1 = np.zeros(41, dtype=float)
        d2 = np.zeros(41, dtype=float)
        d3 = np.zeros(41, dtype=float)

        for (i, j), p in s1_data["set_results_tuple"].items():
            d1[OFFSET + (i - j)] += p
        for (i, j), p in s2_data["set_results_tuple"].items():
            d2[OFFSET + (i - j)] += p
        for (i, j), p in s3_data["set_results_tuple"].items():
            d3[OFFSET + (i - j)] += p

        conv_diff_2 = np.convolve(d1, d2)      # offset = 40
        conv_diff_3 = np.convolve(conv_diff_2, d3) # offset = 60

        # P1 Handicap -2.5 significa scarto >= 3 game
        p1_h_m2_5 = float(
            (p_2_0 + p_0_2) * np.sum(conv_diff_2[43:]) +
            (p_2_1 + p_1_2) * np.sum(conv_diff_3[63:])
        )
        p2_h_m2_5 = float(
            (p_2_0 + p_0_2) * np.sum(conv_diff_2[:38]) +
            (p_2_1 + p_1_2) * np.sum(conv_diff_3[:58])
        )

        # Fatigue warning
        p1_fatigue_warning = age1 >= 32 and stamina1 < 0.75
        p2_fatigue_warning = age2 >= 32 and stamina2 < 0.75

        # Raccomandazioni Gemme
        recommendations = []
        if prob_over_18_5 >= 0.70:
            recommendations.append({
                "market": "Over 18.5 Game Totali",
                "fair_odds": round(1.0 / max(0.01, prob_over_18_5), 2),
                "prob": round(prob_over_18_5, 3),
                "reason": f"Match su {surface} equilibrato con alta probabilità di set lunghi o 3 set (Markov conv)."
            })
        if prob_p1_wins >= 0.62:
            recommendations.append({
                "market": f"{player1} Handicap -2.5 Game",
                "fair_odds": round(1.0 / max(0.01, p1_h_m2_5), 2),
                "prob": round(p1_h_m2_5, 3),
                "reason": f"{player1} ha Elo su {surface} superiore (+{adj_elo1 - adj_elo2:.0f} pts)."
            })
        elif prob_p2_wins >= 0.62:
            recommendations.append({
                "market": f"{player2} Handicap -2.5 Game",
                "fair_odds": round(1.0 / max(0.01, p2_h_m2_5), 2),
                "prob": round(p2_h_m2_5, 3),
                "reason": f"{player2} ha Elo su {surface} superiore (+{adj_elo2 - adj_elo1:.0f} pts)."
            })

        return {
            "player1": player1,
            "player2": player2,
            "surface": surface,
            "p1_prob": round(prob_p1_wins, 3),
            "p2_prob": round(prob_p2_wins, 3),
            "p1_fair_odds": round(1.0 / max(0.01, prob_p1_wins), 2),
            "p2_fair_odds": round(1.0 / max(0.01, prob_p2_wins), 2),
            "prob_over_18_5": round(prob_over_18_5, 3),
            "prob_over_21_5": round(prob_over_21_5, 3),
            "prob_three_sets": round(prob_three_sets, 3),
            "p1_handicap_m2_5": round(p1_h_m2_5, 3),
            "p2_handicap_m2_5": round(p2_h_m2_5, 3),
            "fatigue_risk": {
                player1: p1_fatigue_warning,
                player2: p2_fatigue_warning,
            },
            "recommendations": recommendations
        }

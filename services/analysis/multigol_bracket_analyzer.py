#!/usr/bin/env python3
"""
services/analysis/multigol_bracket_analyzer.py — Motore Quantitativo per Mercati Multigol a Fasce per Tempo.
Analizza forchette di gol indipendenti da chi segna:
1. Multigol 1° Tempo (0-2 Gol)
2. Multigol 2° Tempo (1-3 Gol)
3. Multigol Match Totale (1-4 Gol / 2-4 Gol / 2-5 Gol)
4. Tempo con Maggior Numero di Gol (2° Tempo / Pareggio)
"""

import math
from typing import Dict, Any, List

class MultigolBracketAnalyzer:
    def __init__(self):
        # Parametri empirici di calibrazione Top 5 Leghe europee
        self.first_half_goal_share = 0.42   # ~42% dei gol nel 1° tempo
        self.second_half_goal_share = 0.58  # ~58% dei gol nel 2° tempo

    def _poisson(self, lmbda: float, k: int) -> float:
        """Calcola la probabilità di esattamente k eventi data la media lambda."""
        if lmbda <= 0 or k < 0:
            return 0.0
        return (math.exp(-lmbda) * (lmbda ** k)) / math.factorial(k)

    def analyze_match_brackets(self, home_team: str, away_team: str, expected_total_goals: float) -> Dict[str, Any]:
        """
        Calcola le probabilità e l'efficienza asimmetrica dei mercati a fasce indipendenti da chi segna.
        """
        exp_1h = expected_total_goals * self.first_half_goal_share
        exp_2h = expected_total_goals * self.second_half_goal_share

        # Distribuzione probabilità 1° Tempo (k da 0 a 5)
        p_1h = [self._poisson(exp_1h, k) for k in range(6)]
        # Distribuzione probabilità 2° Tempo (k da 0 a 5)
        p_2h = [self._poisson(exp_2h, k) for k in range(6)]

        # 1. Multigol 1° Tempo (0 - 2 Gol)
        prob_1h_0_2 = sum(p_1h[0:3])  # 0, 1 o 2 gol
        prob_1h_1_2 = sum(p_1h[1:3])  # 1 o 2 gol

        # 2. Multigol 2° Tempo (1 - 3 Gol)
        prob_2h_1_3 = sum(p_2h[1:4])  # 1, 2 o 3 gol
        prob_2h_1_4 = sum(p_2h[1:5])  # 1, 2, 3 o 4 gol

        # 3. Multigol Match Totale (k da 0 a 8)
        p_total = [self._poisson(expected_total_goals, k) for k in range(9)]
        prob_mg_1_4 = sum(p_total[1:5])  # 1, 2, 3, 4 gol
        prob_mg_2_4 = sum(p_total[2:5])  # 2, 3, 4 gol
        prob_mg_2_5 = sum(p_total[2:6])  # 2, 3, 4, 5 gol

        # 4. Tempo con più gol: 2° Tempo (P(2H > 1H))
        prob_2h_more = 0.0
        prob_draw_halves = 0.0
        for k1 in range(6):
            for k2 in range(6):
                joint_p = p_1h[k1] * p_2h[k2]
                if k2 > k1:
                    prob_2h_more += joint_p
                elif k2 == k1:
                    prob_draw_halves += joint_p

        # Costruisci raccomandazioni asimmetriche
        recommendations = []
        
        # Fascia 1° Tempo 0-2 & 2° Tempo 1-3
        combo_bracket_prob = prob_1h_0_2 * prob_2h_1_3
        recommendations.append({
            "market_name": "Multigol Tempo: 1°T (0-2) & 2°T (1-3)",
            "estimated_prob": round(combo_bracket_prob * 100, 1),
            "estimated_fair_odd": round(1.0 / combo_bracket_prob if combo_bracket_prob > 0 else 99, 2),
            "description": "Vince se il 1°T ha 0-2 gol e la ripresa ha 1-3 gol (indipendentemente da chi segna!)."
        })

        # Multigol 1-4 Totale
        recommendations.append({
            "market_name": "Multigol Match: 1-4 Gol Totali",
            "estimated_prob": round(prob_mg_1_4 * 100, 1),
            "estimated_fair_odd": round(1.0 / prob_mg_1_4 if prob_mg_1_4 > 0 else 99, 2),
            "description": "Copre tutti i risultati da 1-0, 0-1, 1-1, 2-0, 2-1, 2-2, 3-0, 3-1 fino a 4-0."
        })

        # Multigol 2-4 Totale
        recommendations.append({
            "market_name": "Multigol Match: 2-4 Gol Totali",
            "estimated_prob": round(prob_mg_2_4 * 100, 1),
            "estimated_fair_odd": round(1.0 / prob_mg_2_4 if prob_mg_2_4 > 0 else 99, 2),
            "description": "Ideale per match con almeno 2 gol (es. 2-0, 2-1, 1-1, 3-0, 2-2, 3-1)."
        })

        return {
            "match": f"{home_team} vs {away_team}",
            "expected_goals": expected_total_goals,
            "prob_1h_0_2": round(prob_1h_0_2 * 100, 1),
            "prob_2h_1_3": round(prob_2h_1_3 * 100, 1),
            "prob_mg_1_4": round(prob_mg_1_4 * 100, 1),
            "prob_mg_2_4": round(prob_mg_2_4 * 100, 1),
            "prob_2h_more_goals": round(prob_2h_more * 100, 1),
            "recommendations": recommendations
        }

if __name__ == "__main__":
    analyzer = MultigolBracketAnalyzer()
    res = analyzer.analyze_match_brackets("Liverpool", "Nottingham Forest", expected_total_goals=3.10)
    print(f"\n--- TEST MULTIGOL BRACKET ANALYZER: {res['match']} ---")
    for r in res['recommendations']:
        print(f"• {r['market_name']} ➔ Prob: {r['estimated_prob']}% (Quota Fair: {r['estimated_fair_odd']})")

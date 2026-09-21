"""
Expected Goals (xG) & Bivariate Dixon-Coles Poisson Engine
Simula la matrice esatta dei risultati calcistici (da 0-0 a 6-6) e calcola le probabilità
reali e il valore atteso (Edge) per mercati di nicchia: MultiGol 1-2 Casa, MultiGol 2-4,
Combo 1X2 + U/O e Doppia Chance + MultiGol.
"""

from __future__ import annotations
import math
from typing import Dict, Any, List, Tuple

class XgPoissonEngine:
    """
    Motore quantitativo basato su distribuzione di Poisson bivariata e Dixon-Coles.
    """

    def __init__(self, rho: float = -0.05):
        # rho: fattore di correlazione per bassi punteggi (0-0, 1-0, 0-1, 1-1)
        self.rho = rho

    @staticmethod
    def _poisson_pmf(k: int, lam: float) -> float:
        """Calcola la probabilità di Poisson P(X = k | lambda)."""
        if lam <= 0:
            return 1.0 if k == 0 else 0.0
        return (math.pow(lam, k) * math.exp(-lam)) / math.factorial(k)

    def _dixon_coles_tau(self, x: int, y: int, lambda_home: float, mu_away: float) -> float:
        """Fattore di correzione Dixon-Coles per punteggi bassi."""
        if x == 0 and y == 0:
            return 1.0 - (lambda_home * mu_away * self.rho)
        elif x == 0 and y == 1:
            return 1.0 + (lambda_home * self.rho)
        elif x == 1 and y == 0:
            return 1.0 + (mu_away * self.rho)
        elif x == 1 and y == 1:
            return 1.0 - self.rho
        return 1.0

    def generate_score_matrix(
        self,
        xg_home: float,
        xg_away: float,
        max_goals: int = 7
    ) -> List[List[float]]:
        """Genera la matrice di probabilità per ogni punteggio esatto [home_goals][away_goals]."""
        matrix = [[0.0 for _ in range(max_goals)] for _ in range(max_goals)]
        total_prob = 0.0

        for i in range(max_goals):
            p_home = self._poisson_pmf(i, xg_home)
            for j in range(max_goals):
                p_away = self._poisson_pmf(j, xg_away)
                tau = self._dixon_coles_tau(i, j, xg_home, xg_away)
                prob = p_home * p_away * tau
                matrix[i][j] = prob
                total_prob += prob

        # Normalizzazione
        if total_prob > 0:
            for i in range(max_goals):
                for j in range(max_goals):
                    matrix[i][j] /= total_prob

        return matrix

    def analyze_niche_markets(
        self,
        home_team: str,
        away_team: str,
        xg_home: float,
        xg_away: float,
        bookmaker_odds: Dict[str, float] = None
    ) -> Dict[str, Any]:
        """
        Analizza tutti i mercati e confronta con le quote Netwin per trovare il vero Edge.
        """
        matrix = self.generate_score_matrix(xg_home, xg_away)
        book_odds = bookmaker_odds or {}

        # 1. 1X2 e Doppia Chance
        prob_home = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if i > j)
        prob_draw = sum(matrix[i][i] for i in range(len(matrix)))
        prob_away = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if i < j)
        prob_1x = prob_home + prob_draw
        prob_x2 = prob_draw + prob_away

        # 2. Over / Under Totali
        prob_over_1_5 = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if (i + j) > 1.5)
        prob_over_2_5 = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if (i + j) > 2.5)
        prob_under_2_5 = 1.0 - prob_over_2_5
        prob_under_3_5 = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if (i + j) < 3.5)

        # 3. MultiGol Totali
        prob_mg_1_4 = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if 1 <= (i + j) <= 4)
        prob_mg_2_4 = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if 2 <= (i + j) <= 4)

        # 4. MultiGol Casa (es. Trento 1-2 Gol Casa)
        prob_home_mg_1_2 = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if 1 <= i <= 2)
        prob_home_over_1_5 = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if i >= 2)

        # 5. Combo Protette (1X + Over 1.5, 1X + MultiGol 1-4)
        prob_1x_over_1_5 = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if i >= j and (i + j) > 1.5)
        prob_1x_mg_1_4 = sum(matrix[i][j] for i in range(len(matrix)) for j in range(len(matrix)) if i >= j and 1 <= (i + j) <= 4)

        # Mappatura mercati con Fair Odds
        markets = {
            "MultiGol 1-2 Casa": {
                "prob": round(prob_home_mg_1_2, 3),
                "fair_odds": round(1.0 / max(0.01, prob_home_mg_1_2), 2),
            },
            "MultiGol 2-4 Totale": {
                "prob": round(prob_mg_2_4, 3),
                "fair_odds": round(1.0 / max(0.01, prob_mg_2_4), 2),
            },
            "1X + Over 1.5": {
                "prob": round(prob_1x_over_1_5, 3),
                "fair_odds": round(1.0 / max(0.01, prob_1x_over_1_5), 2),
            },
            "1X + MultiGol 1-4": {
                "prob": round(prob_1x_mg_1_4, 3),
                "fair_odds": round(1.0 / max(0.01, prob_1x_mg_1_4), 2),
            },
            "1X (Doppia Chance)": {
                "prob": round(prob_1x, 3),
                "fair_odds": round(1.0 / max(0.01, prob_1x), 2),
            },
            "Over 2.5": {
                "prob": round(prob_over_2_5, 3),
                "fair_odds": round(1.0 / max(0.01, prob_over_2_5), 2),
            }
        }

        # Calcolo Edge se le quote Netwin sono fornite
        gems = []
        for m_name, data in markets.items():
            netwin_q = book_odds.get(m_name)
            if netwin_q:
                edge = (data["prob"] * netwin_q - 1.0) * 100.0
                data["netwin_odds"] = netwin_q
                data["edge_pct"] = round(edge, 1)
                if edge >= 8.0 and netwin_q >= 1.60:
                    gems.append({
                        "market": m_name,
                        "netwin_odds": netwin_q,
                        "fair_odds": data["fair_odds"],
                        "prob": data["prob"],
                        "edge_pct": round(edge, 1)
                    })

        return {
            "match": f"{home_team} vs {away_team}",
            "xg_home": xg_home,
            "xg_away": xg_away,
            "markets": markets,
            "true_gems": gems
        }

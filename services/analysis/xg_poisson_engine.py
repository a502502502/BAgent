"""
Expected Goals (xG) & Bivariate Dixon-Coles Poisson Engine + Negative Binomial Corners
Ottimizzato con NumPy/SciPy per calcoli vettoriali ad alte prestazioni.
"""

from __future__ import annotations
import numpy as np
from scipy.stats import poisson, nbinom
from typing import Dict, Any, List, Optional

class QuantitativeEngine:
    """
    Motore quantitativo unificato per Calcio (Poisson/Dixon-Coles) e Corner (Binomiale Negativa).
    """

    def __init__(self, rho: float = -0.05):
        # rho: fattore di correlazione per bassi punteggi. 
        # TODO: In futuro, passa un dizionario {league: rho} per calibrazione specifica.
        self.rho = rho

    def generate_score_matrix(self, xg_home: float, xg_away: float, max_goals: int = 7) -> np.ndarray:
        """
        Genera la matrice di probabilità per ogni punteggio esatto [home_goals][away_goals] 
        usando operazioni vettoriali NumPy (molto più veloce dei cicli for).
        """
        # 1. Calcolo vettoriale delle PMF di Poisson
        goals_range = np.arange(max_goals)
        p_home = poisson.pmf(goals_range, xg_home)
        p_away = poisson.pmf(goals_range, xg_away)

        # 2. Matrice base (prodotto esterno)
        matrix = np.outer(p_home, p_away)

        # 3. Applicazione vettoriale della correzione Dixon-Coles Tau
        tau = np.ones((max_goals, max_goals), dtype=float)
        
        # Casi speciali Dixon-Coles
        if xg_home > 0 and xg_away > 0:
            tau[0, 0] = 1.0 - (xg_home * xg_away * self.rho)
            tau[0, 1] = 1.0 + (xg_home * self.rho)
            tau[1, 0] = 1.0 + (xg_away * self.rho)
            tau[1, 1] = 1.0 - self.rho

        # Applica la correzione
        matrix *= tau

        # 4. Normalizzazione per assicurare che la somma sia 1.0
        return matrix / matrix.sum()

    def analyze_football_markets(
        self,
        home_team: str,
        away_team: str,
        xg_home: float,
        xg_away: float,
        bookmaker_odds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Analizza i mercati calcistici usando slicing vettoriale NumPy."""
        matrix = self.generate_score_matrix(xg_home, xg_away)
        book_odds = bookmaker_odds or {}

        # Slicing vettoriale per probabilità (estremamente veloce)
        prob_home = np.tril(matrix, -1).sum()       # i > j
        prob_draw = np.diag(matrix).sum()           # i == j
        prob_away = np.triu(matrix, 1).sum()        # i < j
        
        prob_1x = prob_home + prob_draw
        prob_x2 = prob_draw + prob_away

        # Griglia per calcoli basati sulla somma dei gol (i + j)
        goals_range = np.arange(matrix.shape[0])
        total_goals_grid = goals_range[:, None] + goals_range[None, :]

        prob_over_1_5 = np.sum(matrix[total_goals_grid > 1.5])
        prob_over_2_5 = np.sum(matrix[total_goals_grid > 2.5])
        prob_under_3_5 = np.sum(matrix[total_goals_grid < 3.5])
        
        prob_mg_1_4 = np.sum(matrix[(total_goals_grid >= 1) & (total_goals_grid <= 4)])
        prob_mg_2_4 = np.sum(matrix[(total_goals_grid >= 2) & (total_goals_grid <= 4)])

        # MultiGol Casa (es. 1-2 gol casa: righe 1 e 2, tutte le colonne)
        prob_home_mg_1_2 = matrix[1:3, :].sum()
        prob_home_over_1_5 = matrix[2:, :].sum()

        # Combo Protette
        # 1X + Over 1.5: (i >= j) AND (i + j > 1.5)
        mask_1x_over = (goals_range[:, None] >= goals_range[None, :]) & (total_goals_grid > 1.5)
        prob_1x_over_1_5 = np.sum(matrix[mask_1x_over])

        mask_1x_mg = (goals_range[:, None] >= goals_range[None, :]) & ((total_goals_grid >= 1) & (total_goals_grid <= 4))
        prob_1x_mg_1_4 = np.sum(matrix[mask_1x_mg])

        markets = {
            "MultiGol 1-2 Casa": {"prob": round(prob_home_mg_1_2, 3), "fair_odds": round(1.0 / max(0.01, prob_home_mg_1_2), 2)},
            "MultiGol 2-4 Totale": {"prob": round(prob_mg_2_4, 3), "fair_odds": round(1.0 / max(0.01, prob_mg_2_4), 2)},
            "1X + Over 1.5": {"prob": round(prob_1x_over_1_5, 3), "fair_odds": round(1.0 / max(0.01, prob_1x_over_1_5), 2)},
            "1X + MultiGol 1-4": {"prob": round(prob_1x_mg_1_4, 3), "fair_odds": round(1.0 / max(0.01, prob_1x_mg_1_4), 2)},
            "1X (Doppia Chance)": {"prob": round(prob_1x, 3), "fair_odds": round(1.0 / max(0.01, prob_1x), 2)},
            "Over 2.5": {"prob": round(prob_over_2_5, 3), "fair_odds": round(1.0 / max(0.01, prob_over_2_5), 2)},
        }

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

    # Alias per compatibilità con il codice esistente
    analyze_niche_markets = analyze_football_markets

    def analyze_corners(
        self,
        home_team: str,
        away_team: str,
        avg_corners_home: float,
        avg_corners_away: float,
        dispersion_factor: float = 1.5, # >1 indica overdispersion tipica dei corner
        bookmaker_odds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Modella i corner usando la Distribuzione Binomiale Negativa per gestire l'overdispersion.
        """
        # Parametrizzazione Binomiale Negativa da Media (mu) e Fattore di Dispersione (alpha)
        # Varianza = mu + alpha * mu^2. 
        # n (number of successes) = 1 / alpha
        # p (probability) = 1 / (1 + alpha * mu)
        
        def get_nbinom_params(mu: float, alpha: float) -> tuple[float, float]:
            n = 1.0 / alpha
            p = 1.0 / (1.0 + alpha * mu)
            return n, p

        # Assumiamo un alpha di default (es. 0.1) se dispersion_factor è passato come moltiplicatore
        alpha = 0.1 * dispersion_factor 
        
        n_home, p_home = get_nbinom_params(avg_corners_home, alpha)
        n_away, p_away = get_nbinom_params(avg_corners_away, alpha)

        max_corners = 20
        corners_range = np.arange(max_corners)

        # PMF vettoriali
        pmf_home = nbinom.pmf(corners_range, n_home, p_home)
        pmf_away = nbinom.pmf(corners_range, n_away, p_away)

        # Matrice congiunta (assumendo indipendenza tra corner casa e ospite, buona approssimazione)
        corner_matrix = np.outer(pmf_home, pmf_away)
        total_corners_grid = corners_range[:, None] + corners_range[None, :]

        prob_over_8_5 = np.sum(corner_matrix[total_corners_grid > 8.5])
        prob_over_9_5 = np.sum(corner_matrix[total_corners_grid > 9.5])
        prob_over_10_5 = np.sum(corner_matrix[total_corners_grid > 10.5])

        markets = {
            "Over 8.5 Corner Totali": {"prob": round(prob_over_8_5, 3), "fair_odds": round(1.0 / max(0.01, prob_over_8_5), 2)},
            "Over 9.5 Corner Totali": {"prob": round(prob_over_9_5, 3), "fair_odds": round(1.0 / max(0.01, prob_over_9_5), 2)},
            "Over 10.5 Corner Totali": {"prob": round(prob_over_10_5, 3), "fair_odds": round(1.0 / max(0.01, prob_over_10_5), 2)},
        }

        # Logica Edge per Corner (identica a quella calcistica)
        gems = []
        for m_name, data in markets.items():
            netwin_q = bookmaker_odds.get(m_name) if bookmaker_odds else None
            if netwin_q:
                edge = (data["prob"] * netwin_q - 1.0) * 100.0
                data["netwin_odds"] = netwin_q
                data["edge_pct"] = round(edge, 1)
                if edge >= 8.0 and netwin_q >= 1.50: # Soglia leggermente più bassa per i corner
                    gems.append({
                        "market": m_name,
                        "netwin_odds": netwin_q,
                        "fair_odds": data["fair_odds"],
                        "prob": data["prob"],
                        "edge_pct": round(edge, 1)
                    })

        return {
            "match": f"{home_team} vs {away_team}",
            "avg_corners_home": avg_corners_home,
            "avg_corners_away": avg_corners_away,
            "corner_markets": markets,
            "corner_gems": gems
        }

# Alias per retrocompatibilità
XgPoissonEngine = QuantitativeEngine

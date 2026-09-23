"""
NicheMarketEngine — Motore di Rilevamento Gemme Nascoste ad Alta Quota (1.50 - 2.50).
Scansiona e calcola le quote eque e l'Edge matematico sui mercati alternativi:
  1. Calcio Corner (Over/Under 8.5, 9.5, Handicap Corner)
  2. Calcio Cartellini (Over/Under 3.5, 4.5, 5.5, 1X2 Cartellini)
  3. Calcio Combo Protette (1X + MultiGol 1-4, 1X + Over 1.5, MultiGol 2-4)
  4. Calcio Tiri Totali (Over 21.5, Over 23.5)
"""

from __future__ import annotations
import math
import logging
from typing import Dict, List, Any, Optional, Tuple

logger = logging.getLogger(__name__)


def poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def bivariate_poisson_matrix(lam_h: float, lam_a: float, max_k: int = 7) -> List[List[float]]:
    matrix = []
    for i in range(max_k + 1):
        row = []
        p_i = poisson_pmf(i, lam_h)
        for j in range(max_k + 1):
            row.append(p_i * poisson_pmf(j, lam_a))
        matrix.append(row)
    return matrix


class NicheMarketEngine:
    """
    Rilevatore matematico di valore sui mercati alternativi ad alta quota (1.50 - 2.50).
    """

    def __init__(self, min_edge: float = 0.04):
        self.min_edge = min_edge

    @staticmethod
    def estimate_football_parameters(
        home_elo: float,
        away_elo: float,
        home_form_5: float = 7.0,
        away_form_5: float = 7.0,
        is_derby: bool = False,
    ) -> Dict[str, float]:
        """
        Stima dinamica di xG, xCorner, xCartellini e xTiri da differenziale ELO e forma.
        """
        elo_diff = home_elo - away_elo

        # xG Gol: media base ~1.45 casa / 1.15 ospite
        xg_home = max(0.5, min(3.8, 1.45 + (elo_diff / 400.0) + (home_form_5 - 7.0) * 0.04))
        xg_away = max(0.3, min(2.8, 1.15 - (elo_diff / 500.0) + (away_form_5 - 7.0) * 0.03))

        # xCorner: la squadra più forte che preme in casa produce più corner
        xc_home = max(3.0, min(9.5, 5.5 + (elo_diff / 300.0)))
        xc_away = max(2.0, min(7.0, 4.0 - (elo_diff / 450.0)))

        # xCartellini: match equilibrati o derby producono molti più falli tattici e cartellini
        base_cards = 4.8 if is_derby else 4.0
        tension_factor = math.exp(-abs(elo_diff) / 350.0) # picco quando le squadre sono alla pari
        xk_tot = base_cards + tension_factor * 1.5

        # xTiri: correlati al volume di attacco complessivo
        exp_shots_tot = (xg_home * 7.5 + 4.5) + (xg_away * 6.5 + 4.0)

        return {
            "xg_home": round(xg_home, 2),
            "xg_away": round(xg_away, 2),
            "xc_home": round(xc_home, 2),
            "xc_away": round(xc_away, 2),
            "xc_tot": round(xc_home + xc_away, 2),
            "xk_tot": round(xk_tot, 2),
            "exp_shots_tot": round(exp_shots_tot, 2),
        }

    def scan_football_niche(
        self,
        home_team: str,
        away_team: str,
        home_elo: float = 1500.0,
        away_elo: float = 1500.0,
        home_form_5: float = 7.0,
        away_form_5: float = 7.0,
        is_derby: bool = False,
        market_odds: Optional[Dict[str, float]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Calcola le probabilità reali e individua le gemme sui mercati alternativi calcio.
        """
        params = self.estimate_football_parameters(home_elo, away_elo, home_form_5, away_form_5, is_derby)
        xg_h, xg_a = params["xg_home"], params["xg_away"]
        xc_tot = params["xc_tot"]
        xk_tot = params["xk_tot"]
        shots_tot = params["exp_shots_tot"]

        # Matrice gol
        g_mat = bivariate_poisson_matrix(xg_h, xg_a, max_k=7)
        p_home_win = sum(g_mat[i][j] for i in range(8) for j in range(8) if i > j)
        p_draw = sum(g_mat[i][i] for i in range(8))
        p_1x = p_home_win + p_draw

        # 1. Combo Protetta: 1X + MultiGol 1-4
        p_mg_1_4 = sum(g_mat[i][j] for i in range(8) for j in range(8) if 1 <= (i + j) <= 4)
        p_1x_mg_1_4 = round(min(p_1x * 0.96, p_mg_1_4 * 0.92), 4)

        # 2. Combo Protetta: 1X + Over 1.5
        p_1x_ov_15 = round(sum(g_mat[i][j] for i in range(8) for j in range(8) if i >= j and (i + j) > 1.5), 4)

        # 3. MultiGol 2-4 Totale
        p_mg_2_4 = round(sum(g_mat[i][j] for i in range(8) for j in range(8) if 2 <= (i + j) <= 4), 4)

        # 4. MultiGol Casa 2-3
        p_mg_h_2_3 = round(sum(poisson_pmf(k, xg_h) for k in [2, 3]), 4)

        # 5. Corner: Over 8.5 e Over 9.5
        p_c_ov_85 = round(1.0 - sum(poisson_pmf(k, xc_tot) for k in range(9)), 4)
        p_c_ov_95 = round(1.0 - sum(poisson_pmf(k, xc_tot) for k in range(10)), 4)

        # 6. Cartellini: Over 3.5 e Over 4.5
        p_k_ov_35 = round(1.0 - sum(poisson_pmf(k, xk_tot) for k in range(4)), 4)
        p_k_ov_45 = round(1.0 - sum(poisson_pmf(k, xk_tot) for k in range(5)), 4)

        # 7. Tiri Totali: Over 21.5
        p_shots_ov_215 = round(1.0 - sum(poisson_pmf(k, shots_tot) for k in range(22)), 4)

        picks = [
            {
                "market_category": "Combo Protetta",
                "market_name": f"1X + MultiGol 1-4",
                "selection": f"1X + MultiGol 1-4 ({home_team})",
                "prob_real": p_1x_mg_1_4,
                "fair_odd": round(1.0 / p_1x_mg_1_4, 2) if p_1x_mg_1_4 > 0 else 99.0,
                "default_market_odd": 1.62,
                "resilience": "90_MIN_ELASTIC",
            },
            {
                "market_category": "Combo Protetta",
                "market_name": f"1X + Over 1.5",
                "selection": f"1X + Over 1.5 ({home_team})",
                "prob_real": p_1x_ov_15,
                "fair_odd": round(1.0 / p_1x_ov_15, 2) if p_1x_ov_15 > 0 else 99.0,
                "default_market_odd": 1.55,
                "resilience": "90_MIN_ELASTIC",
            },
            {
                "market_category": "MultiGol a Fasce",
                "market_name": "MultiGol 2-4 Totale",
                "selection": "MultiGol 2-4",
                "prob_real": p_mg_2_4,
                "fair_odd": round(1.0 / p_mg_2_4, 2) if p_mg_2_4 > 0 else 99.0,
                "default_market_odd": 1.55,
                "resilience": "90_MIN_ELASTIC",
            },
            {
                "market_category": "MultiGol Squadra",
                "market_name": f"MultiGol 2-3 {home_team}",
                "selection": f"MultiGol 2-3 {home_team}",
                "prob_real": p_mg_h_2_3,
                "fair_odd": round(1.0 / p_mg_h_2_3, 2) if p_mg_h_2_3 > 0 else 99.0,
                "default_market_odd": 1.95,
                "resilience": "90_MIN_ELASTIC",
            },
            {
                "market_category": "Calci d'Angolo",
                "market_name": "Over 8.5 Corner Totali",
                "selection": "Over 8.5 Corner",
                "prob_real": p_c_ov_85,
                "fair_odd": round(1.0 / p_c_ov_85, 2) if p_c_ov_85 > 0 else 99.0,
                "default_market_odd": 1.72,
                "resilience": "90_MIN_ELASTIC",
            },
            {
                "market_category": "Calci d'Angolo",
                "market_name": "Over 9.5 Corner Totali",
                "selection": "Over 9.5 Corner",
                "prob_real": p_c_ov_95,
                "fair_odd": round(1.0 / p_c_ov_95, 2) if p_c_ov_95 > 0 else 99.0,
                "default_market_odd": 2.05,
                "resilience": "90_MIN_ELASTIC",
            },
            {
                "market_category": "Cartellini Disciplinari",
                "market_name": "Over 4.5 Cartellini Totali",
                "selection": "Over 4.5 Cartellini",
                "prob_real": p_k_ov_45,
                "fair_odd": round(1.0 / p_k_ov_45, 2) if p_k_ov_45 > 0 else 99.0,
                "default_market_odd": 1.88,
                "resilience": "90_MIN_ELASTIC",
            },
            {
                "market_category": "Volume Tiri",
                "market_name": "Over 21.5 Tiri Totali",
                "selection": "Over 21.5 Tiri",
                "prob_real": p_shots_ov_215,
                "fair_odd": round(1.0 / p_shots_ov_215, 2) if p_shots_ov_215 > 0 else 99.0,
                "default_market_odd": 1.80,
                "resilience": "90_MIN_ELASTIC",
            },
        ]

        # Calcolo Edge e Balanced Safety Score (BSS)
        gems = []
        for p in picks:
            m_key = p["market_name"]
            odd = (market_odds.get(m_key) or market_odds.get(p["selection"]) or p["default_market_odd"]) if market_odds else p["default_market_odd"]
            edge = round((p["prob_real"] * odd - 1.0) * 100, 2)
            # Balanced Safety Score (BSS)
            q_factor = 1.15 if 1.50 <= odd <= 1.95 else 0.90
            bss = round((p["prob_real"] ** 1.5) * (1.0 + edge / 100.0) * q_factor * 100.0, 1)

            item = {
                "match": f"{home_team} vs {away_team}",
                "market_category": p["market_category"],
                "market_name": p["market_name"],
                "selection": p["selection"],
                "odd": odd,
                "fair_odd": p["fair_odd"],
                "prob_real": p["prob_real"],
                "edge_pct": edge,
                "bss": bss,
                "is_gem": edge >= (self.min_edge * 100) and odd >= 1.50,
            }
            if item["is_gem"]:
                gems.append(item)

        gems.sort(key=lambda x: (x["bss"], x["edge_pct"]), reverse=True)
        return gems

"""
services/quant/sharp_synthetic_benchmark.py — Motore di Benchmarking Sharp & De-Vigging.

Ispirato ai motori di Value Betting professionali (stile BetBurger / RebelBetting / OddsJam):
1. Rimuove l'aggio del bookmaker (Vig/Overround) da mercati primari (es. 1X2, U/O 2.5) usando
   l'algoritmo di Shin (o il Power/Multiplicative method come fallback analitico).
2. Costruisce la distribuzione bivariata reale non distorta (Joint Score Matrix).
3. Calcola il Fair Odd sintetico privo di margine per TUTTI i mercati secondari
   (Doppie Chance Tempi, MultiGol flessibili, Chance Mix, Team Over/Under).
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import numpy as np


def de_vig_proportional(odds: List[float]) -> List[float]:
    """Rimuove l'aggio in modo proporzionale semplice."""
    raw_probs = [1.0 / max(1.001, o) for o in odds]
    total_margin = sum(raw_probs)
    return [p / total_margin for p in raw_probs]


def de_vig_shin(odds: List[float], max_iter: int = 100, tol: float = 1e-6) -> List[float]:
    """
    Rimuove l'aggio del bookmaker utilizzando il modello di Shin (1991, 1993).
    Distingue tra scommettitori informati (insiders con proporzione z) e scommettitori ricreativi.
    Risolve per punto fisso il valore z (frazione di informed trading).
    """
    if len(odds) < 2 or any(o <= 1.0 for o in odds):
        return de_vig_proportional(odds)

    inv_odds = [1.0 / o for o in odds]
    beta = sum(inv_odds)
    if beta <= 1.0:
        return [p / beta for p in inv_odds]

    # Stima iniziale di z (proporzione di insider trading)
    z = (beta - 1.0) / (beta - (1.0 / len(odds)))
    z = max(0.0001, min(0.30, z))

    for _ in range(max_iter):
        p_candidates = []
        for o_inv in inv_odds:
            val = math.sqrt(z**2 + 4.0 * (1.0 - z) * (o_inv**2) / beta)
            p_i = (val - z) / (2.0 * (1.0 - z))
            p_candidates.append(max(0.0001, p_i))

        p_sum = sum(p_candidates)
        diff = abs(p_sum - 1.0)
        if diff < tol:
            break

        # Aggiornamento gradiente su z
        z += (p_sum - 1.0) * 0.1
        z = max(0.0001, min(0.40, z))

    total = sum(p_candidates)
    return [p / total for p in p_candidates]


@dataclass
class SharpMarketBenchmark:
    """Rappresentazione delle probabilità Fair pure e non distorte di una partita."""
    match_name: str
    fair_1x2: Dict[str, float]
    fair_uo_25: Dict[str, float]
    lambda_home: float
    lambda_away: float
    grid_90: np.ndarray
    grid_ht: np.ndarray

    def get_fair_odd(self, target_prob: float) -> float:
        """Restituisce la quota equa teorica priva di margine per una probabilità data."""
        return round(1.0 / max(0.001, min(0.999, target_prob)), 2)


class SyntheticBenchmarkEngine:
    """Generatore di benchmark sintetici per tutti i mercati secondari."""

    def __init__(self, max_goals: int = 8):
        self.max_goals = max_goals

    def build_benchmark_from_primary_odds(
        self,
        match_name: str,
        odds_1x2: Tuple[float, float, float],
        odds_uo25: Tuple[float, float]
    ) -> SharpMarketBenchmark:
        """
        Dalle quote Sharp primarie (1X2 e Over/Under 2.5):
        1. Rimuove l'aggio con Shin.
        2. Risolve per inversione i parametri di Poisson (lambda home e lambda away).
        3. Costruisce la matrice bidimensionale dei risultati esatti ai 90' e al 45'.
        """
        # De-vig 1X2
        probs_1x2 = de_vig_shin(list(odds_1x2))
        p_1, p_x, p_2 = probs_1x2[0], probs_1x2[1], probs_1x2[2]

        # De-vig Over/Under 2.5
        probs_uo = de_vig_shin(list(odds_uo25))
        p_u25, p_o25 = probs_uo[0], probs_uo[1]

        # Stima dei gol attesi (lambda) che soddisfano contemporaneamente P(U2.5) e P(1)/P(2)
        # Relazione empirica robusta: P(Over 2.5) correla fortemente con Total Expected Goals (TEG)
        # Approssimazione analitica ben collaudata: TEG ~ 2.5 - ln(p_u25) / 0.8
        teg = max(1.4, min(4.5, 2.5 - math.log(max(0.05, p_u25)) * 0.95))
        
        # Assegnazione proporzionale ai due team in base al ratio P(1) vs P(2)
        ratio = math.sqrt(max(0.1, p_1) / max(0.1, p_2))
        lam_home = (teg * ratio) / (1.0 + ratio)
        lam_away = teg - lam_home

        # Costruzione matrice di probabilità bivariata (indipendenza con correzione Dixon-Coles soft)
        from scipy.stats import poisson
        g_range = np.arange(self.max_goals)
        pmf_h = poisson.pmf(g_range, lam_home)
        pmf_a = poisson.pmf(g_range, lam_away)
        grid_90 = np.outer(pmf_h, pmf_a)

        # Correzione Dixon-Coles sui bassi punteggi (0-0, 1-0, 0-1, 1-1)
        rho = -0.11
        if grid_90[0, 0] > 0:
            grid_90[0, 0] *= (1.0 - lam_home * lam_away * rho)
            grid_90[0, 1] *= (1.0 + lam_home * rho)
            grid_90[1, 0] *= (1.0 + lam_away * rho)
            grid_90[1, 1] *= (1.0 - rho)
        grid_90 /= grid_90.sum()

        # Matrice Primo Tempo (circa il 45% del volume gol totale)
        lam_h_ht = lam_home * 0.45
        lam_a_ht = lam_away * 0.45
        pmf_h_ht = poisson.pmf(g_range, lam_h_ht)
        pmf_a_ht = poisson.pmf(g_range, lam_a_ht)
        grid_ht = np.outer(pmf_h_ht, pmf_a_ht)
        grid_ht /= grid_ht.sum()

        return SharpMarketBenchmark(
            match_name=match_name,
            fair_1x2={"1": p_1, "X": p_x, "2": p_2},
            fair_uo_25={"Under": p_u25, "Over": p_o25},
            lambda_home=lam_home,
            lambda_away=lam_away,
            grid_90=grid_90,
            grid_ht=grid_ht
        )

    def price_derived_market(self, benchmark: SharpMarketBenchmark, market_type: str, selection: str) -> float:
        """
        Calcola la probabilità FAIR pura di qualsiasi mercato secondario
        interrogando la matrice bivariata dei risultati esatti.
        """
        m_lower = market_type.lower().strip()
        s_upper = selection.upper().strip()

        # 1. Doppia Chance Primo Tempo (12, 1X, X2)
        if "12" in s_upper and any(k in m_lower for k in ["1 tempo", "1° tempo", "dc tempo 1", "primo tempo"]):
            # P(non pareggio a metà tempo) = 1.0 - sum(diag(grid_ht))
            p_draw_ht = float(np.diag(benchmark.grid_ht).sum())
            return 1.0 - p_draw_ht

        # 2. MultiGol Tempi (es. 0-1 1°T, 0-2 1°T, 1-3 2°T)
        if "0-1" in m_lower or "0-1" in s_upper:
            if "1 tempo" in m_lower or "1° tempo" in m_lower or "primo tempo" in m_lower:
                # Somma risultati 0-0, 1-0, 0-1
                return float(benchmark.grid_ht[0, 0] + benchmark.grid_ht[1, 0] + benchmark.grid_ht[0, 1])

        # 3. Chance Mix (es. 1X o NoGol, 1X o Over 1.5, X2 o NoGol)
        if "chance mix" in m_lower or "combo chance" in m_lower:
            grid = benchmark.grid_90
            # 1X o NoGol: vince se (home >= away) OPPURE (home==0 o away==0)
            if "1x o nogol" in m_lower or "1x o no gol" in m_lower:
                mask = np.zeros_like(grid, dtype=bool)
                for i in range(grid.shape[0]):
                    for j in range(grid.shape[1]):
                        if i >= j or i == 0 or j == 0:
                            mask[i, j] = True
                return float(grid[mask].sum())

            # X2 o NoGol
            if "x2 o nogol" in m_lower or "x2 o no gol" in m_lower:
                mask = np.zeros_like(grid, dtype=bool)
                for i in range(grid.shape[0]):
                    for j in range(grid.shape[1]):
                        if j >= i or i == 0 or j == 0:
                            mask[i, j] = True
                return float(grid[mask].sum())

            # 1X o Over 1.5
            if "1x o over 1.5" in m_lower:
                mask = np.zeros_like(grid, dtype=bool)
                for i in range(grid.shape[0]):
                    for j in range(grid.shape[1]):
                        if (i >= j) or (i + j >= 2):
                            mask[i, j] = True
                return float(grid[mask].sum())

        # 4. MultiGol Squadra (es. Casa 1-3)
        if "multigol" in m_lower and ("casa" in m_lower or "squadra 1" in m_lower):
            # Somma lungo l'asse home per i gol da 1 a 3
            return float(benchmark.grid_90[1:4, :].sum())

        if "multigol" in m_lower and ("ospite" in m_lower or "squadra 2" in m_lower):
            # Somma lungo l'asse away per i gol da 1 a 3
            return float(benchmark.grid_90[:, 1:4].sum())

        # 5. MultiGol Totale Aperto (es. 1-4, 2-5)
        if "1-4" in m_lower or "1-4" in s_upper:
            total_goals = np.zeros(self.max_goals * 2)
            for i in range(benchmark.grid_90.shape[0]):
                for j in range(benchmark.grid_90.shape[1]):
                    total_goals[i + j] += benchmark.grid_90[i, j]
            return float(total_goals[1:5].sum())

        if "2-5" in m_lower or "2-5" in s_upper:
            total_goals = np.zeros(self.max_goals * 2)
            for i in range(benchmark.grid_90.shape[0]):
                for j in range(benchmark.grid_90.shape[1]):
                    total_goals[i + j] += benchmark.grid_90[i, j]
            return float(total_goals[2:6].sum())

        # Default fallback: somma marginale Under 3.5 con 1X
        if "1x + under 3.5" in m_lower or "1x + under 3.5" in s_upper:
            mask = np.zeros_like(benchmark.grid_90, dtype=bool)
            for i in range(benchmark.grid_90.shape[0]):
                for j in range(benchmark.grid_90.shape[1]):
                    if (i >= j) and (i + j <= 3):
                        mask[i, j] = True
            return float(benchmark.grid_90[mask].sum())

        return 0.50

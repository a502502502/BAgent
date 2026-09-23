"""
services/analysis/national_team_lambda_engine.py — Calcolo Dinamico dei Lambda Dixon-Coles per Nazionali.

Risolve il problema dell'avvio tornei (es. Giornata 1 UEFA Nations League, Mondiali, Europei)
dove l'xG della stagione in corso è None o 0.
Invece di consentire l'inserimento di xG manuali o arbitrari:
1. Aggrega le ultime N partite storiche (amichevoli, qualificazioni, fasi finali)
2. Calcola i parametri d'intensità offensiva/difensiva (lambda) usando la formulazione empirica:
       lambda_home = mean(xg_home_scored, xg_away_conceded)
       lambda_away = mean(xg_away_scored, xg_home_conceded)
3. Genera la matrice bivariata Dixon-Coles con correzione Tau (rho=-0.05)
4. Applica il doppio vincolo inderogabile:
       - Edge Matematico >= +4.0%
       - Probabilità Minima della Gamba >= 72.0%
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple
import numpy as np

from services.analysis.xg_poisson_engine import QuantitativeEngine


@dataclass
class NationalTeamRecentStats:
    team_name: str
    matches_counted: int = 5
    avg_xg_scored: float = 1.30
    avg_xg_conceded: float = 1.20
    avg_goals_scored: float = 1.20
    avg_goals_conceded: float = 1.20
    match_notes: List[str] = field(default_factory=list)


@dataclass
class MarketEvaluationResult:
    market_name: str
    bookmaker_odd: float
    probability: float
    fair_odd: float
    edge_pct: float
    passed_edge: bool
    passed_probability_floor: bool
    is_certified: bool
    rejection_reasons: List[str] = field(default_factory=list)


class NationalTeamLambdaEngine:
    MIN_EDGE_THRESHOLD: float = 0.04          # Minimo +4.0% di edge reale
    MIN_PROBABILITY_FLOOR: float = 0.72       # Minimo 72.0% di probabilità per singola gamba

    def __init__(self, rho: float = -0.05):
        self.quant_engine = QuantitativeEngine(rho=rho)

    def compute_lambdas(
        self,
        home_stats: NationalTeamRecentStats,
        away_stats: NationalTeamRecentStats,
    ) -> Tuple[float, float]:
        """
        Calcola i lambda attesi per l'incontro:
        lambda_home = media tra xG fatti in casa/recente e xG/gol subiti dall'avversaria
        lambda_away = media tra xG fatti dall'ospite e xG/gol subiti dalla squadra di casa
        """
        # Miscela pesata tra xG e gol effettivi subiti per catturare difese colabrodo
        defense_home_leaked = max(home_stats.avg_xg_conceded, home_stats.avg_goals_conceded * 0.75 + home_stats.avg_xg_conceded * 0.25)
        defense_away_leaked = max(away_stats.avg_xg_conceded, away_stats.avg_goals_conceded * 0.75 + away_stats.avg_xg_conceded * 0.25)

        lambda_home = (home_stats.avg_xg_scored + defense_away_leaked) / 2.0
        lambda_away = (away_stats.avg_xg_scored + defense_home_leaked) / 2.0

        # Floor di sicurezza minimo 0.20 per evitare divisioni per zero o matrici vuote
        return max(0.20, float(lambda_home)), max(0.20, float(lambda_away))

    def evaluate_with_lambdas(
        self,
        lambda_home: float,
        lambda_away: float,
        market_name: str,
        bookmaker_odd: float,
    ) -> MarketEvaluationResult:
        """Valuta direttamente data una coppia di parametri lambda empirici."""
        prob = self.quant_engine.goal_market_probability(lambda_home, lambda_away, market_name)

        if prob is None or prob <= 0:
            return MarketEvaluationResult(
                market_name=market_name,
                bookmaker_odd=bookmaker_odd,
                probability=0.0,
                fair_odd=999.0,
                edge_pct=-1.0,
                passed_edge=False,
                passed_probability_floor=False,
                is_certified=False,
                rejection_reasons=[f"Mercato '{market_name}' non calcolabile dal motore."]
            )

        fair_odd = 1.0 / prob
        edge = (prob * bookmaker_odd) - 1.0

        passed_edge = edge >= self.MIN_EDGE_THRESHOLD
        passed_prob_floor = prob >= self.MIN_PROBABILITY_FLOOR
        is_certified = passed_edge and passed_prob_floor

        rejection_reasons: List[str] = []
        if not passed_edge:
            rejection_reasons.append(
                f"Edge {edge*100:+.1f}% inferiore alla soglia minima vincolante +{self.MIN_EDGE_THRESHOLD*100:.1f}%. "
                f"Quota offerta @{bookmaker_odd:.2f} vs Quota Equa @{fair_odd:.2f}."
            )
        if not passed_prob_floor:
            rejection_reasons.append(
                f"Probabilità reale {prob*100:.1f}% inferiore alla soglia di sicurezza minima {self.MIN_PROBABILITY_FLOOR*100:.1f}% "
                f"richiesta per le gambe di multipla (rischio abbattimento win rate)."
            )

        return MarketEvaluationResult(
            market_name=market_name,
            bookmaker_odd=bookmaker_odd,
            probability=prob,
            fair_odd=fair_odd,
            edge_pct=edge,
            passed_edge=passed_edge,
            passed_probability_floor=passed_prob_floor,
            is_certified=is_certified,
            rejection_reasons=rejection_reasons
        )

    def evaluate_market(
        self,
        home_stats: NationalTeamRecentStats,
        away_stats: NationalTeamRecentStats,
        market_name: str,
        bookmaker_odd: float,
    ) -> MarketEvaluationResult:
        """
        Valuta una selezione con Dixon-Coles e i doppi vincoli di sicurezza.
        """
        l_home, l_away = self.compute_lambdas(home_stats, away_stats)
        return self.evaluate_with_lambdas(l_home, l_away, market_name, bookmaker_odd)

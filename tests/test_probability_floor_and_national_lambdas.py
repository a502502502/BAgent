"""
tests/test_probability_floor_and_national_lambdas.py

Test del vincolo doppio:
1. Soglia Minima di Probabilità della Gamba (>= 72.0%)
2. Motore Dixon-Coles per Nazionali (NationalTeamLambdaEngine)
"""

import pytest
from services.analysis.national_team_lambda_engine import (
    NationalTeamLambdaEngine,
    NationalTeamRecentStats,
)
from services.betting.strict_ticket_pipeline import MarketCandidate, StrictTicketPipeline


def test_national_team_lambda_engine_serbia_greece():
    engine = NationalTeamLambdaEngine()
    # Dati reali ultime 5 partite (Cursor audit):
    # Serbia: 1.35 xG fatti, 2.60 gol subiti (colabrodo)
    # Grecia: 1.29 xG fatti, 0.40 gol segnati
    serbia = NationalTeamRecentStats(
        team_name="Serbia",
        avg_xg_scored=1.35,
        avg_xg_conceded=1.80,
        avg_goals_scored=1.00,
        avg_goals_conceded=2.60,
    )
    greece = NationalTeamRecentStats(
        team_name="Greece",
        avg_xg_scored=1.29,
        avg_xg_conceded=0.90,
        avg_goals_scored=0.40,
        avg_goals_conceded=0.80,
    )

    res = engine.evaluate_market(
        home_stats=serbia,
        away_stats=greece,
        market_name="Under 2.5",
        bookmaker_odd=1.73,
    )

    assert not res.is_certified
    assert res.probability < 0.60  # P ~ 54.2%
    assert res.edge_pct < 0.0      # Edge negativo (-6.3%)
    assert not res.passed_edge
    assert not res.passed_probability_floor


def test_national_team_lambda_engine_portugal_wales():
    engine = NationalTeamLambdaEngine()
    # Dati reali ultime 5 partite (Cursor audit):
    # Portogallo vs Galles: lambda_home=1.38, lambda_away=1.69
    res = engine.evaluate_with_lambdas(
        lambda_home=1.38,
        lambda_away=1.69,
        market_name="Under 3.5",
        bookmaker_odd=1.62,
    )

    assert not res.is_certified
    # P ~ 63.3%, sotto la soglia minima del 72%
    assert res.probability < 0.72
    assert not res.passed_probability_floor
    # Edge ~ +2.6%, sotto il +4.0%
    assert res.edge_pct < 0.04
    assert not res.passed_edge


def test_strict_pipeline_blocks_leg_below_72_percent_probability():
    pipeline = StrictTicketPipeline()
    # Mock candidato con edge positivo (+15.4% >= +4%) ma probabilità < 72% (48.1% < 72%)
    candidate = MarketCandidate(
        match_name="Team A vs Team B",
        tournament="Serie A",
        market_name="Over 2.5",
        bookmaker_odd=2.40,
        xg_home=1.4,
        xg_away=1.2,
        sixth_sense_analysis="Buon volume di tiri su entrambi i lati.",
    )

    rep = pipeline.validate_candidate(candidate)
    assert not rep.passed
    assert rep.stage_failed == 6
    assert "PROBABILITÀ INSUFFICIENTE SOTTO SOGLIA 72%" in rep.rejection_reason
    assert rep.real_probability < 0.72


def test_strict_pipeline_accepts_leg_meeting_both_edge_and_probability_floor():
    pipeline = StrictTicketPipeline()
    # xG 1.8 vs 1.6 su Over 1.5: P = 85.7% (>= 72%), quota 1.22 -> Edge = +4.6% (>= +4%)
    candidate = MarketCandidate(
        match_name="Netherlands vs Germany",
        tournament="UEFA Nations League",
        market_name="Over 1.5",
        bookmaker_odd=1.22,
        xg_home=1.8,
        xg_away=1.6,
        sixth_sense_analysis="Olanda e Germania entrambe votate all attacco verticale; xG combinato elevato.",
    )

    rep = pipeline.validate_candidate(candidate)
    assert rep.passed
    assert rep.stage_failed is None
    assert rep.real_probability >= 0.72
    assert rep.mathematical_edge >= 0.04

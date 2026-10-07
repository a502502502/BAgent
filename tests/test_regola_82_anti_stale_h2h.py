"""
tests/test_regola_82_anti_stale_h2h.py — Verifica Regola #82: Divieto Assoluto Motivazioni H2H Obsolete.
"""

import pytest
from services.betting.strict_ticket_pipeline import MarketCandidate, StrictTicketPipeline


def _make_candidate(match: str, analysis: str, odd: float = 1.85) -> MarketCandidate:
    return MarketCandidate(
        match_name=match,
        tournament="Serie A",
        market_name="Goal",
        bookmaker_odd=odd,
        xg_home=1.5,
        xg_away=1.3,
        sixth_sense_analysis=analysis,
        home_matches_played=5,
        away_matches_played=5,
        kickoff_time="2026-10-11 15:00 CEST",
    )


def test_gate_008_blocks_stale_multi_year_h2h_without_contemporary_context():
    pipeline = StrictTicketPipeline()
    # Motivazione basata solo su vecchi H2H
    analysis = "Serie storica Oddspedia: 8 degli ultimi 9 precedenti tra Sassuolo e Milan sono terminati in Gol."
    c = _make_candidate("Sassuolo vs Milan", analysis=analysis)
    report = pipeline.validate_candidate(c)

    assert not report.passed
    assert report.stage_failed == 0
    assert "REGOLA #82" in report.rejection_reason
    assert "ANTI-STALE-H2H BIAS" in report.rejection_reason


def test_gate_008_allows_contemporary_season_2026_metrics():
    pipeline = StrictTicketPipeline()
    # Motivazione basata su dati attuali 2026 e xG
    analysis = "Dati stagione 2026: Como baricentro alto e 1.68 xG concessi p90. Roma sempre a segno in trasferta con transizioni verticali."
    c = _make_candidate("Como vs Roma", analysis=analysis)
    report = pipeline.validate_candidate(c)

    # Il gate 0.08 non deve bloccare
    if not report.passed:
        assert "REGOLA #82" not in (report.rejection_reason or "")


def test_gate_008_allows_h2h_when_corroborated_by_current_2026_context():
    pipeline = StrictTicketPipeline()
    # Se la serie H2H è esplicitamente verificata con continuità tecnica e dati 2026/27
    analysis = "Negli ultimi 6 confronti diretti trend confermato dai dati di questo campionato 2026 con xG sopra media."
    c = _make_candidate("IF Gnistan vs Inter Turku", analysis=analysis)
    report = pipeline.validate_candidate(c)

    if not report.passed:
        assert "REGOLA #82" not in (report.rejection_reason or "")

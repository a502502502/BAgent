"""
tests/test_regola_76_match_datetime.py — Verifica Regola #76: Data e Ora Obbligatorie per Ogni Partita.
"""

import pytest
from services.betting.strict_ticket_pipeline import MarketCandidate, StrictTicketPipeline


def _make_candidate(match: str, kickoff: str | None = None, odd: float = 1.35) -> MarketCandidate:
    return MarketCandidate(
        match_name=match,
        tournament="Brasileirao Serie A",
        market_name="1X",
        bookmaker_odd=odd,
        xg_home=1.5,
        xg_away=0.9,
        sixth_sense_analysis="Fattore campo marcato.",
        home_matches_played=5,
        away_matches_played=5,
        kickoff_time=kickoff,
    )


def test_gate_005_blocks_missing_hour():
    pipeline = StrictTicketPipeline()
    # Data presente ma priva di orario
    c = _make_candidate("Flamengo vs Vasco", kickoff="2026-10-09")
    report = pipeline.validate_candidate(c)

    assert not report.passed
    assert report.stage_failed == 0
    assert "REGOLA #76" in report.rejection_reason
    assert "ORA MANCANTE" in report.rejection_reason


def test_gate_005_blocks_past_season():
    pipeline = StrictTicketPipeline()
    c = _make_candidate("Flamengo vs Vasco", kickoff="2024-10-09 20:00 CEST")
    report = pipeline.validate_candidate(c)

    assert not report.passed
    assert report.stage_failed == 0
    assert "DATA NON ATTUALE" in report.rejection_reason


def test_gate_005_accepts_valid_date_and_time():
    pipeline = StrictTicketPipeline()
    c = _make_candidate("Flamengo vs Vasco", kickoff="2026-10-09 00:30 CEST")
    report = pipeline.validate_candidate(c)

    # Il controllo temporale Gate 0.05 deve passare
    if not report.passed:
        assert report.stage_failed != 0


def test_validate_ticket_blocks_missing_kickoff():
    pipeline = StrictTicketPipeline()
    c1 = _make_candidate("Flamengo vs Vasco", kickoff="2026-10-09 00:30 CEST")
    c2 = _make_candidate("Palmeiras vs Gremio", kickoff=None)  # Kickoff assente!

    ticket_rep = pipeline.validate_ticket([c1, c2], current_bankroll=50.0, proposed_stake=2.0)

    assert not ticket_rep.passed
    assert any("REGOLA #76: DATA E ORA MANCANTI" in r for r in ticket_rep.rejection_reasons)
    assert any("Palmeiras vs Gremio" in r for r in ticket_rep.rejection_reasons)


def test_validate_ticket_accepts_when_all_legs_have_kickoff():
    pipeline = StrictTicketPipeline()
    c1 = _make_candidate("Flamengo vs Vasco", kickoff="2026-10-09 00:30 CEST")
    c2 = _make_candidate("Palmeiras vs Gremio", kickoff="2026-10-09 02:45 CEST")

    ticket_rep = pipeline.validate_ticket([c1, c2], current_bankroll=50.0, proposed_stake=2.0)

    # Nessun rifiuto per Regola #76
    assert not any("REGOLA #76" in r for r in ticket_rep.rejection_reasons)

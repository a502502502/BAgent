from datetime import date

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from harness.candidates import pipeline, selection
from services.betting.kelly_staking_engine import KellyStakingEngine


@settings(max_examples=20, deadline=None)
@given(st.dates(min_value=date(2026, 1, 1), max_value=date(2026, 12, 28)))
def test_a_date_without_a_clock_is_rule_76(day):
    report = pipeline().validate_candidate(selection(kickoff_time=day.isoformat()))
    assert report.passed is False
    assert report.stage_failed == 0
    assert "REGOLA #76" in (report.rejection_reason or "")


@settings(max_examples=20, deadline=None)
@given(st.floats(min_value=1.20, max_value=1.64, allow_nan=False, allow_infinity=False))
def test_straight_home_win_under_165_is_blocked(odd):
    report = pipeline().validate_candidate(
        selection(market_name="1", market_type="1X2", bookmaker_odd=odd)
    )
    assert report.passed is False
    assert "DIVIETO 1/2 FISSO" in (report.rejection_reason or "")


@settings(max_examples=30, deadline=None)
@given(
    st.floats(min_value=1.05, max_value=6.0, allow_nan=False, allow_infinity=False),
    st.floats(min_value=0.05, max_value=0.95, allow_nan=False, allow_infinity=False),
    st.floats(min_value=25.0, max_value=500.0, allow_nan=False, allow_infinity=False),
)
def test_kelly_stake_stays_inside_the_eight_percent_cap(odds, probability, bankroll):
    stake = KellyStakingEngine(bankroll).calculate_stake(odds, probability).recommended_stake
    assert stake <= bankroll * 0.08 + 1e-6


@settings(max_examples=10, deadline=None)
@given(st.floats(min_value=1.25, max_value=1.90, allow_nan=False, allow_infinity=False))
def test_passed_edge_matches_probability_times_odds(odd):
    report = pipeline().validate_candidate(selection(bookmaker_odd=odd))
    if not report.passed:
        return
    assert report.mathematical_edge == pytest.approx((report.real_probability * odd) - 1.0)

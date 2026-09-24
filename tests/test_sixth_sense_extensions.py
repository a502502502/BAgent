"""Arbitro, ritorno, corner e decadimento non muovono il modello se il dato manca."""

from datetime import date

import pytest

from services.football.sixth_sense.calibration import (
    INTERNAL_WEIGHT_CAP,
    LambdaSample,
    fit_factors,
    internal_weight,
    sample_decay,
)
from services.football.sixth_sense.lambda_context import (
    AGGREGATE_CHASE,
    AGGREGATE_LEAK,
    AGGREGATE_MANAGE,
    CORNER_DOMINANT_BOOST,
    CORNER_PARKED_FACTOR,
    REFEREE_ATTACK_BOOST,
    MatchContext,
    market_context_veto,
    project_attack,
    project_corners,
)


def test_severe_referee_lifts_both_attacks_and_blocks_a_card_under():
    attack = project_attack(1.50, 1.20, MatchContext(referee_cards_per_game=5.4))
    assert attack.xg_home == pytest.approx(1.50 * REFEREE_ATTACK_BOOST)
    assert attack.xg_away == pytest.approx(1.20 * REFEREE_ATTACK_BOOST)
    assert attack.veto_sanction
    assert market_context_veto("Under 4.5 Cartellini", attack) == "arbitro severo: under cartellini"


def test_permissive_referee_and_a_missing_profile_leave_the_lambdas():
    permissive = project_attack(1.50, 1.20, MatchContext(referee_style="permissive"))
    missing = project_attack(1.50, 1.20, MatchContext())
    assert permissive.xg_home == missing.xg_home == 1.50
    assert permissive.xg_away == missing.xg_away == 1.20
    assert permissive.veto_sanction is False
    assert missing.veto_sanction is False


def test_two_goal_first_leg_lead_manages_one_side_and_opens_the_other():
    attack = project_attack(1.50, 1.00, MatchContext(first_leg_home=3, first_leg_away=0))
    assert attack.xg_home == pytest.approx(1.50 * AGGREGATE_MANAGE * AGGREGATE_LEAK)
    assert attack.xg_away == pytest.approx(1.00 * AGGREGATE_CHASE)
    assert attack.veto_chase_away
    assert market_context_veto("X2 + Under 3.5", attack).startswith("ritorno")


def test_a_one_goal_lead_or_a_missing_leg_does_not_change_the_match():
    narrow = project_attack(1.50, 1.00, MatchContext(first_leg_home=1, first_leg_away=0))
    missing = project_attack(1.50, 1.00, MatchContext(first_leg_home=3, first_leg_away=None))
    assert narrow.xg_home == missing.xg_home == 1.50
    assert narrow.xg_away == missing.xg_away == 1.00
    assert narrow.veto_chase_home is False and narrow.veto_chase_away is False


def test_dominant_attack_boosts_one_corner_line_and_cuts_the_parked_side():
    projected = project_corners(8.0, 3.0, MatchContext(), xg_home=2.40, xg_away=0.70)
    assert projected.corners_home == pytest.approx(8.0 * CORNER_DOMINANT_BOOST)
    assert projected.corners_away == pytest.approx(3.0 * CORNER_PARKED_FACTOR)
    assert projected.base_home == 8.0


def test_corto_muso_away_is_the_side_that_earns_the_corners():
    projected = project_corners(6.0, 5.0, MatchContext(corto_muso_away=True), xg_home=1.2, xg_away=1.1)
    assert projected.corners_away == pytest.approx(5.0 * CORNER_DOMINANT_BOOST)
    assert projected.corners_home == pytest.approx(6.0 * CORNER_PARKED_FACTOR)


def test_missing_corner_averages_stay_on_the_base():
    projected = project_corners(None, 4.0, MatchContext(corto_muso_home=True))
    assert projected.corners_home == 0.0
    assert projected.corners_away == 4.0
    assert projected.notes == ("corner non forniti: proiezione base",)


def test_sample_decay_steps_at_45_and_90_days_and_ignores_the_future():
    as_of = date(2026, 9, 24)
    assert sample_decay("2026-09-01", as_of) == 1.0
    assert sample_decay("2026-08-10", as_of) == 1.0
    assert sample_decay("2026-07-20", as_of) == 0.5
    assert sample_decay("2026-05-01", as_of) == 0.25
    assert sample_decay("2026-10-01", as_of) == 0.0


def test_old_matches_do_not_fill_the_group_and_the_cap_stays_at_thirty_percent():
    as_of = date(2026, 9, 24)
    old = [
        LambdaSample(
            season="2026-27",
            match_date="2026-05-01",
            home_team=f"H{day}",
            away_team=f"A{day}",
            base_xg_home=2.0,
            base_xg_away=1.0,
            projected_xg_home=2.0,
            projected_xg_away=1.0,
            rotation_risk=True,
            actual_home_goals=0,
            actual_away_goals=0,
        )
        for day in range(8)
    ]
    assert fit_factors(old, as_of)[0].used is False
    assert internal_weight(100) == INTERNAL_WEIGHT_CAP
    recent = []
    for day in range(40):
        recent.append(
            LambdaSample(
                "2026-27",
                "2026-09-20",
                f"C{day}",
                f"D{day}",
                2.0,
                1.0,
                2.0,
                1.0,
                actual_home_goals=2,
                actual_away_goals=1,
            )
        )
        recent.append(
            LambdaSample(
                "2026-27",
                "2026-09-20",
                f"T{day}",
                f"U{day}",
                2.0,
                1.0,
                1.4,
                0.7,
                rotation_risk=True,
                actual_home_goals=0,
                actual_away_goals=0,
            )
        )
    rotation = fit_factors(recent, as_of)[0]
    assert rotation.used is True
    assert rotation.internal_weight == INTERNAL_WEIGHT_CAP
    assert abs(rotation.fitted - rotation.prior) <= INTERNAL_WEIGHT_CAP * abs(0.50 - rotation.prior) + 1e-9

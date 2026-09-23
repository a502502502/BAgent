"""Combo gol, linee corner e tetto Kelly prezzati sulla matrice, non sul nome."""

from services.analysis.xg_poisson_engine import QuantitativeEngine
from services.betting.kelly_staking_engine import KellyStakingEngine


def test_result_plus_total_is_the_intersection():
    engine = QuantitativeEngine()
    combo = engine.goal_market_probability(1.7, 1.2, "1 + Over 1.5")
    bare_total = engine.goal_market_probability(1.7, 1.2, "Over 1.5")
    intersection = engine.joint_goal_probability(1.7, 1.2, ["1", "Over 1.5"])
    assert combo == intersection
    assert combo < bare_total


def test_chance_mix_or_is_not_priced_as_and():
    engine = QuantitativeEngine()
    union = engine.goal_market_probability(1.7, 1.2, "Chance Mix: 1X o Over 1.5")
    intersection = engine.goal_market_probability(1.7, 1.2, "1X + Over 1.5")
    assert union > intersection
    assert union > 0.90


def test_double_chance_keeps_the_result_on_other_lines():
    engine = QuantitativeEngine()
    combo = engine.goal_market_probability(1.7, 1.2, "X2 + Under 3.5")
    under_only = engine.goal_market_probability(1.7, 1.2, "Under 3.5")
    assert combo == engine.joint_goal_probability(1.7, 1.2, ["X2", "Under 3.5"])
    assert combo < under_only


def test_team_multigol_uses_the_stated_band():
    engine = QuantitativeEngine()
    wide = engine.goal_market_probability(1.7, 1.2, "MultiGol 1-3 Casa")
    narrow = engine.goal_market_probability(1.7, 1.2, "MultiGol 2-3 Casa")
    assert wide is not None and narrow is not None
    assert narrow < wide


def test_unmapped_result_combo_is_not_guessed():
    engine = QuantitativeEngine()
    assert engine.goal_market_probability(1.7, 1.2, "1X2 + Over 1.5") is None


def test_opposite_results_on_the_same_match_have_empty_intersection():
    engine = QuantitativeEngine()
    home = engine.goal_market_probability(1.7, 1.2, "1")
    away = engine.goal_market_probability(1.7, 1.2, "2")
    joint = engine.joint_goal_probability(1.7, 1.2, ["1", "2"])
    assert joint == 0.0
    assert home * away > joint


def test_corner_line_does_not_match_inside_a_longer_number():
    engine = QuantitativeEngine()
    over_8_5 = engine.corner_market_probability(5.0, 5.0, "Over 8.5 Corner Totali")
    over_18_5 = engine.corner_market_probability(5.0, 5.0, "Over 18.5 Corner Totali")
    assert over_8_5 is not None
    assert over_18_5 is None


def test_minimum_stake_cannot_break_the_eight_percent_cap():
    engine = KellyStakingEngine(20.0)
    recommendation = engine.calculate_stake(odds=3.0, estimated_prob=0.50)
    assert recommendation.recommended_stake == 0.0
    assert recommendation.recommended_stake <= 20.0 * 0.08


def test_daily_allocator_does_not_lift_stakes_back_over_the_cap():
    engine = KellyStakingEngine(100.0)
    tickets = [{"odds": 2.0, "prob": 0.52} for _ in range(13)]
    allocated = engine.allocate_daily_tickets(tickets)
    total = sum(item["calculated_stake"] for item in allocated)
    assert total <= 100.0 * 0.25

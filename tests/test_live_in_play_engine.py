"""Il live non eredita percentuali fisse: la matrice dei minuti rimanenti decide."""

import pytest

from services.betting.netwin_market_parser import parse_netwin_selection
from services.live.live_in_play_engine import (
    CORNER_PARKED,
    CORNER_SIEGE,
    next_goal_probabilities,
    price_live_market,
    project_residual,
    residual_time_fraction,
    scan_live_book,
)
from services.live.live_momentum_sniper import LiveMatchSnapshot, LiveMomentumSniper


def test_remaining_time_uses_stoppage_and_never_drops_to_zero():
    assert residual_time_fraction(72, 4) == pytest.approx(22 / 90)
    assert residual_time_fraction(96, 4) == pytest.approx(1 / 90)


def test_red_card_scales_the_residual_attacks():
    base = project_residual(1.8, 1.1, 72, home_shots=0, away_shots=0)
    short = project_residual(1.8, 1.1, 72, away_reds=1, home_shots=0, away_shots=0)
    assert short.lambda_home == pytest.approx(base.lambda_home * 1.08)
    assert short.lambda_away == pytest.approx(base.lambda_away * 0.72)
    assert any("ospite in 10" in note for note in short.notes)


def test_next_goal_and_score_matrix_are_distributions():
    state = project_residual(1.6, 1.2, 60)
    home, away, none = next_goal_probabilities(state.lambda_home, state.lambda_away)
    assert home + away + none == pytest.approx(1.0)
    assert float(state.matrix.sum()) == pytest.approx(1.0)
    assert home > away


def test_a_settled_over_is_not_resold():
    state = project_residual(1.8, 1.1, 70, home_goals=2, away_goals=0)
    priced, rejected = scan_live_book(
        state,
        {"Over 0.5": 1.55},
        home_goals=2,
        away_goals=0,
    )
    assert priced == ()
    assert "determinato" in rejected[0].reason


def test_short_price_and_thin_slice_stay_out_of_the_live_spot():
    open_game = project_residual(2.4, 1.8, 40, home_goals=0, away_goals=0, home_shots=6, away_shots=6)
    probability = price_live_market(open_game, "Over 0.5", home_goals=0, away_goals=0)
    assert probability is not None and probability >= 0.72
    short, _ = scan_live_book(open_game, {"Over 0.5": 1.25}, home_goals=0, away_goals=0)
    assert short == ()
    late = project_residual(1.2, 0.9, 75, home_goals=0, away_goals=0, home_shots=4, away_shots=4)
    thin, rejected = scan_live_book(late, {"Over 1.5": 1.70}, home_goals=0, away_goals=0)
    assert thin == ()
    assert "probabilità" in rejected[0].reason


def test_a_live_price_inside_the_band_becomes_a_signal_the_parser_can_click():
    state = project_residual(2.4, 1.8, 40, home_goals=0, away_goals=0, home_shots=6, away_shots=6)
    priced, _rejected = scan_live_book(state, {"Over 0.5": 1.55}, home_goals=0, away_goals=0)
    assert len(priced) == 1
    gem = priced[0]
    assert gem.book_odd == 1.55
    assert gem.probability >= 0.72
    assert gem.edge == pytest.approx(gem.probability * 1.55 - 1.0)
    assert gem.edge >= 0.05
    assert 0.015 <= gem.stake_pct <= 0.030

    snapshot = LiveMatchSnapshot(
        fixture_id="t",
        match_name="Casa vs Ospite",
        minute=40,
        home_team="Casa",
        away_team="Ospite",
        home_goals=0,
        away_goals=0,
        home_shots=6,
        away_shots=6,
        xg_home=2.4,
        xg_away=1.8,
    )
    signal = LiveMomentumSniper().evaluate_live_match(snapshot, book_odds={"Over 0.5": 1.55})
    assert signal is not None
    assert signal.exact_selection == "Over 0.5"
    assert parse_netwin_selection("", signal.exact_selection).family == "OU"
    assert parse_netwin_selection(signal.market_to_bet_now, "").family == "OU"
    assert "83.5" not in f"{signal.real_probability_pct:.1f}"
    assert signal.real_probability_pct == pytest.approx(gem.probability * 100.0)


def test_suspended_quotes_and_a_missing_book_emit_nothing():
    state = project_residual(2.4, 1.8, 40, home_goals=0, away_goals=0)
    priced, rejected = scan_live_book(
        state,
        {"Over 0.5": 1.55},
        home_goals=0,
        away_goals=0,
        suspended=True,
    )
    assert priced == ()
    assert rejected[0].reason == "quote sospese"
    snapshot = LiveMatchSnapshot(
        fixture_id="t",
        match_name="Casa vs Ospite",
        minute=40,
        home_team="Casa",
        away_team="Ospite",
        home_goals=0,
        away_goals=0,
        xg_home=2.4,
        xg_away=1.8,
    )
    assert LiveMomentumSniper().evaluate_live_match(snapshot) is None


def test_next_goal_corner_and_second_half_multigol_parse_and_price():
    state = project_residual(
        1.8,
        1.1,
        50,
        home_goals=0,
        away_goals=0,
        home_shots=10,
        away_shots=4,
        home_corners=4,
        away_corners=1,
        favorite="HOME",
    )
    leading = project_residual(
        1.8,
        1.1,
        50,
        home_goals=2,
        away_goals=0,
        home_shots=10,
        away_shots=4,
        home_corners=4,
        away_corners=1,
        favorite="HOME",
    )
    assert state.siege
    assert state.corner_remaining_home > leading.corner_remaining_home
    next_home = price_live_market(state, "Next Goal Casa", home_goals=0, away_goals=0)
    no_more = price_live_market(state, "Nessun Altro Gol", home_goals=0, away_goals=0)
    corners = price_live_market(
        state,
        "Over 8.5 Corner",
        home_goals=0,
        away_goals=0,
        home_corners=4,
        away_corners=1,
    )
    second_half = price_live_market(
        state,
        "MultiGol 1-3 2° Tempo",
        home_goals=0,
        away_goals=0,
        second_half_goals=0,
    )
    assert next_home is not None and no_more is not None and corners is not None and second_half is not None
    assert 0.0 < next_home < 1.0
    assert parse_netwin_selection("", "Next Goal Casa").family == "NEXT_GOAL"
    assert parse_netwin_selection("", "Over 4.5 Corner Casa").specialty_scope == "HOME"
    assert parse_netwin_selection("G/NG", "Gol").family == "BTTS"


def _open_match(minute: int, **kwargs):
    defaults = dict(home_goals=0, away_goals=0, home_shots=5, away_shots=5)
    defaults.update(kwargs)
    return project_residual(1.7, 1.2, minute, **defaults)


def test_over_15_at_the_half_hour_is_not_the_same_number_as_at_82():
    early = price_live_market(_open_match(30), "Over 1.5", home_goals=0, away_goals=0)
    late = price_live_market(_open_match(82), "Over 1.5", home_goals=0, away_goals=0)
    assert early is not None and late is not None
    assert early > late
    assert early != pytest.approx(0.835)
    assert late != pytest.approx(0.850)
    assert early - late > 0.40


def test_a_red_card_cuts_the_win_and_the_next_goal():
    even = project_residual(1.5, 1.5, 55, home_shots=0, away_shots=0)
    ten_men = project_residual(1.5, 1.5, 55, home_reds=1, home_shots=0, away_shots=0)
    win = price_live_market(even, "1", home_goals=0, away_goals=0)
    win_short = price_live_market(ten_men, "1", home_goals=0, away_goals=0)
    next_home, next_away, _none = next_goal_probabilities(even.lambda_home, even.lambda_away)
    short_home, short_away, _short_none = next_goal_probabilities(ten_men.lambda_home, ten_men.lambda_away)
    assert win is not None and win_short is not None
    assert win_short < win
    assert short_home < next_home
    assert short_away > next_away
    assert ten_men.lambda_home == pytest.approx(even.lambda_home * 0.72)
    assert ten_men.lambda_away == pytest.approx(even.lambda_away * 1.08)


def test_a_favorite_behind_at_75_gets_the_corner_siege_boost():
    behind = project_residual(
        1.9,
        1.0,
        75,
        home_goals=0,
        away_goals=1,
        home_shots=12,
        away_shots=3,
        home_corners=6,
        away_corners=2,
        favorite="HOME",
    )
    leading = project_residual(
        1.9,
        1.0,
        75,
        home_goals=2,
        away_goals=0,
        home_shots=12,
        away_shots=3,
        home_corners=6,
        away_corners=2,
        favorite="HOME",
    )
    assert behind.siege
    assert not leading.siege
    assert behind.corner_remaining_home == pytest.approx(leading.corner_remaining_home * CORNER_SIEGE)
    assert behind.corner_remaining_away == pytest.approx(leading.corner_remaining_away * CORNER_PARKED)
    over_behind = price_live_market(
        behind, "Over 9.5 Corner Casa", home_goals=0, away_goals=1, home_corners=6, away_corners=2
    )
    over_leading = price_live_market(
        leading, "Over 9.5 Corner Casa", home_goals=2, away_goals=0, home_corners=6, away_corners=2
    )
    assert over_behind is not None and over_leading is not None
    assert over_behind > over_leading


def test_a_negative_edge_inside_the_price_band_is_rejected():
    state = _open_match(52)
    probability = price_live_market(state, "Over 0.5", home_goals=0, away_goals=0)
    assert probability is not None
    assert probability >= 0.72
    assert probability * 1.35 - 1.0 < 0
    priced, rejected = scan_live_book(state, {"Over 0.5": 1.35}, home_goals=0, away_goals=0)
    assert priced == ()
    assert "edge" in rejected[0].reason

    cheap, cheap_rejected = scan_live_book(state, {"Over 0.5": 1.25}, home_goals=0, away_goals=0)
    assert cheap == ()
    assert "1.25" in cheap_rejected[0].reason


def test_every_emitted_signal_is_a_netwin_selection():
    snapshot = LiveMatchSnapshot(
        fixture_id="t",
        match_name="Casa vs Ospite",
        minute=30,
        home_team="Casa",
        away_team="Ospite",
        home_goals=0,
        away_goals=0,
        home_shots=5,
        away_shots=5,
        xg_home=1.7,
        xg_away=1.2,
    )
    book = {
        "Over 0.5": 1.50,
        "Over 1.5": 1.70,
        "Next Goal Casa": 1.80,
        "1X + Under 4.5": 1.55,
        "MultiGol 1-4": 1.45,
    }
    signals = LiveMomentumSniper().scan(snapshot, book)
    assert signals
    assert any(signal.exact_selection == "Over 0.5" for signal in signals)
    for signal in signals:
        picked = parse_netwin_selection("", signal.exact_selection)
        named = parse_netwin_selection(signal.market_to_bet_now, "")
        assert picked.family
        assert named.family == picked.family
        assert signal.market_to_bet_now == signal.exact_selection


def test_stoppage_minutes_do_not_divide_by_zero():
    for minute in (90, 93, 99, 120):
        state = project_residual(
            1.4,
            1.1,
            minute,
            home_goals=1,
            away_goals=1,
            home_corners=8,
            away_corners=5,
            home_shots=14,
            away_shots=9,
        )
        assert state.time_fraction == pytest.approx(max(1, 94 - minute) / 90.0)
        assert state.lambda_home > 0
        assert state.corner_remaining_home > 0
        priced = price_live_market(
            state,
            "Over 1.5",
            home_goals=1,
            away_goals=1,
            home_corners=8,
            away_corners=5,
        )
        assert priced is not None
        assert 0.0 <= priced <= 1.0

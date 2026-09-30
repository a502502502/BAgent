"""Il cacciatore tiene solo lo sweet spot e scarta veti, quote stracce e masse basse."""

import numpy as np
import pytest

from services.analysis.combo_book_search import COMBO_CATALOG, find_hidden_gems
from services.analysis.xg_poisson_engine import QuantitativeEngine, _goal_market_mask
from services.football.sixth_sense.lambda_context import MatchContext


NEW_MARKETS = (
    "MultiGol 1-2 Casa",
    "MultiGol 1-3 Casa",
    "MultiGol 2-3 Casa",
    "MultiGol 1-2 Ospite",
    "MultiGol 1-3 Ospite",
    "MultiGol 1-3",
    "MultiGol 2-4",
    "MultiGol 2-5",
    "MultiGol 3-5",
    "1X + MultiGol 1-3",
    "1X + MultiGol 1-4",
    "1X + MultiGol 2-4",
    "1X + MultiGol 2-5",
    "X2 + MultiGol 1-3",
    "X2 + MultiGol 1-4",
    "X2 + MultiGol 2-4",
    "X2 + MultiGol 2-5",
    "1X + Under 2.5",
    "1X + Under 3.5",
    "1X + Under 4.5",
    "X2 + Under 2.5",
    "X2 + Under 3.5",
    "X2 + Under 4.5",
    "1 + MultiGol 1-4",
    "2 + MultiGol 1-4",
    "1 + MultiGol 2-5",
    "2 + MultiGol 2-5",
)


def test_every_new_clause_is_a_mask_on_the_joint_matrix():
    engine = QuantitativeEngine()
    matrix, home, away, total = engine._score_axes(1.6, 1.1)
    for market in NEW_MARKETS:
        assert market in COMBO_CATALOG
        mask = _goal_market_mask(market, home, away, total)
        assert mask is not None
        probability = float(np.sum(matrix[mask]))
        assert 0.0 < probability < 1.0
    home_band = engine.goal_market_probability(1.6, 1.1, "MultiGol 1-2 Casa")
    band = np.broadcast_to((home >= 1) & (home <= 2), matrix.shape)
    rows = matrix[band].sum()
    assert home_band == pytest.approx(float(rows))
    combo = engine.goal_market_probability(1.6, 1.1, "1X + MultiGol 1-4")
    one_x = engine.goal_market_probability(1.6, 1.1, "1X")
    band = engine.goal_market_probability(1.6, 1.1, "MultiGol 1-4")
    assert combo is not None and one_x is not None and band is not None
    assert combo <= min(one_x, band)


def test_a_short_price_with_real_edge_stays_out_of_the_sweet_spot():
    market = "MultiGol 1-5"
    probability = QuantitativeEngine().goal_market_probability(1.2, 1.0, market)
    assert probability is not None
    edge = probability * 1.25 - 1.0
    assert edge > 0.06
    result = find_hidden_gems(1.2, 1.0, {market: 1.25})
    assert result.ranked == ()
    reason = next(item.reason for item in result.rejected if item.market == market)
    assert reason == "quota 1.25 sotto il minimo 1.35"


def test_a_long_price_on_a_thin_slice_is_rejected_for_probability():
    market = "MultiGol 3-5"
    probability = QuantitativeEngine().goal_market_probability(1.8, 1.3, market)
    assert probability == pytest.approx(0.506, abs=0.02)
    assert probability < 0.70
    result = find_hidden_gems(1.8, 1.3, {market: 2.10})
    assert result.ranked == ()
    reason = next(item.reason for item in result.rejected if item.market == market)
    assert reason.startswith("probabilità")
    assert "sotto la soglia" in reason


def test_a_price_inside_the_band_with_a_fat_matrix_is_a_hidden_gem():
    market = "Over 1.5"
    probability = QuantitativeEngine().goal_market_probability(1.5, 1.2, market)
    assert probability == pytest.approx(0.757, abs=0.02)
    result = find_hidden_gems(1.5, 1.2, {market: 1.55})
    assert [combo.market for combo in result.ranked] == [market]
    gem = result.ranked[0]
    assert gem.book_odd == 1.55
    assert gem.probability == pytest.approx(probability)
    assert gem.edge == pytest.approx(probability * 1.55 - 1.0)
    assert gem.edge > 0.072
    assert gem.fair_odd == pytest.approx(1.0 / probability)


def test_sixth_sense_vetoes_still_drop_the_combo_before_the_sweet_spot():
    severe = find_hidden_gems(
        1.2,
        1.0,
        {"Under 3.5": 1.55},
        MatchContext(referee_cards_per_game=5.4),
    )
    assert severe.ranked == ()
    assert "arbitro severo" in next(item.reason for item in severe.rejected if item.market == "Under 3.5")

    chase = find_hidden_gems(
        1.2,
        1.0,
        {"1X + Under 4.5": 1.60},
        MatchContext(first_leg_home=0, first_leg_away=3),
    )
    assert chase.ranked == ()
    assert "ritorno" in next(item.reason for item in chase.rejected if item.market == "1X + Under 4.5")

    short_lead = find_hidden_gems(
        1.5,
        1.05,
        {"1X + Over 1.5": 1.70},
        MatchContext(corto_muso_home=True),
    )
    assert "1-0" in next(item.reason for item in short_lead.rejected if item.market == "1X + Over 1.5")


def test_projected_corners_move_the_team_line_before_the_edge():
    engine = QuantitativeEngine()
    base = engine.corner_over_probability(8.0, 3.0, "Over 4.5 Corner Casa")
    result = find_hidden_gems(
        2.4,
        0.7,
        {"Over 4.5 Corner Casa": 1.50},
        corners_home=8.0,
        corners_away=3.0,
    )
    gem = next(combo for combo in result.ranked if combo.market == "Over 4.5 Corner Casa")
    boosted = engine.corner_over_probability(8.0 * 1.12, 3.0 * 0.85, "Over 4.5 Corner Casa")
    assert base is not None and boosted is not None
    assert boosted > base
    assert gem.probability == pytest.approx(boosted)
    assert gem.edge == pytest.approx(boosted * 1.50 - 1.0)
    assert any("corner" in note for note in gem.notes)
    missing = find_hidden_gems(1.5, 1.2, {"Over 8.5 Corner": 1.50})
    assert any(item.reason == "corner non forniti: proiezione base" for item in missing.rejected)

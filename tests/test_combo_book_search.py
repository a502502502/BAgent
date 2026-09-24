"""Le combo battono il banco solo con una quota vera, e il sesto senso cambia la matrice."""

from services.analysis.combo_book_search import search_combo_edge
from services.analysis.xg_poisson_engine import QuantitativeEngine
from services.football.sixth_sense.analyzer import SixthSenseEvent
from services.football.sixth_sense.lambda_context import MatchContext, context_from_events


def test_missing_book_price_does_not_invent_an_edge():
    result = search_combo_edge(1.7, 1.1, book_odds=None)
    assert result.ranked == ()
    assert any(item.reason == "quota del banco assente" for item in result.rejected)


def test_only_the_quote_above_fair_odds_is_ranked():
    plain = search_combo_edge(1.7, 1.1)
    under = next(item for item in plain.rejected if item.market == "1X + Under 3.5")
    assert under.reason == "quota del banco assente"
    engine = QuantitativeEngine()
    mix = engine.goal_market_probability(1.7, 1.1, "Chance Mix: 1X o Over 1.5")
    over = engine.goal_market_probability(1.7, 1.1, "Over 2.5")
    assert mix is not None and over is not None
    generous = round(1.0 / mix + 0.15, 2)
    short = round(max(1.01, 1.0 / over - 0.15), 2)
    result = search_combo_edge(
        1.7,
        1.1,
        {
            "Chance Mix: 1X o Over 1.5": generous,
            "Over 2.5": short,
        },
    )
    assert [combo.market for combo in result.ranked] == ["Chance Mix: 1X o Over 1.5"]
    winner = result.ranked[0]
    assert winner.edge == winner.probability * generous - 1


def test_corto_muso_home_drops_combos_that_die_on_one_nil():
    priced = QuantitativeEngine().goal_market_probability(1.7, 1.05, "1X + Under 3.5")
    assert priced is not None
    result = search_combo_edge(
        1.7,
        1.05,
        {
            "1X + Over 1.5": 2.20,
            "Chance Mix: X2 o Over 1.5": 1.80,
            "1X + Under 3.5": round(1.0 / priced + 0.20, 2),
            "Chance Mix: 1X o Over 1.5": 1.40,
        },
        MatchContext(corto_muso_home=True),
    )
    rejected = {item.market: item.reason for item in result.rejected}
    assert "1-0" in rejected["1X + Over 1.5"]
    assert "1-0" in rejected["Chance Mix: X2 o Over 1.5"]
    assert any(combo.market == "1X + Under 3.5" for combo in result.ranked)
    assert result.xg_home < 1.7


def test_dominant_attack_rejects_a_capped_home_multigol_even_at_a_fat_price():
    result = search_combo_edge(
        2.6,
        0.7,
        {"MultiGol 1-3 Casa": 3.00, "Under 2.5": 2.40},
    )
    reasons = {item.market: item.reason for item in result.rejected}
    assert "tetto" in reasons["MultiGol 1-3 Casa"]
    assert "under" in reasons["Under 2.5"]


def test_rotation_event_shrinks_both_attacks_before_pricing():
    events = [
        SixthSenseEvent("both", "fatigue", "turno infrasettimanale", impact=-1, confidence=0.8)
    ]
    context = context_from_events(events)
    base = QuantitativeEngine().goal_market_probability(1.8, 1.4, "Over 2.5")
    result = search_combo_edge(1.8, 1.4, {"Over 2.5": 2.50}, context)
    adjusted = QuantitativeEngine().goal_market_probability(result.xg_home, result.xg_away, "Over 2.5")
    assert context.rotation_risk
    assert result.xg_home < 1.8
    assert result.xg_away < 1.4
    assert base is not None and adjusted is not None
    assert adjusted < base

"""Scanner mercati: fixture Netwin, coerenza della matrice, combo sopra l'1 secco."""

import json

import pytest

from services.analysis.match_market_optimizer import MatchMarketOptimizer


def _fixture(path) -> None:
    payload = {
        "matches": [
            {
                "match_name": "Home FC vs Away FC",
                "raw_name": "Home FC - Away FC",
                "tournament": "Serie A",
                "kickoff": "2026-10-04 18:00:00",
                "markets": {
                    "1X2": {"1": 2.40, "X": 3.30, "2": 3.10},
                    "UNDER_OVER": {
                        "2.5": {"Under": 1.90, "Over": 1.90},
                        "1.5": {"Under": 3.20, "Over": 1.35},
                        "3.5": {"Under": 1.32, "Over": 3.40},
                    },
                    "COMBO": {
                        "1X + MultiGol 2-5": 1.70,
                        "1X + Over 1.5": 1.65,
                        "1X + MultiGol 1-4": 1.55,
                        "1X + Under 3.5": 1.60,
                    },
                    "CHANCE_MIX": {"Chance Mix: 1X o Gol": 1.40},
                    "CORNER": {"8.5": {"Under": 1.85, "Over": 1.90}},
                    "CARTELLINI": {"3.5": {"Under": 1.70, "Over": 2.05}},
                },
            }
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _optimizer(tmp_path) -> MatchMarketOptimizer:
    odds = tmp_path / "odds.json"
    _fixture(odds)
    return MatchMarketOptimizer(
        odds_path=odds,
        db_path=tmp_path / "missing.db",
        xg_home=1.35,
        xg_away=1.15,
        corner_home=5.5,
        corner_away=4.4,
        card_home=2.2,
        card_away=1.9,
    )


def test_loads_every_quoted_goal_market(tmp_path):
    scan = _optimizer(tmp_path).scan("Home FC vs Away FC")
    names = {row.market for row in scan.markets}
    assert {"1", "X", "2", "Under 2.5", "Over 2.5", "1X + MultiGol 2-5"} <= names
    assert scan.source == "override"
    assert scan.markets[0].probability >= scan.markets[-1].probability


def test_exclusive_markets_sum_to_one(tmp_path):
    optimizer = _optimizer(tmp_path)
    optimizer.scan(home="Home FC", away="Away FC")
    priced = {row.market: row.probability for row in optimizer.scan_result.markets}
    assert priced["1"] + priced["X"] + priced["2"] == pytest.approx(1.0)
    assert priced["Under 2.5"] + priced["Over 2.5"] == pytest.approx(1.0)


def test_combo_beats_the_straight_home_win(tmp_path):
    optimizer = _optimizer(tmp_path)
    optimizer.scan("Home")
    alternatives = optimizer.find_alternative_combos("1X2")
    combo = next(row for row in alternatives if row.single == "1" and row.alternative == "1X + MultiGol 2-5")
    assert combo.alternative_probability > combo.single_probability
    assert combo.delta_p > 0
    assert "1-1" in combo.scenario
    over = next(row for row in alternatives if row.single == "Over 2.5" and row.alternative == "1X + Over 1.5")
    assert "1-1" not in over.scenario


def test_corners_and_cards_partition(tmp_path):
    optimizer = _optimizer(tmp_path)
    optimizer.scan("Home FC vs Away FC")
    priced = {row.market: row.probability for row in optimizer.scan_result.markets}
    assert priced["Over 8.5 Corner"] + priced["Under 8.5 Corner"] == pytest.approx(1.0)
    assert priced["Over 3.5 Cartellini"] + priced["Under 3.5 Cartellini"] == pytest.approx(1.0)
    assert priced["1 Corner"] + priced["X Corner"] + priced["2 Corner"] == pytest.approx(1.0)
    assert priced["1 Cartellini"] + priced["X Cartellini"] + priced["2 Cartellini"] == pytest.approx(1.0)
    quoted = {row.market: row.odd for row in optimizer.scan_result.markets}
    assert quoted["Over 8.5 Corner"] == 1.90
    assert quoted["Under 3.5 Cartellini"] == 1.70

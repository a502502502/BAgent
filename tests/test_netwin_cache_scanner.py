"""Cache Netwin piatta, Hidden Gems sopra soglia, snapshot Flashscore coerenti."""

import json

from services.analysis.xg_poisson_engine import QuantitativeEngine
from services.betting.netwin_cache_reader import (
    flatten_netwin_markets,
    load_cached_matches,
    scan_netwin_matches,
)
from services.football.external.sources.flashscore_live import FlashscoreLiveEngine
from services.football.sixth_sense.lambda_context import MatchContext


def test_nested_netwin_markets_flatten_to_the_combo_dictionary():
    flat = flatten_netwin_markets({
        "markets": {
            "1X2": {"1": 2.30, "X": 2.97, "2": 3.25, "missing": None},
            "DOPPIA_CHANCE": {"1X": 1.32, "X2": 1.88, "12": 1.37},
            "UNDER_OVER": {
                "1.5": {"Over": 1.22, "Under": 3.40},
                "2.5": {"Over": 1.91, "Under": 1.77},
                "3.5": {"Under": 1.30, "Over": 3.15},
            },
            "GOL_NOGOL": {"Gol": 1.85, "NoGol": 1.90},
            "MULTIGOL": {"1-5": 1.44, "MultiGol 1-3 Casa": 1.62},
            "CORNER": {"9.5": {"Over": 1.70, "Under": 1.95}},
        }
    })
    assert flat["1"] == 2.30
    assert flat["X"] == 2.97
    assert flat["2"] == 3.25
    assert flat["1X"] == 1.32
    assert flat["X2"] == 1.88
    assert flat["12"] == 1.37
    assert flat["Over 2.5"] == 1.91
    assert flat["Under 2.5"] == 1.77
    assert flat["Over 1.5"] == 1.22
    assert flat["Under 3.5"] == 1.30
    assert flat["Gol"] == 1.85
    assert flat["NoGol"] == 1.90
    assert flat["MultiGol 1-5"] == 1.44
    assert flat["MultiGol 1-3 Casa"] == 1.62
    assert flat["Over 9.5 Corner"] == 1.70
    assert flat["Under 9.5 Corner"] == 1.95
    assert "missing" not in flat
    assert flatten_netwin_markets(None) == {}
    assert flatten_netwin_markets({"markets": "rotto"}) == {}


def test_cached_match_resolves_teams_and_skips_a_corrupt_file(tmp_path):
    payload = {
        "matches": [
            {
                "raw_name": "Independiente - Instituto Cordoba",
                "tournament": "Liga Profesional",
                "kickoff": "20261003 00:15:00",
                "markets": {"1X2": {"1": 2.30, "X": 2.97, "2": 3.25}},
            },
            {"match_name": "senza separatore"},
            "non-dict",
        ]
    }
    path = tmp_path / "netwin_live_odds.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    rows = load_cached_matches(path=path)
    assert len(rows) == 1
    match = rows[0]
    assert match.home_team == "Independiente"
    assert match.away_team == "Instituto Cordoba"
    assert match.match_name == "Independiente vs Instituto Cordoba"
    assert match.odds_dict["1"] == 2.30
    assert load_cached_matches("brasil", path) == []
    assert load_cached_matches("profesional", path) == rows

    broken = tmp_path / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert load_cached_matches(path=broken) == []
    assert load_cached_matches(path=tmp_path / "missing.json") == []


def test_hidden_gems_keep_the_priced_edge_and_drop_the_rest(tmp_path):
    xg_home, xg_away = 1.20, 0.95
    engine = QuantitativeEngine()
    gem_p = engine.goal_market_probability(xg_home, xg_away, "MultiGol 1-4")
    thin_p = engine.goal_market_probability(xg_home, xg_away, "MultiGol 1-3")
    assert gem_p is not None and thin_p is not None
    assert gem_p * 1.65 - 1.0 >= 0.045
    assert thin_p >= 0.70
    assert thin_p * 1.40 - 1.0 < 0.045

    payload = {
        "matches": [{
            "match_name": "Casa Test vs Ospite Test",
            "tournament": "Lega Test",
            "kickoff": "20261003 19:45:00",
            "markets": {
                "MULTIGOL": {"1-4": 1.65, "1-3": 1.40},
                "UNDER_OVER": {"2.5": {"Over": 1.20}},
            },
        }]
    }
    path = tmp_path / "cache.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    matches = load_cached_matches(path=path)
    gems = scan_netwin_matches(
        matches,
        min_edge=0.045,
        min_probability=0.70,
        xg_for=lambda _match: (xg_home, xg_away),
        context_for=lambda _match: MatchContext(),
    )
    markets = [gem.market for gem in gems]
    assert "MultiGol 1-4" in markets
    assert "MultiGol 1-3" not in markets
    assert "Over 2.5" not in markets
    assert gems[0].edge >= gems[-1].edge
    for gem in gems:
        assert gem.probability >= 0.70
        assert gem.edge >= 0.045
        assert gem.book_odd == 1.65 or gem.market != "MultiGol 1-4"


def test_flashscore_live_feed_becomes_a_snapshot_with_minute_score_and_cards():
    feed = (
        "~AA÷ABC123¬AE÷Home FC¬AF÷Away FC¬AB÷12¬AC÷67¬AG÷1¬AH÷0¬"
        "BA÷2¬BB÷1¬GRA÷1¬GRB÷0¬BC÷1¬BD÷0¬"
        "~AA÷LATER99¬AE÷Non Live¬AF÷Domani¬AB÷1¬AC÷¬AG÷¬AH÷¬"
        "~AA÷ADDED3¬AE÷Late Home¬AF÷Late Away¬AB÷13¬AC÷90+3¬AG÷2¬AH÷2¬"
    )
    snapshots = FlashscoreLiveEngine().get_live_snapshots(feed)
    by_id = {snap.fixture_id: snap for snap in snapshots}
    assert "LATER99" not in by_id
    live = by_id["ABC123"]
    assert live.match_name == "Home FC vs Away FC"
    assert live.minute == 67
    assert (live.home_goals, live.away_goals) == (1, 0)
    assert (live.home_yellow_cards, live.away_yellow_cards) == (2, 1)
    assert (live.home_red_cards, live.away_red_cards) == (1, 0)
    assert (live.ht_home_goals, live.ht_away_goals) == (1, 0)
    added = by_id["ADDED3"]
    assert added.minute == 93
    assert (added.home_goals, added.away_goals) == (2, 2)

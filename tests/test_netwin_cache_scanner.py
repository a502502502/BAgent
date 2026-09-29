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
            "PRIMO_TEMPO": {"1 1° Tempo": 2.70, "Under 1.5 1° Tempo": 1.25},
            "CHANCE_MIX": {"Chance Mix: 1 o Over 2.5": 1.55, "Chance Mix: 1X o Gol": 1.35},
            "DRAW_NO_BET": {"DNB 1": 1.40, "DNB 2": 2.90},
            "MULTIGOL_SQUADRA": {"MultiGol 1-2 Casa": 1.58},
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
    assert flat["1 1° Tempo"] == 2.70
    assert flat["Under 1.5 1° Tempo"] == 1.25
    assert flat["Chance Mix: 1 o Over 2.5"] == 1.55
    assert flat["Chance Mix: 1X o Gol"] == 1.35
    assert flat["DNB 1"] == 1.40
    assert flat["DNB 2"] == 2.90
    assert flat["MultiGol 1-2 Casa"] == 1.58
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


def test_secondary_aggregates_merge_into_match_combos():
    from services.betting.netwin_odds_downloader import NetwinOddsDownloader, decode_multigol_range

    assert decode_multigol_range(131073) == "1-2"
    assert decode_multigol_range(196609) == "1-3"
    assert decode_multigol_range(262145) == "1-4"
    assert decode_multigol_range(327681) == "1-5"
    assert decode_multigol_range(262146) == "2-4"
    assert decode_multigol_range(327682) == "2-5"
    assert decode_multigol_range(393217) == "1-6"
    assert decode_multigol_range(262147) == "3-4"

    downloader = NetwinOddsDownloader(headless=True)
    matches = [
        {
            "match_name": "Palmeiras vs Bahia",
            "palinsesto": 36401,
            "avvenimento": 1001,
            "markets": {},
        }
    ]

    # 1. Test Agg 452 (DC + U/O)
    agg_452 = {
        "avs": [
            {
                "p": 36401,
                "a": 1001,
                "scs": [
                    {
                        "d": "DOPPIA CHANCE IN + U/O",
                        "h": 250,
                        "eqs": [{"ce": 1, "q": 170}, {"ce": 2, "q": 360}],
                    },
                    {
                        "d": "DOPPIA CHANCE OUT + U/O",
                        "h": 350,
                        "eqs": [{"ce": 1, "q": 210}, {"ce": 2, "q": 650}],
                    },
                ],
            }
        ]
    }
    downloader._merge_aggregate_markets(matches, agg_452, 452)
    assert matches[0]["markets"]["COMBO"]["1X + Under 2.5"] == 1.70
    assert matches[0]["markets"]["COMBO"]["1X + Over 2.5"] == 3.60
    assert matches[0]["markets"]["COMBO"]["X2 + Under 3.5"] == 2.10

    # 2. Test Agg 1477 (DC + MultiGol)
    agg_1477 = {
        "avs": [
            {
                "p": 36401,
                "a": 1001,
                "scs": [
                    {
                        "d": "DC IN + MULTIGOAL",
                        "h": 262145,  # 1-4
                        "eqs": [{"ce": 1, "q": 145}],
                    },
                    {
                        "d": "DC OUT + MULTIGOAL",
                        "h": 327681,  # 1-5
                        "eqs": [{"ce": 3, "q": 220}],
                    },
                ],
            }
        ]
    }
    downloader._merge_aggregate_markets(matches, agg_1477, 1477)
    assert matches[0]["markets"]["COMBO"]["1X + MultiGol 1-4"] == 1.45
    assert matches[0]["markets"]["COMBO"]["X2 + MultiGol 1-5"] == 2.20

    # Flatten check
    flat = flatten_netwin_markets(matches[0])
    assert flat["1X + Under 2.5"] == 1.70
    assert flat["1X + MultiGol 1-4"] == 1.45
    assert flat["X2 + MultiGol 1-5"] == 2.20


def test_sanitize_double_chance_purges_incoherent_odds():
    # Caso Santos: 1=4.05, X=3.60, 2=1.80. X2 a 1.76 è assurda (fair ~1.20) e va eliminata.
    raw_match = {
        "markets": {
            "1X2": {"1": 4.05, "X": 3.60, "2": 1.80},
            "DOPPIA_CHANCE": {"1X": 1.92, "X2": 1.76, "12": 1.27},
        }
    }
    flat = flatten_netwin_markets(raw_match)
    assert "1X" in flat
    assert flat["1X"] == 1.92
    assert "12" in flat
    assert flat["12"] == 1.27
    assert "X2" not in flat  # Corrotta / anomala, scartata!


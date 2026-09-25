"""La richiesta tiene il mercato con l'edge più alto e ne scrive il perché."""

from datetime import datetime
from zoneinfo import ZoneInfo

from services.analysis.combo_book_search import find_hidden_gems
from services.football.sixth_sense.lambda_context import MatchContext
from services.portal.slip_advisor import advise_records, league_allowed, records_from_feed

ROME = ZoneInfo("Europe/Rome")
NOW = datetime(2026, 9, 25, 12, 0, tzinfo=ROME)
KICK = datetime(2026, 9, 26, 20, 45, tzinfo=ROME)


def test_the_shown_market_is_the_highest_edge_gem_and_explains_why():
    context = MatchContext(corto_muso_home=True)
    record = _record("Napoli", "Cagliari", "Italy Serie A", {"Under 3.5": 1.55, "Over 2.5": 1.70})
    result = advise_records([record], NOW, context)
    gems = find_hidden_gems(1.85, 0.95, record["odds"], context)
    assert gems.ranked
    best = gems.ranked[0]
    shown = result["selections"][0]
    assert shown["market"] == best.market
    assert any("corto muso" in line for line in shown["motivations"])
    assert any("sweet spot" in line for line in shown["motivations"])
    assert "validatore" in result["note"]


def test_italia_vs_belgio_is_the_english_fixture_and_stops_without_xg():
    assert league_allowed("International UEFA Nations League") is True
    record = _record("Italy", "Belgium", "International UEFA Nations League", {"Over 2.5": 1.80})
    record["xg_home"] = None
    record["xg_away"] = None
    result = advise_records([record], NOW, query="italia vs belgio")
    assert result["selections"] == []
    assert result["discarded"][0]["match"] == "Italy vs Belgium"
    assert "xG" in result["message"]


def test_a_lower_league_or_a_match_without_prices_never_becomes_a_pick():
    assert league_allowed("Netherlands Eerste Divisie") is False
    assert league_allowed("Italy Serie A") is True
    rows = [
        _raw("Oldham", "Salford", 1, 1.2, 1.1, 11),
        _raw("Milan", "Lecce", 2, 1.8, 0.9, 0),
    ]
    records = records_from_feed(rows, {1: "England League Two", 2: "Italy Serie A"})
    result = advise_records(records, NOW, query="Milan")
    assert result["selections"] == []
    assert result["discarded"][0]["reason"] == "quote assenti nel feed"


def test_only_the_three_strongest_edges_enter_the_slip():
    records = [
        _record(f"Casa {index}", f"Ospite {index}", "Spain La Liga", {"Over 1.5": odd})
        for index, odd in enumerate((1.40, 1.50, 1.60, 1.70, 1.80), start=1)
    ]
    result = advise_records(records, NOW)
    assert result["count"] == 3
    edges = [row["edge"] for row in result["selections"]]
    assert edges == sorted(edges, reverse=True)


def _record(home, away, league, odds):
    return {
        "home": home,
        "away": away,
        "league": league,
        "kickoff": KICK,
        "xg_home": 1.85,
        "xg_away": 0.95,
        "odds": odds,
        "status": "incomplete",
    }


def _raw(home, away, competition, xg_home, xg_away, over_15):
    return {
        "home_name": home,
        "away_name": away,
        "competition_id": competition,
        "date_unix": int(KICK.timestamp()),
        "status": "incomplete",
        "team_a_xg_prematch": xg_home,
        "team_b_xg_prematch": xg_away,
        "odds_ft_over15": over_15,
        "odds_ft_over25": 0,
        "odds_ft_under25": 0,
        "odds_ft_under35": 0,
    }

from datetime import datetime

from models.football import (
    FootballMatch,
    FootballTeam,
)

from models.football_odds import (
    FootballMatchOdds,
)

from models.historical_match import (
    HistoricalFootballMatch,
)


def test_historical_match_can_store_odds():

    match = FootballMatch(
        id="MATCH-1",
        competition="Premier League",
        season="2025/26",
        home=FootballTeam(
            id="Liverpool",
            name="Liverpool",
        ),
        away=FootballTeam(
            id="Bournemouth",
            name="Bournemouth",
        ),
        start_time="2025-08-15T20:00:00",
        home_goals=4,
        away_goals=2,
        status="Completed",
    )

    odds = FootballMatchOdds(
        home=1.30,
        draw=6.00,
        away=8.50,
        over_2_5=1.36,
        under_2_5=3.20,
    )

    historical = HistoricalFootballMatch(
        match=match,
        date=datetime.fromisoformat(
            "2025-08-15T20:00:00"
        ),
        odds=odds,
    )

    assert historical.odds is not None
    assert historical.odds.home == 1.30
    assert historical.odds.draw == 6.00
    assert historical.odds.away == 8.50
    assert historical.odds.over_2_5 == 1.36


def test_historical_match_odds_are_optional():

    match = FootballMatch(
        id="MATCH-2",
        competition="Premier League",
        season="2025/26",
        home=FootballTeam(
            id="Liverpool",
            name="Liverpool",
        ),
        away=FootballTeam(
            id="Bournemouth",
            name="Bournemouth",
        ),
        start_time="2025-08-15T20:00:00",
        status="Scheduled",
    )

    historical = HistoricalFootballMatch(
        match=match,
        date=datetime.fromisoformat(
            "2025-08-15T20:00:00"
        ),
    )

    assert historical.odds is None

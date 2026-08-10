from datetime import datetime

from models.football import (
    FootballMatch,
    FootballTeam,
)

from models.football_statistics import (
    FootballMatchStatistics,
)

from models.historical_match import (
    HistoricalFootballMatch,
)


def test_historical_match_can_store_statistics():

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

    statistics = FootballMatchStatistics(
        home_shots=19,
        away_shots=10,
        home_shots_on_target=10,
        away_shots_on_target=3,
        home_corners=6,
        away_corners=7,
        home_yellow_cards=1,
        away_yellow_cards=2,
        home_red_cards=0,
        away_red_cards=0,
        home_half_time_goals=1,
        away_half_time_goals=0,
    )

    historical = HistoricalFootballMatch(
        match=match,
        date=datetime.fromisoformat(
            "2025-08-15T20:00:00"
        ),
        statistics=statistics,
    )

    assert historical.statistics is not None
    assert historical.statistics.home_shots == 19
    assert historical.statistics.away_shots == 10
    assert historical.statistics.total_corners == 13


def test_historical_match_statistics_are_optional():

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

    assert historical.statistics is None
    assert historical.result is None

from datetime import datetime

from models.football import (
    FootballMatch,
    FootballTeam,
)

from models.historical_match import (
    HistoricalFootballMatch,
)

from services.football_historical_dataset import (
    FootballHistoricalDataset,
)


def make_match(
    match_id: str,
    date: str,
    home_goals: int,
    away_goals: int,
) -> HistoricalFootballMatch:

    match = FootballMatch(
        id=match_id,
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id="TeamA",
            name="Team A",
        ),
        away=FootballTeam(
            id="TeamB",
            name="Team B",
        ),
        start_time=date,
        home_goals=home_goals,
        away_goals=away_goals,
        status="Completed",
    )

    return HistoricalFootballMatch(
        match=match,
        date=datetime.fromisoformat(date),
        winner=match.result,
    )


def test_dataset_sorts_matches_chronologically():

    matches = [
        make_match(
            "MATCH-3",
            "2026-08-03T20:00:00",
            2,
            0,
        ),
        make_match(
            "MATCH-1",
            "2026-08-01T20:00:00",
            1,
            0,
        ),
        make_match(
            "MATCH-2",
            "2026-08-02T20:00:00",
            1,
            1,
        ),
    ]

    dataset = FootballHistoricalDataset(
        matches
    )

    result = dataset.all()

    assert [
        item.match_id
        for item in result
    ] == [
        "MATCH-1",
        "MATCH-2",
        "MATCH-3",
    ]


def test_before_excludes_match_on_same_date():

    matches = [
        make_match(
            "MATCH-1",
            "2026-08-01T20:00:00",
            1,
            0,
        ),
        make_match(
            "MATCH-2",
            "2026-08-02T20:00:00",
            2,
            1,
        ),
        make_match(
            "MATCH-3",
            "2026-08-03T20:00:00",
            0,
            0,
        ),
    ]

    dataset = FootballHistoricalDataset(
        matches
    )

    result = dataset.before(
        datetime.fromisoformat(
            "2026-08-02T20:00:00"
        )
    )

    assert [
        item.match_id
        for item in result
    ] == [
        "MATCH-1",
    ]


def test_completed_before_excludes_scheduled_matches():

    completed = make_match(
        "MATCH-1",
        "2026-08-01T20:00:00",
        1,
        0,
    )

    scheduled_match = FootballMatch(
        id="MATCH-2",
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id="TeamA",
            name="Team A",
        ),
        away=FootballTeam(
            id="TeamB",
            name="Team B",
        ),
        start_time="2026-08-02T20:00:00",
        status="Scheduled",
    )

    scheduled = HistoricalFootballMatch(
        match=scheduled_match,
        date=datetime.fromisoformat(
            "2026-08-02T20:00:00"
        ),
    )

    dataset = FootballHistoricalDataset(
        [
            completed,
            scheduled,
        ]
    )

    result = dataset.completed_before(
        datetime.fromisoformat(
            "2026-08-03T20:00:00"
        )
    )

    assert [
        item.match_id
        for item in result
    ] == [
        "MATCH-1",
    ]


def test_up_to_includes_same_timestamp():

    matches = [
        make_match(
            "MATCH-1",
            "2026-08-01T20:00:00",
            1,
            0,
        ),
        make_match(
            "MATCH-2",
            "2026-08-02T20:00:00",
            2,
            1,
        ),
    ]

    dataset = FootballHistoricalDataset(
        matches
    )

    result = dataset.up_to(
        datetime.fromisoformat(
            "2026-08-02T20:00:00"
        )
    )

    assert [
        item.match_id
        for item in result
    ] == [
        "MATCH-1",
        "MATCH-2",
    ]


def test_completed_returns_only_finished_matches():

    completed = make_match(
        "MATCH-1",
        "2026-08-01T20:00:00",
        1,
        0,
    )

    scheduled_match = FootballMatch(
        id="MATCH-2",
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id="TeamA",
            name="Team A",
        ),
        away=FootballTeam(
            id="TeamB",
            name="Team B",
        ),
        start_time="2026-08-02T20:00:00",
        status="Scheduled",
    )

    scheduled = HistoricalFootballMatch(
        match=scheduled_match,
        date=datetime.fromisoformat(
            "2026-08-02T20:00:00"
        ),
    )

    dataset = FootballHistoricalDataset(
        [
            completed,
            scheduled,
        ]
    )

    result = dataset.completed()

    assert [
        item.match_id
        for item in result
    ] == [
        "MATCH-1",
    ]

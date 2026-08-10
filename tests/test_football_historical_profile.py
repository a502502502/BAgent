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

from services.football_historical_profile import (
    FootballHistoricalProfile,
)


def make_match(
    match_id: str,
    date: str,
    home_id: str,
    away_id: str,
    home_goals: int,
    away_goals: int,
) -> HistoricalFootballMatch:

    match = FootballMatch(
        id=match_id,
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id=home_id,
            name=home_id,
        ),
        away=FootballTeam(
            id=away_id,
            name=away_id,
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


def test_profile_excludes_current_match():

    historical_matches = [
        make_match(
            "MATCH-1",
            "2026-08-01T20:00:00",
            "TeamA",
            "TeamB",
            2,
            0,
        ),
        make_match(
            "MATCH-2",
            "2026-08-05T20:00:00",
            "TeamA",
            "TeamC",
            1,
            1,
        ),
        make_match(
            "MATCH-3",
            "2026-08-10T20:00:00",
            "TeamA",
            "TeamD",
            5,
            0,
        ),
    ]

    dataset = FootballHistoricalDataset(
        historical_matches
    )

    historical_profile = (
        FootballHistoricalProfile(dataset)
    )

    profiles = historical_profile.build_as_of(
        datetime.fromisoformat(
            "2026-08-10T20:00:00"
        )
    )

    team_a = profiles["TeamA"]

    assert team_a.matches == 2
    assert team_a.wins == 1
    assert team_a.draws == 1

    assert team_a.goals_for == 3
    assert team_a.goals_against == 1

    assert "TeamD" not in profiles


def test_profile_excludes_future_matches():

    historical_matches = [
        make_match(
            "MATCH-1",
            "2026-08-01T20:00:00",
            "TeamA",
            "TeamB",
            2,
            0,
        ),
        make_match(
            "MATCH-2",
            "2026-08-20T20:00:00",
            "TeamA",
            "TeamC",
            5,
            0,
        ),
    ]

    dataset = FootballHistoricalDataset(
        historical_matches
    )

    historical_profile = (
        FootballHistoricalProfile(dataset)
    )

    profiles = historical_profile.build_as_of(
        datetime.fromisoformat(
            "2026-08-10T20:00:00"
        )
    )

    team_a = profiles["TeamA"]

    assert team_a.matches == 1
    assert team_a.wins == 1

    assert team_a.goals_for == 2
    assert team_a.goals_against == 0

    assert "TeamC" not in profiles


def test_profile_for_unknown_team_is_none():

    historical_matches = [
        make_match(
            "MATCH-1",
            "2026-08-01T20:00:00",
            "TeamA",
            "TeamB",
            2,
            0,
        ),
    ]

    dataset = FootballHistoricalDataset(
        historical_matches
    )

    historical_profile = (
        FootballHistoricalProfile(dataset)
    )

    profile = (
        historical_profile.get_team_profile(
            team_id="Unknown",
            date=datetime.fromisoformat(
                "2026-08-10T20:00:00"
            ),
        )
    )

    assert profile is None


def test_profile_is_based_only_on_completed_matches():

    completed = make_match(
        "MATCH-1",
        "2026-08-01T20:00:00",
        "TeamA",
        "TeamB",
        2,
        0,
    )

    scheduled_match = FootballMatch(
        id="MATCH-2",
        competition="Test League",
        season="2025/26",
        home=FootballTeam(
            id="TeamA",
            name="TeamA",
        ),
        away=FootballTeam(
            id="TeamC",
            name="TeamC",
        ),
        start_time="2026-08-05T20:00:00",
        status="Scheduled",
    )

    scheduled = HistoricalFootballMatch(
        match=scheduled_match,
        date=datetime.fromisoformat(
            "2026-08-05T20:00:00"
        ),
    )

    dataset = FootballHistoricalDataset(
        [
            completed,
            scheduled,
        ]
    )

    historical_profile = (
        FootballHistoricalProfile(dataset)
    )

    profiles = historical_profile.build_as_of(
        datetime.fromisoformat(
            "2026-08-10T20:00:00"
        )
    )

    assert profiles["TeamA"].matches == 1
    assert profiles["TeamA"].goals_for == 2

    assert "TeamC" not in profiles

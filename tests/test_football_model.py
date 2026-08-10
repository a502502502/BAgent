from models.football import (
    FootballMatch,
    FootballTeam,
)


def test_completed_home_win():

    home = FootballTeam(
        id="Liverpool",
        name="Liverpool",
    )

    away = FootballTeam(
        id="Arsenal",
        name="Arsenal",
    )

    match = FootballMatch(
        id="TEST-001",
        competition="Premier League",
        season="2025/26",
        home=home,
        away=away,
        start_time="2026-08-10T20:00:00",
        home_goals=2,
        away_goals=1,
        status="Completed",
    )

    assert match.is_completed
    assert match.total_goals == 3
    assert match.goal_difference == 1
    assert match.result == "HOME"


def test_completed_draw():

    match = FootballMatch(
        id="TEST-002",
        competition="Premier League",
        season="2025/26",
        home=FootballTeam(
            id="Liverpool",
            name="Liverpool",
        ),
        away=FootballTeam(
            id="Arsenal",
            name="Arsenal",
        ),
        start_time="2026-08-10T20:00:00",
        home_goals=1,
        away_goals=1,
        status="Completed",
    )

    assert match.result == "DRAW"


def test_scheduled_match_has_no_result():

    match = FootballMatch(
        id="TEST-003",
        competition="Premier League",
        season="2026/27",
        home=FootballTeam(
            id="Liverpool",
            name="Liverpool",
        ),
        away=FootballTeam(
            id="Arsenal",
            name="Arsenal",
        ),
        start_time="2026-08-20T20:00:00",
        status="Scheduled",
    )

    assert not match.is_completed
    assert match.total_goals is None
    assert match.goal_difference is None
    assert match.result is None

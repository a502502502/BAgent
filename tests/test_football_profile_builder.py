from models.football import (
    FootballMatch,
    FootballTeam,
)

from services.football_profile_builder import (
    FootballProfileBuilder,
)


def test_builder_updates_both_teams():

    match = FootballMatch(
        id="MATCH-001",
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
        home_goals=2,
        away_goals=1,
        status="Completed",
        home_corners=6,
        away_corners=3,
        home_yellow_cards=2,
        away_yellow_cards=4,
        home_red_cards=0,
        away_red_cards=1,
        home_xg=1.8,
        away_xg=0.9,
    )

    builder = FootballProfileBuilder()

    profiles = builder.build([match])

    home = profiles["Liverpool"]
    away = profiles["Arsenal"]

    assert home.matches == 1
    assert home.home_matches == 1
    assert home.wins == 1
    assert home.home_wins == 1
    assert home.draws == 0
    assert home.losses == 0

    assert home.goals_for == 2
    assert home.goals_against == 1

    assert home.clean_sheets == 0
    assert home.btts_matches == 1

    assert home.corners_for == 6
    assert home.corners_against == 3

    assert home.yellow_cards == 2
    assert home.red_cards == 0

    assert home.xg_for == 1.8
    assert home.xg_against == 0.9

    assert away.matches == 1
    assert away.away_matches == 1
    assert away.wins == 0
    assert away.draws == 0
    assert away.losses == 1

    assert away.goals_for == 1
    assert away.goals_against == 2

    assert away.clean_sheets == 0
    assert away.btts_matches == 1

    assert away.corners_for == 3
    assert away.corners_against == 6

    assert away.yellow_cards == 4
    assert away.red_cards == 1

    assert away.xg_for == 0.9
    assert away.xg_against == 1.8


def test_builder_handles_draw_and_clean_sheet():

    match = FootballMatch(
        id="MATCH-002",
        competition="Serie A",
        season="2025/26",
        home=FootballTeam(
            id="Inter",
            name="Inter",
        ),
        away=FootballTeam(
            id="Milan",
            name="Milan",
        ),
        start_time="2026-08-11T20:00:00",
        home_goals=0,
        away_goals=0,
        status="Completed",
    )

    profiles = FootballProfileBuilder().build(
        [match]
    )

    inter = profiles["Inter"]
    milan = profiles["Milan"]

    assert inter.draws == 1
    assert inter.home_draws == 1
    assert inter.clean_sheets == 1

    assert milan.draws == 1
    assert milan.away_draws == 1
    assert milan.clean_sheets == 1


def test_builder_ignores_scheduled_matches():

    match = FootballMatch(
        id="MATCH-003",
        competition="Serie A",
        season="2026/27",
        home=FootballTeam(
            id="Inter",
            name="Inter",
        ),
        away=FootballTeam(
            id="Milan",
            name="Milan",
        ),
        start_time="2026-08-20T20:00:00",
        status="Scheduled",
    )

    profiles = FootballProfileBuilder().build(
        [match]
    )

    assert profiles["Inter"].matches == 0
    assert profiles["Milan"].matches == 0


def test_builder_handles_multiple_matches():

    matches = [
        FootballMatch(
            id="MATCH-004",
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
            home_goals=2,
            away_goals=0,
            status="Completed",
        ),
        FootballMatch(
            id="MATCH-005",
            competition="Premier League",
            season="2025/26",
            home=FootballTeam(
                id="Arsenal",
                name="Arsenal",
            ),
            away=FootballTeam(
                id="Liverpool",
                name="Liverpool",
            ),
            start_time="2026-08-17T20:00:00",
            home_goals=1,
            away_goals=1,
            status="Completed",
        ),
    ]

    profiles = FootballProfileBuilder().build(
        matches
    )

    liverpool = profiles["Liverpool"]
    arsenal = profiles["Arsenal"]

    assert liverpool.matches == 2
    assert liverpool.wins == 1
    assert liverpool.draws == 1

    assert arsenal.matches == 2
    assert arsenal.wins == 0
    assert arsenal.draws == 1
    assert arsenal.losses == 1

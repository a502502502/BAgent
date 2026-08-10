from models.football_profile import (
    FootballTeamProfile,
)

from services.football_team_strength_factor import (
    FootballTeamStrengthFactor,
)


def test_stronger_home_team_produces_positive_value():

    home = FootballTeamProfile(
        team_id="Home",
        team_name="Home",
        matches=10,
        wins=8,
        draws=1,
        losses=1,
    )

    away = FootballTeamProfile(
        team_id="Away",
        team_name="Away",
        matches=10,
        wins=3,
        draws=2,
        losses=5,
    )

    contribution = (
        FootballTeamStrengthFactor().evaluate(
            home,
            away,
        )
    )

    assert contribution is not None
    assert contribution.factor == "TeamStrength"
    assert contribution.value > 0
    assert contribution.confidence == 0.5


def test_equal_teams_produce_zero_value():

    home = FootballTeamProfile(
        team_id="Home",
        team_name="Home",
        matches=10,
        wins=5,
        draws=2,
        losses=3,
    )

    away = FootballTeamProfile(
        team_id="Away",
        team_name="Away",
        matches=10,
        wins=5,
        draws=2,
        losses=3,
    )

    contribution = (
        FootballTeamStrengthFactor().evaluate(
            home,
            away,
        )
    )

    assert contribution is not None
    assert contribution.value == 0.0


def test_smoothing_is_applied():

    home = FootballTeamProfile(
        team_id="Home",
        team_name="Home",
        matches=1,
        wins=1,
    )

    away = FootballTeamProfile(
        team_id="Away",
        team_name="Away",
        matches=1,
        wins=0,
    )

    contribution = (
        FootballTeamStrengthFactor().evaluate(
            home,
            away,
        )
    )

    assert contribution is not None

    expected_home = (
        1 + 5 * 0.5
    ) / (1 + 5)

    expected_away = (
        0 + 5 * 0.5
    ) / (1 + 5)

    expected_difference = (
        expected_home
        - expected_away
    )

    assert (
        contribution.details[
            "home_smoothed_win_rate"
        ]
        == expected_home
    )

    assert (
        contribution.details[
            "away_smoothed_win_rate"
        ]
        == expected_away
    )

    assert (
        contribution.details[
            "difference"
        ]
        == expected_difference
    )


def test_missing_profile_returns_none():

    away = FootballTeamProfile(
        team_id="Away",
        team_name="Away",
        matches=10,
        wins=5,
    )

    contribution = (
        FootballTeamStrengthFactor().evaluate(
            None,
            away,
        )
    )

    assert contribution is None


def test_no_history_returns_none():

    home = FootballTeamProfile(
        team_id="Home",
        team_name="Home",
        matches=0,
    )

    away = FootballTeamProfile(
        team_id="Away",
        team_name="Away",
        matches=10,
        wins=5,
    )

    contribution = (
        FootballTeamStrengthFactor().evaluate(
            home,
            away,
        )
    )

    assert contribution is None


def test_confidence_reaches_one_with_enough_history():

    home = FootballTeamProfile(
        team_id="Home",
        team_name="Home",
        matches=40,
        wins=25,
    )

    away = FootballTeamProfile(
        team_id="Away",
        team_name="Away",
        matches=40,
        wins=20,
    )

    contribution = (
        FootballTeamStrengthFactor().evaluate(
            home,
            away,
        )
    )

    assert contribution is not None
    assert contribution.confidence == 1.0

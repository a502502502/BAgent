from models.football_profile import FootballTeamProfile

from services.football_match_balance_factor import (
    FootballMatchBalanceFactor,
)


def test_equal_teams_produce_high_balance():
    home = FootballTeamProfile(
        team_id="A",
        team_name="Team A",
        matches=20,
        wins=8,
        draws=6,
        losses=6,
    )

    away = FootballTeamProfile(
        team_id="B",
        team_name="Team B",
        matches=20,
        wins=8,
        draws=6,
        losses=6,
    )

    contribution = (
        FootballMatchBalanceFactor()
        .evaluate(home, away)
    )

    assert contribution is not None
    assert contribution.value > 0.8


def test_different_teams_produce_lower_balance():
    home = FootballTeamProfile(
        team_id="A",
        team_name="Team A",
        matches=20,
        wins=15,
        draws=2,
        losses=3,
    )

    away = FootballTeamProfile(
        team_id="B",
        team_name="Team B",
        matches=20,
        wins=4,
        draws=4,
        losses=12,
    )

    contribution = (
        FootballMatchBalanceFactor()
        .evaluate(home, away)
    )

    assert contribution is not None
    assert contribution.value < 0.5


def test_balance_uses_draw_rates():
    home = FootballTeamProfile(
        team_id="A",
        team_name="Team A",
        matches=20,
        wins=6,
        draws=10,
        losses=4,
    )

    away = FootballTeamProfile(
        team_id="B",
        team_name="Team B",
        matches=20,
        wins=6,
        draws=2,
        losses=12,
    )

    contribution = (
        FootballMatchBalanceFactor()
        .evaluate(home, away)
    )

    assert contribution is not None
    assert contribution.value > 0.5


def test_missing_profile_returns_none():
    home = FootballTeamProfile(
        team_id="A",
        team_name="Team A",
        matches=10,
        wins=5,
    )

    contribution = (
        FootballMatchBalanceFactor()
        .evaluate(home, None)
    )

    assert contribution is None


def test_no_history_returns_none():
    home = FootballTeamProfile(
        team_id="A",
        team_name="Team A",
        matches=0,
    )

    away = FootballTeamProfile(
        team_id="B",
        team_name="Team B",
        matches=10,
        wins=5,
    )

    contribution = (
        FootballMatchBalanceFactor()
        .evaluate(home, away)
    )

    assert contribution is None


def test_balance_is_between_zero_and_one():
    home = FootballTeamProfile(
        team_id="A",
        team_name="Team A",
        matches=50,
        wins=30,
        draws=10,
        losses=10,
    )

    away = FootballTeamProfile(
        team_id="B",
        team_name="Team B",
        matches=50,
        wins=10,
        draws=10,
        losses=30,
    )

    contribution = (
        FootballMatchBalanceFactor()
        .evaluate(home, away)
    )

    assert contribution is not None
    assert 0.0 <= contribution.value <= 1.0

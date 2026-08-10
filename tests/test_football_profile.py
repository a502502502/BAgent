from models.football_profile import (
    FootballTeamProfile,
)


def test_empty_profile():

    profile = FootballTeamProfile(
        team_id="Liverpool",
        team_name="Liverpool",
    )

    assert profile.matches == 0
    assert profile.win_rate is None
    assert profile.goals_for_per_match is None
    assert profile.clean_sheet_rate is None


def test_profile_rates():

    profile = FootballTeamProfile(
        team_id="Liverpool",
        team_name="Liverpool",
        matches=10,
        wins=6,
        draws=2,
        losses=2,
        goals_for=20,
        goals_against=10,
        clean_sheets=4,
        btts_matches=7,
    )

    assert profile.win_rate == 0.6
    assert profile.draw_rate == 0.2
    assert profile.loss_rate == 0.2

    assert profile.goals_for_per_match == 2.0
    assert profile.goals_against_per_match == 1.0

    assert profile.goal_difference == 10

    assert profile.clean_sheet_rate == 0.4
    assert profile.btts_rate == 0.7


def test_statistical_averages():

    profile = FootballTeamProfile(
        team_id="Liverpool",
        team_name="Liverpool",
        matches=5,
        corners_for=30,
        corners_against=20,
        yellow_cards=10,
        red_cards=2,
        xg_for=8.5,
        xg_against=5.0,
    )

    assert profile.average_corners_for == 6.0
    assert profile.average_corners_against == 4.0

    assert profile.average_yellow_cards == 2.0
    assert profile.average_red_cards == 0.4

    assert profile.average_xg_for == 1.7
    assert profile.average_xg_against == 1.0

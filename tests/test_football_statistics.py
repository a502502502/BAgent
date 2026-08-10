from models.football_statistics import (
    FootballMatchStatistics,
)


def test_statistics_store_match_data():

    statistics = FootballMatchStatistics(
        home_shots=19,
        away_shots=10,
        home_shots_on_target=10,
        away_shots_on_target=3,
        home_fouls=7,
        away_fouls=10,
        home_corners=6,
        away_corners=7,
        home_yellow_cards=1,
        away_yellow_cards=2,
        home_red_cards=0,
        away_red_cards=0,
        home_half_time_goals=1,
        away_half_time_goals=0,
    )

    assert statistics.home_shots == 19
    assert statistics.away_shots == 10

    assert statistics.total_shots == 29
    assert statistics.total_corners == 13
    assert statistics.total_yellow_cards == 3


def test_missing_statistics_return_none():

    statistics = FootballMatchStatistics()

    assert statistics.total_shots is None
    assert statistics.total_corners is None
    assert statistics.total_yellow_cards is None

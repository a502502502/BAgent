from pathlib import Path

from services.football_data_loader import (
    FootballDataLoader,
)


FIXTURE = Path(
    "data/football/raw/E0_2025_2026.csv"
)


def test_loader_reads_real_season_file():

    matches = FootballDataLoader().load(
        FIXTURE
    )

    assert len(matches) == 380


def test_loader_maps_first_match():

    matches = FootballDataLoader().load(
        FIXTURE
    )

    match = matches[0]

    assert match.match_id
    assert match.home_team_id == "Liverpool"
    assert match.away_team_id == "Bournemouth"

    assert match.match.home_goals == 4
    assert match.match.away_goals == 2

    assert match.result == "HOME"
    assert match.is_completed


def test_loader_maps_match_statistics():

    matches = FootballDataLoader().load(
        FIXTURE
    )

    match = matches[0]

    assert match.statistics is not None

    assert match.statistics.home_shots == 19
    assert match.statistics.away_shots == 10

    assert match.statistics.home_shots_on_target == 10
    assert match.statistics.away_shots_on_target == 3

    assert match.statistics.home_corners == 6
    assert match.statistics.away_corners == 7

    assert match.statistics.home_yellow_cards == 1
    assert match.statistics.away_yellow_cards == 2

    assert match.statistics.home_half_time_goals == 1
    assert match.statistics.away_half_time_goals == 0


def test_loader_preserves_chronological_order():

    matches = FootballDataLoader().load(
        FIXTURE
    )

    dates = [
        match.date
        for match in matches
    ]

    assert dates == sorted(dates)


def test_loader_uses_completed_status():

    matches = FootballDataLoader().load(
        FIXTURE
    )

    assert all(
        match.match.status == "Completed"
        for match in matches
    )

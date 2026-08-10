from pathlib import Path

from services.football_data_loader import (
    FootballDataLoader,
)


FIXTURE = Path(
    "data/football/raw/E0_2025_2026.csv"
)


def test_loader_maps_real_1x2_odds():

    matches = FootballDataLoader().load(
        FIXTURE
    )

    odds = matches[0].odds

    assert odds is not None

    assert odds.home == 1.30
    assert odds.draw == 6.00
    assert odds.away == 8.50


def test_loader_maps_real_over_under_odds():

    matches = FootballDataLoader().load(
        FIXTURE
    )

    odds = matches[0].odds

    assert odds is not None

    assert odds.over_2_5 == 1.36
    assert odds.under_2_5 == 3.20


def test_loader_provides_1x2_odds_for_most_matches():

    matches = FootballDataLoader().load(
        FIXTURE
    )

    available = [
        match
        for match in matches
        if match.odds is not None
        and match.odds.is_1x2_available
    ]

    assert len(available) >= 370

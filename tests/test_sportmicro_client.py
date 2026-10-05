"""Unit test per SportmicroClient."""

from unittest.mock import MagicMock, patch
import pytest

from services.betting.sportmicro_client import SportmicroClient, _normalize_name


def test_normalize_name():
    assert _normalize_name("France U21") == "france"
    assert _normalize_name("FC Bayern München") == "bayern munchen"
    assert _normalize_name("AC Milan") == "milan"
    assert _normalize_name("Atlético Tucumán") == "atletico tucuman"


def test_find_match_id():
    client = SportmicroClient(api_key="dummy")
    matches = [
        {"id": 101, "home_team_name": "France", "away_team_name": "Belgium"},
        {"id": 102, "home_team_name": "Italy", "away_team_name": "Türkiye"},
    ]

    assert client.find_match_id("France", "Belgium", matches) == 101
    assert client.find_match_id("Francia", "Belgio", matches) == 101  # ora con alias IT!
    assert client.find_match_id("Italy", "Turkiye", matches) == 102
    assert client.find_match_id("Italia", "Turchia", matches) == 102
    assert client.find_match_id("Spain", "Germany", matches) is None


def test_get_score_in_both_halves_odds_parsing():
    client = SportmicroClient(api_key="dummy")
    sample_payload = [
        {
            "match_id": 142,
            "periods": [
                {
                    "period_type": "Full Time",
                    "odds": [
                        {
                            "id": 1,
                            "bookmaker_id": 39,
                            "bookmaker_name": "bet365",
                            "home": 5.0,
                            "away": 4.0,
                        },
                        {
                            "id": 2,
                            "bookmaker_id": 4,
                            "bookmaker_name": "BetVictor",
                            "home": 5.4,
                            "away": 4.2,
                        },
                    ],
                }
            ],
        }
    ]

    with patch.object(client, "_get", return_value=sample_payload):
        odds = client.get_score_in_both_halves_odds(142)
        assert odds["Casa Segna in Entrambi i Tempi: SI"] == 5.0
        assert odds["Ospite Segna in Entrambi i Tempi: SI"] == 4.0
        assert odds["Casa Segna in Entrambi i Tempi"] == 5.0


def test_enrich_odds_dict():
    client = SportmicroClient(api_key="dummy")
    matches = [{"id": 555, "home_team_name": "France", "away_team_name": "Belgium"}]

    with patch.object(client, "get_matches_for_date", return_value=matches):
        with patch.object(
            client,
            "get_score_in_both_halves_odds",
            return_value={"Casa Segna in Entrambi i Tempi: SI": 3.80},
        ):
            base_odds = {"1": 1.70, "X": 3.50, "2": 4.20}
            enriched = client.enrich_odds_dict("France vs Belgium", base_odds)
            assert enriched["Casa Segna in Entrambi i Tempi: SI"] == 3.80
            assert enriched["1"] == 1.70

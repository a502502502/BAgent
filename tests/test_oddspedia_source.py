"""
tests/test_oddspedia_source.py — Unit test per OddspediaSource e parsing dei segnali.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.football.external.sources.oddspedia import (
    OddspediaSignal,
    OddspediaSource,
)


@pytest.fixture
def sample_dropping_odds_state():
    return {
        "toolName": "DroppingOdds",
        "toolData": {
            "matches": [
                {
                    "id": 1001,
                    "sport_slug": "football",
                    "category_name": "Italy",
                    "league_name": "Serie B",
                    "md": "2026-10-07 19:30:00+00",
                    "ht": "Palermo",
                    "at": "Cremonese",
                    "ot_name": "Full Time Result",
                    "group_name": "1X2",
                    "oddNumberDrop": "o1",
                    "maxDrop": 24.5,
                    "allBookies": 25,
                    "odds": [
                        {
                            "allDrops": [
                                {
                                    "slug": "pinnacle",
                                    "current": "1.75",
                                    "max": "2.32",
                                    "percentage": 24.5,
                                }
                            ],
                            "allOdds": [
                                {"name": "Pinnacle", "slug": "pinnacle", "current": "1.75"},
                                {"name": "SNAI", "slug": "snai", "current": "1.85"},
                                {"name": "Bet365", "slug": "bet365", "current": "1.78"},
                            ],
                        }
                    ],
                },
                {
                    "id": 1002,
                    "sport_slug": "basketball",
                    "category_name": "USA",
                    "league_name": "NBA",
                    "md": "2026-10-07 23:00:00+00",
                    "ht": "Lakers",
                    "at": "Warriors",
                    "maxDrop": 35.0,
                    "odds": [],
                },
                {
                    "id": 1003,
                    "sport_slug": "football",
                    "category_name": "England",
                    "league_name": "League One",
                    "md": "2026-10-07 18:45:00+00",
                    "ht": "Barnsley",
                    "at": "Bolton",
                    "ot_name": "Full Time Result",
                    "oddNumberDrop": "o2",
                    "maxDrop": 8.0,  # Sotto soglia (minimo 10.0%)
                    "odds": [],
                },
            ]
        },
    }


@pytest.fixture
def sample_value_bets_state():
    return {
        "toolName": "ValueBets",
        "toolData": {
            "matches": [
                {
                    "id": 2001,
                    "sport_slug": "football",
                    "category_name": "Spain",
                    "league_name": "La Liga",
                    "md": "2026-10-07 20:00:00+00",
                    "ht": "Real Betis",
                    "at": "Osasuna",
                    "ot_name": "Over/Under 2.5",
                    "selection": "Over 2.5",
                    "prob": 58.5,
                    "overvalue": 7.8,
                    "odds": [
                        {"bookie_name": "Sisal", "bookie_slug": "sisal", "odd": "1.84"},
                        {"bookie_name": "Bet365", "bookie_slug": "bet365", "odd": "1.80"},
                    ],
                },
                {
                    "id": 2002,
                    "sport_slug": "football",
                    "category_name": "Germany",
                    "league_name": "Bundesliga",
                    "md": "2026-10-07 19:30:00+00",
                    "ht": "Mainz",
                    "at": "Augsburg",
                    "prob": 40.0,
                    "overvalue": 95.0,  # Errore materiale di quota da scartare (>20%)
                    "odds": [{"bookie_name": "Bwin", "bookie_slug": "bwin", "odd": "25.0"}],
                },
            ]
        },
    }


def test_parse_dropping_odds_filters_and_formats(sample_dropping_odds_state):
    source = OddspediaSource(headless=True)
    signals = source.parse_dropping_odds_state(
        state=sample_dropping_odds_state,
        sport="football",
        min_drop_pct=10.0,
        limit=10,
    )

    # Solo la partita di Palermo deve passare (la NBA e basket, Barnsley ha calo solo 8%)
    assert len(signals) == 1
    s = signals[0]
    assert s.home_team == "Palermo"
    assert s.away_team == "Cremonese"
    assert s.sport == "football"
    assert s.league == "Serie B"
    assert s.drop_percentage == 24.5
    assert s.selection == "1 (Casa)"
    assert s.initial_odd == 2.32
    assert s.current_odd == 1.75
    # Verifica riconoscimento bookmaker ADM (SNAI e Bet365)
    adm_slugs = {b["slug"] for b in s.italian_bookmakers}
    assert "snai" in adm_slugs
    assert "bet365" in adm_slugs


def test_parse_value_bets_filters_outliers(sample_value_bets_state):
    source = OddspediaSource(headless=True)
    signals = source.parse_value_bets_state(
        state=sample_value_bets_state,
        sport="football",
        min_overvalue_pct=3.0,
        max_overvalue_pct=20.0,
        limit=10,
    )

    # Solo Real Betis vs Osasuna passa (+7.8%), Mainz ha 95% che e un evidente refuso da scartare
    assert len(signals) == 1
    s = signals[0]
    assert s.home_team == "Real Betis"
    assert s.away_team == "Osasuna"
    assert s.overvalue_pct == 7.8
    assert s.fair_probability_pct == 58.5
    assert s.current_odd == 1.84
    assert s.best_bookmaker == "Sisal"
    assert any(b["slug"] == "sisal" for b in s.italian_bookmakers)


def test_export_signals_to_json(tmp_path, sample_dropping_odds_state):
    source = OddspediaSource(headless=True)
    signals = source.parse_dropping_odds_state(
        state=sample_dropping_odds_state,
        sport="football",
        min_drop_pct=5.0,
        limit=10,
    )
    out_file = tmp_path / "test_signals.json"
    result_path = source.export_signals_to_json(signals, output_file=out_file)

    assert result_path.exists()
    data = json.loads(result_path.read_text(encoding="utf-8"))
    assert data["total_signals"] == 2  # Palermo (24.5%) e Barnsley (8.0%)
    assert len(data["signals"]) == 2
    assert data["signals"][0]["home_team"] == "Palermo"


def test_parse_match_insights_and_warnings():
    source = OddspediaSource(headless=True)
    fake_event_state = {
        "event": {
            "id": 15819,
            "ht": "Avispa Fukuoka",
            "at": "Yokohama",
            "ht_form": "LDLLW?",
            "at_form": "LWDWW?",
            "hscore": 0,
            "ascore": 1,
            "inplay_status": "2T",
            "current_time": 77,
            "venue_name": "Best Denki Stadium",
            "match_keys": [
                {"statement": "Avispa Fukuoka ha subito gol in ciascuna delle sue ultime 6 partite."},
                {"statement": "Quando Yokohama si porta in vantaggio per 1-0 nei match in trasferta, poi vince la partita nel 87% dei casi."},
                {"statement": "La prestazione nelle ultime 5 partite di Yokohama e' migliore di quella di Avispa Fukuoka."},
            ],
        },
        "bettingStats": {
            "data": [
                {"label": "goals", "data": [{"label": "total"}]},
                {"label": "btts", "data": [{"label": "total"}]},
                {"label": "corners", "data": [{"label": "total"}]},
                {"label": "cards", "data": [{"label": "total"}]},
            ]
        },
    }

    insights = source.parse_match_insights_state(fake_event_state)
    assert insights.match_id == 15819
    assert insights.home_team == "Avispa Fukuoka"
    assert insights.away_team == "Yokohama"
    assert insights.home_form == "LDLLW"
    assert insights.away_form == "LWDWW"
    assert insights.home_score == 0
    assert insights.away_score == 1
    assert len(insights.statements) == 3
    assert "goals" in insights.betting_stats
    assert "corners" in insights.betting_stats

    warnings = source.analyze_match_warnings(insights)
    assert any("CONCESSION_STREAK" in w for w in warnings)
    assert any("DOMINANT_CONVERSION" in w for w in warnings)
    assert any("SUPERIOR_MOMENTUM" in w for w in warnings)
    assert any("FORM_ALERT" in w for w in warnings)


def test_parse_hot_bets_rows():
    source = OddspediaSource(headless=True)
    fake_rows = [
        {
            "league": "BOLIVIA LFPB LEAGUE CUP",
            "market": "btts: words.yes",
            "matchInfo": "8 ott 02:30 Guabira Montero The Strongest",
            "playedGames": "6 /7",
            "percent": "86%",
            "odd": "1.57",
        },
        {
            "league": "SERBIA U19 LEAGUE",
            "market": "btts: words.yes",
            "matchInfo": "7 ott 18:00 Jedinstvo UB U19 Stella Rossa U19",
            "playedGames": "7 /7",
            "percent": "100%",
            "odd": "1.44",
        },
    ]

    hot_bets = source.parse_hot_bets_rows(fake_rows)
    assert len(hot_bets) == 2
    # Primo elemento per win_percentage decrescente (100% prima di 86%)
    assert hot_bets[0].win_percentage == 100.0
    assert "Stella Rossa" in hot_bets[0].match
    assert "Gol (Entrambe Segnano)" in hot_bets[0].market or "GG" in hot_bets[0].market
    assert hot_bets[0].odd == 1.44

    assert hot_bets[1].win_percentage == 86.0
    assert hot_bets[1].odd == 1.57
    assert hot_bets[1].streak_count == "6 /7"



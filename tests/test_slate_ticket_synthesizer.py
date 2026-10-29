"""
tests/test_slate_ticket_synthesizer.py — Test per il Generatore Autonomo di Schedine Tipster-Style.
"""

from __future__ import annotations
from pathlib import Path
import pytest

from services.analysis.slate_ticket_synthesizer import (
    SlateTicketSynthesizer,
    cards_market_allowed,
    kickoff_complete,
    open_or_tense_fixture,
)

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "bagent.db"


def test_slate_ticket_synthesizer_build_ticket():
    synth = SlateTicketSynthesizer(db_path=DB_PATH)

    matches_sample = [
        {"home_team": "Monza", "away_team": "Cagliari", "tournament": "Serie A", "kickoff": "2026-10-19 18:30 CEST", "markets": {"DOPPIA_CHANCE": {"1X": 1.36}}},
        {"home_team": "Viborg", "away_team": "Midtjylland", "tournament": "Superligaen DEN", "kickoff": "2026-10-19 19:00 CEST", "markets": {"GOL_NOGOL": {"Gol": 1.47}}},
        {"home_team": "Trabzonspor", "away_team": "Besiktas", "tournament": "Super Lig TUR", "kickoff": "2026-10-19 19:00 CEST", "markets": {"CHANCE_MIX": {"Chance Mix: X o Gol": 1.35}}},
        {"home_team": "Sporting CP", "away_team": "Casa Pia", "tournament": "Liga Portugal", "kickoff": "2026-10-19 20:45 CEST", "markets": {"DOPPIA_CHANCE": {"1X": 1.34}}},
        {"home_team": "Barcelona", "away_team": "Sevilla", "tournament": "La Liga", "kickoff": "2026-10-19 21:00 CEST", "markets": {"COMBO": {"1X + Over 1.5": 1.36}}},
        {"home_team": "PSV", "away_team": "AZ Alkmaar", "tournament": "Eredivisie", "kickoff": "2026-10-19 21:15 CEST", "markets": {"GOL_NOGOL": {"Gol": 1.47}}},
        {"home_team": "Arsenal", "away_team": "Chelsea", "tournament": "Premier League", "kickoff": "2026-10-19 20:00 CEST", "markets": {"COMBO": {"1X + Over 1.5": 1.36}}},
    ]

    ticket = synth.build_tipster_style_ticket(matches_sample, target_legs=5)
    assert ticket is not None
    assert ticket["num_legs"] >= 5
    assert ticket["total_odds"] >= 3.0
    assert "legs" in ticket
    assert len(ticket["legs"]) >= 5

    # Verifica che ci sia eterogeneità di categorie (non mono-mercato)
    categories = set(leg["category"] for leg in ticket["legs"])
    assert len(categories) >= 3, f"Categorie insufficientemente eterogenee: {categories}"
    assert "odds_band" in ticket
    assert ticket["status"] in {"READY", "OUT_OF_ODDS_BAND"}
    assert all(kickoff_complete(leg["kickoff"]) for leg in ticket["legs"])


def test_chance_mix_does_not_fire_on_every_serie_a_match():
    assert open_or_tense_fixture(2.4, 0.4, "Serie A") is False
    assert open_or_tense_fixture(1.2, 1.4, "Serie A") is True
    assert open_or_tense_fixture(2.1, 1.9, "Premier League") is True
    assert open_or_tense_fixture(2.2, 0.5, "Premier League") is False


class _FlowEngine:
    def __init__(self, home_flow, away_flow):
        self.home_flow = home_flow
        self.away_flow = away_flow

    def cross_analyze_match(self, *args, **kwargs):
        return {}

    def get_team_profile(self, name):
        home = name == "Home FC"
        return {
            "avg_goals_scored": 1.8 if home else 1.7,
            "avg_goals_conceded": 0.9 if home else 1.4,
            "hr_over_15_match": 80.0,
            "hr_chance_mix_x_gg": 40.0,
            "hr_multigol_1_3_team": 40.0,
            "avg_cards_match": 6.0,
            "hr_over_05_sh_match": 0.0,
            "hr_mg_1_3_sh_match": 0.0,
        }

    def team_flow(self, name):
        return self.home_flow if name == "Home FC" else self.away_flow


def test_hit_rates_come_from_results_not_from_constants():
    home_flow = {
        "matches": 10,
        "home_n": 6,
        "home_unbeaten_hr": 66.7,
        "unbeaten_hr": 70.0,
        "btts_hr": 40.0,
        "home_dc_and_ov15_hr": 50.0,
        "dc_and_ov15_hr": 55.0,
        "cards_n": 8,
        "avg_team_cards": 2.4,
        "team_cards_ov15_hr": 62.5,
    }
    away_flow = {
        "matches": 10,
        "home_n": 5,
        "btts_hr": 60.0,
        "cards_n": 0,
        "avg_team_cards": 0.0,
        "team_cards_ov15_hr": 0.0,
    }
    synth = SlateTicketSynthesizer(db_path=DB_PATH)
    synth.engine = _FlowEngine(home_flow, away_flow)
    picks = synth.evaluate_match_gems(
        "Home FC",
        "Away FC",
        "Serie A",
        "2026-10-20 20:45 CEST",
        {"GOL_NOGOL": {"Gol": 1.47}, "CARTELLINI": {"Over 1.5 Squadra": 1.40}},
    )
    by_cat = {p.market_category: p for p in picks}
    assert by_cat["GOL"].hit_rate == 50.0
    assert by_cat["CARTELLINI"].hit_rate == 62.5
    assert by_cat["COMBO"].hit_rate == 50.0
    assert "85" not in by_cat["CARTELLINI"].rationale


def test_double_chance_and_combo_use_home_sample():
    home_flow = {
        "matches": 10,
        "home_n": 6,
        "home_unbeaten_hr": 83.3,
        "unbeaten_hr": 70.0,
        "btts_hr": 20.0,
        "home_dc_and_ov15_hr": 66.7,
        "dc_and_ov15_hr": 40.0,
        "cards_n": 0,
        "avg_team_cards": 0.0,
        "team_cards_ov15_hr": 0.0,
    }
    away_flow = {"matches": 8, "home_n": 0, "btts_hr": 20.0, "cards_n": 0, "avg_team_cards": 0.0}

    class Engine(_FlowEngine):
        def get_team_profile(self, name):
            profile = super().get_team_profile(name)
            if name != "Home FC":
                profile["avg_goals_scored"] = 0.8
            return profile

    synth = SlateTicketSynthesizer(db_path=DB_PATH)
    synth.engine = Engine(home_flow, away_flow)
    picks = synth.evaluate_match_gems(
        "Home FC", "Away FC", "Serie A", "2026-10-20 18:00 CEST", {}
    )
    by_cat = {p.market_category: p for p in picks}
    assert by_cat["DOPPIA_CHANCE"].hit_rate == 83.3
    assert by_cat["COMBO"].hit_rate == 66.7
    assert "CARTELLINI" not in by_cat


def test_nordic_cards_stay_out():
    assert cards_market_allowed("Super Lig TUR") is True
    assert cards_market_allowed("Superligaen DEN") is False
    assert cards_market_allowed("Eliteserien") is False


def test_kickoff_requires_date_and_time():
    assert kickoff_complete("2026-10-19 18:30 CEST")
    assert kickoff_complete("19/10/2026 ore 18:30")
    assert kickoff_complete("") is False
    assert kickoff_complete("stasera") is False
    assert kickoff_complete("2026-10-19") is False

"""
tests/test_slate_ticket_synthesizer.py — Test per il Generatore Autonomo di Schedine Tipster-Style.
"""

from __future__ import annotations
from pathlib import Path
import pytest

from services.analysis.slate_ticket_synthesizer import SlateTicketSynthesizer

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "bagent.db"


def test_slate_ticket_synthesizer_build_ticket():
    synth = SlateTicketSynthesizer(db_path=DB_PATH)

    matches_sample = [
        {"home_team": "Monza", "away_team": "Cagliari", "tournament": "Serie A", "kickoff": "2026-10-19 18:30 CEST", "markets": {"DOPPIA_CHANCE": {"1X": 1.36}}},
        {"home_team": "Viborg", "away_team": "Midtjylland", "tournament": "Superligaen DEN", "kickoff": "2026-10-19 19:00 CEST", "markets": {"GOL_NOGOL": {"Gol": 1.47}}},
        {"home_team": "Trabzonspor", "away_team": "Besiktas", "tournament": "Super Lig TUR", "kickoff": "2026-10-19 19:00 CEST", "markets": {"CHANCE_MIX": {"Chance Mix: X o Gol": 1.35}}},
        {"home_team": "Parma", "away_team": "Torino", "tournament": "Serie A", "kickoff": "2026-10-19 20:45 CEST", "markets": {}},
        {"home_team": "Tottenham", "away_team": "Coventry", "tournament": "Premier League", "kickoff": "2026-10-19 21:00 CEST", "markets": {"COMBO": {"1X + Over 1.5": 1.36}}},
        {"home_team": "Braga", "away_team": "Gil Vicente", "tournament": "Liga Portugal", "kickoff": "2026-10-19 21:15 CEST", "markets": {}},
        {"home_team": "Jong PSV", "away_team": "Dordrecht", "tournament": "Eerste Divisie", "kickoff": "2026-10-19 20:00 CEST", "markets": {}},
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

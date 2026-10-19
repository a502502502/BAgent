"""
tests/test_on_demand_ingestion_regola90.py — Test per l'ingestione on-demand e cross-analisi bilaterale (Regola #90).
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
import pytest

from services.football.external.on_demand_ingestor import OnDemandMatchIngestor
from services.analysis.rolling_ten_engine import RollingTenEngine

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "bagent.db"


def test_on_demand_ingestor_parse_section():
    ingestor = OnDemandMatchIngestor(db_path=DB_PATH)
    sample_section = (
        "Last matches: SampleTeam¬"
        "~KC÷1791568800¬KP÷dummy1¬KF÷Eerste Divisie¬KJ÷Sample Home¬KK÷Sample Away¬KU÷2¬KT÷1¬KL÷2:1¬"
        "~KC÷1791560000¬KP÷dummy2¬KF÷Eerste Divisie¬KJ÷Sample Away¬KK÷Other Team¬KU÷0¬KT÷3¬KL÷0:3¬"
    )
    matches = ingestor._parse_section(sample_section, max_matches=10)
    assert len(matches) == 2
    assert matches[0]["home_team"] == "Sample Home"
    assert matches[0]["away_team"] == "Sample Away"
    assert matches[0]["home_goals"] == 2
    assert matches[0]["away_goals"] == 1
    assert matches[0]["total_goals"] == 3


def test_cross_analyze_match_bilateral_execution():
    engine = RollingTenEngine()
    # Verifica che Jong PSV e Dordrecht abbiano dati completi e calcolo bilaterale attivo
    res = engine.cross_analyze_match("Jong PSV", "Dordrecht", auto_download=False)
    assert res.get("status") == "OK"
    assert len(res.get("netwin_gems", [])) > 0
    assert len(res.get("halftime_gems", [])) > 0

    # Verifica che le gemme riflettano entrambe le squadre
    gems = res.get("netwin_gems", [])
    markets = [g["market"] for g in gems]
    assert any("Jong PSV" in m or "Partita" in m or "Chance Mix" in m for m in markets)

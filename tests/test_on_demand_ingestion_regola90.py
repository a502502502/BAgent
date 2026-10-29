"""
tests/test_on_demand_ingestion_regola90.py — Test per l'ingestione on-demand e cross-analisi bilaterale (Regola #90).
"""

from __future__ import annotations
import sqlite3
from pathlib import Path
import pytest

from services.football.external.on_demand_ingestor import (
    OnDemandMatchIngestor,
    names_match,
    season_label,
)
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
    assert matches[0]["season"] == season_label(matches[0]["match_date"])


def test_season_label_follows_european_calendar():
    assert season_label("2026-03-15") == "2025/2026"
    assert season_label("2026-10-19") == "2026/2027"
    assert season_label("2027-02-01") == "2026/2027"


def test_find_match_id_requires_both_teams(monkeypatch):
    feed = [
        {"home": "AC Milan", "away": "Lecce", "match_id": "milan-lecce"},
        {"home": "Inter", "away": "Juventus", "match_id": "inter-juve"},
    ]

    class FakeEngine:
        def fetch_feed(self):
            return feed

    monkeypatch.setattr(
        "services.football.external.sources.flashscore_live.FlashscoreLiveEngine",
        FakeEngine,
    )
    ingestor = OnDemandMatchIngestor(db_path=DB_PATH)
    assert ingestor.find_match_id("Inter", "Juventus") == "inter-juve"
    assert ingestor.find_match_id("Juventus", "Lecce") is None
    assert names_match("Real Madrid", "Real Madrid")


def test_insert_matches_leaves_halftime_unknown(tmp_path):
    db_path = tmp_path / "ingest.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE matches (
            id INTEGER PRIMARY KEY,
            league TEXT, season TEXT, status TEXT,
            home_team TEXT, away_team TEXT,
            home_goals INTEGER, away_goals INTEGER, total_goals INTEGER,
            ht_home_goals INTEGER, ht_away_goals INTEGER,
            match_date TEXT, updated_at TEXT
        )
        """
    )
    conn.commit()
    conn.close()

    ingestor = OnDemandMatchIngestor(db_path=db_path)
    inserted = ingestor._insert_matches([
        {
            "league": "Serie A",
            "season": "2025/2026",
            "match_date": "2026-03-15",
            "home_team": "Sample Home",
            "away_team": "Sample Away",
            "home_goals": 3,
            "away_goals": 1,
            "total_goals": 4,
        }
    ])
    assert inserted == 1
    conn = sqlite3.connect(db_path)
    row = conn.execute(
        "SELECT ht_home_goals, ht_away_goals, season FROM matches"
    ).fetchone()
    conn.close()
    assert row == (None, None, "2025/2026")


def test_parse_stats_and_ht_incidents():
    raw_stats = (
        "~SE÷Match¬"
        "~SD÷1¬SG÷Expected goals (xG)¬SH÷1.84¬SI÷0.72¬"
        "~SD÷2¬SG÷Total shots¬SH÷16¬SI÷8¬"
        "~SD÷3¬SG÷Shots on target¬SH÷6¬SI÷3¬"
        "~SD÷4¬SG÷Corner kicks¬SH÷7¬SI÷2¬"
        "~SD÷5¬SG÷Yellow cards¬SH÷2¬SI÷3¬"
        "~SE÷1st Half¬"
        "~SD÷6¬SG÷Total shots¬SH÷9¬SI÷4¬"
    )
    parsed = OnDemandMatchIngestor.parse_stats_feed(raw_stats)
    assert parsed["home_xg"] == 1.84
    assert parsed["away_xg"] == 0.72
    assert parsed["home_shots"] == 16
    assert parsed["away_shots"] == 8
    assert parsed["home_sot"] == 6
    assert parsed["away_sot"] == 3
    assert parsed["home_corners"] == 7
    assert parsed["away_corners"] == 2
    assert parsed["home_yellow"] == 2
    assert parsed["away_yellow"] == 3

    raw_inc = "~AC÷1st Half¬~IG÷1¬~IH÷0¬~AC÷2nd Half¬~IG÷2¬~IH÷1¬"
    ht = OnDemandMatchIngestor.parse_incidents_ht(raw_inc)
    assert ht == {"ht_home_goals": 1, "ht_away_goals": 0}


def test_cross_analyze_match_bilateral_execution():
    engine = RollingTenEngine()
    # Verifica che Sporting CP e Casa Pia (Tier-1 Liga Portugal) abbiano dati completi e calcolo bilaterale attivo
    res = engine.cross_analyze_match("Sporting CP", "Casa Pia", auto_download=False)
    assert res.get("status") == "OK"
    assert len(res.get("netwin_gems", [])) > 0

    # Verifica che le gemme riflettano entrambe le squadre
    gems = res.get("netwin_gems", [])
    markets = [g["market"] for g in gems]
    assert any("Sporting CP" in m or "Partita" in m or "Chance Mix" in m for m in markets)

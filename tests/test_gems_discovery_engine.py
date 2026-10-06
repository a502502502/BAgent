"""
tests/test_gems_discovery_engine.py — Test per GemsDiscoveryEngine.
"""

from datetime import datetime, timedelta, timezone
from services.analysis.gems_discovery_engine import (
    GemsDiscoveryEngine,
    GemPick,
    _poisson_ge,
    _poisson_pmf,
)

CEST = timezone(timedelta(hours=2))


def test_poisson_helpers():
    # Lambda = 1.0, P(X >= 1) = 1 - e^-1 = ~0.632
    p = _poisson_ge(1, 1.0)
    assert 0.63 < p < 0.64
    # P(X == 0) = e^-1 = ~0.368
    p0 = _poisson_pmf(0, 1.0)
    assert 0.36 < p0 < 0.37


def test_scan_team_combos_finds_gems():
    engine = GemsDiscoveryEngine()
    fake_catalog = {
        "match": "Croazia - Spagna",
        "kickoff_time": "2026-10-06 20:45 CEST",
        "fetched_at": "2026-10-06 14:07 CEST",
        "markets": [
            {
                "market": "1X2 ESITO FINALE",
                "line": "ESITO FINALE",
                "outcomes": [
                    {"selection": "1", "odds": 8.0, "open": True},
                    {"selection": "X", "odds": 4.5, "open": True},
                    {"selection": "2", "odds": 1.27, "open": True},
                ],
            },
            {
                "market": "COMBO: DC + MULTIGOAL",
                "line": "2-5",
                "outcomes": [
                    {"selection": "X2 + MultiGol 2-5", "odds": 1.45, "open": True},
                ],
            },
        ],
    }
    # xg_home=0.49, xg_away=2.93
    gems = engine.scan_catalog_for_gems(fake_catalog, 0.49, 2.93)
    # Dovrebbe estrarre X2 + MultiGol se ha probabilità e edge positivo
    assert isinstance(gems, list)


def test_select_best_gems_slate_enforces_max_1_per_match():
    engine = GemsDiscoveryEngine()
    gems = [
        GemPick(
            match_name="Match A",
            kickoff_time="2026-10-06 20:45 CEST",
            category="ASYMMETRIC_COMBO",
            market="X2",
            selection="X2",
            book_odd=1.50,
            probability=0.75,
            fair_odd=1.33,
            edge=0.125,
            safety_clause="Test clause",
            lineup_status="SQUADRA_NON_DIPENDENTE",
            rationale="Test",
            tier="DIAMANTE",
        ),
        GemPick(
            match_name="Match A",
            kickoff_time="2026-10-06 20:45 CEST",
            category="PLAYER_PROPS_SAFETY",
            market="Quasi Cartellino",
            selection="Player 1 Quasi Cartellino",
            book_odd=1.80,
            probability=0.65,
            fair_odd=1.54,
            edge=0.170,
            safety_clause="Test clause",
            lineup_status="TITOLARE_CONFERMATO",
            rationale="Test",
            tier="DIAMANTE",
        ),
        GemPick(
            match_name="Match B",
            kickoff_time="2026-10-06 20:45 CEST",
            category="ASYMMETRIC_COMBO",
            market="Over 1.5",
            selection="Over 1.5",
            book_odd=1.40,
            probability=0.80,
            fair_odd=1.25,
            edge=0.120,
            safety_clause="Test clause",
            lineup_status="SQUADRA_NON_DIPENDENTE",
            rationale="Test",
            tier="DIAMANTE",
        ),
    ]

    selected = engine.select_best_gems_slate(gems, max_total=2, max_per_match=1)
    assert len(selected) == 2
    # Match A deve apparire una sola volta (la migliore con edge 0.170)
    match_names = [g.match_name for g in selected]
    assert match_names.count("Match A") == 1
    assert match_names.count("Match B") == 1
    assert selected[0].selection == "Player 1 Quasi Cartellino"

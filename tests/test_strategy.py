import pytest
from services.analysis.omni_market_scanner import OmniMarketScanner
from services.live.siege_engine import SiegeEngine
from domain.models import MarketData

def test_corner_filter_blocks_low_volume():
    scanner = OmniMarketScanner()
    stats = {"avg_total_shots": 12, "team_name": "Team Difensivo"}
    result = scanner.filter_corner_markets(stats, "Over 8.5 Corner", 1.50, 0.70)
    assert result is None, "Il mercato corner dovrebbe essere bloccato per basso volume di tiri."

def test_siege_engine_triggers_on_upset():
    engine = SiegeEngine()
    # Favorita a 1.40 che perde 0-1 al 30'
    opportunities = engine.check_siege_trigger("Big Team", "Underdog", 1.40, (0, 1), 30)
    assert len(opportunities) > 0, "L'engine dovrebbe generare opportunità durante un assedio."

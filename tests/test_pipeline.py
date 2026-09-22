import pytest
from domain.models import MarketData, MatchContext
from services.betting.strict_ticket_pipeline import StrictTicketPipeline

def test_edge_calculation():
    market = MarketData(market_name="Over 2.5", quota=1.80, probabilita_reale=0.60)
    assert market.edge == 0.08

def test_negative_edge_rejection():
    # Nota: Questo test richiede che la pipeline sia istanziata correttamente
    # Per ora testiamo solo il modello
    market = MarketData(market_name="1 Fisso", quota=1.20, probabilita_reale=0.70)
    assert market.edge < 0 # Edge negativo

def test_low_odds_gate():
    with pytest.raises(ValueError):
        MarketData(market_name="1 Fisso", quota=1.10, probabilita_reale=0.90)

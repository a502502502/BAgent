"""Unit tests for CertifiedTicketPublisher mapping."""

from services.betting.certified_ticket_publisher import candidate_to_netwin_selection
from services.betting.strict_ticket_pipeline import MarketCandidate, ValidationReport


def test_candidate_maps_home_away_and_odd():
    c = MarketCandidate(
        match_name="Roma vs Lazio",
        tournament="Serie A",
        market_name="1X + Over 1.5",
        bookmaker_odd=1.55,
        netwin_actual_odd=1.52,
        sixth_sense_analysis="Derby coperto.",
    )
    rep = ValidationReport(
        passed=True,
        candidate=c,
        real_probability=0.8,
        fair_odds=1.25,
        mathematical_edge=0.216,
    )
    sel = candidate_to_netwin_selection(c, rep)
    assert sel["home"] == "Roma"
    assert sel["away"] == "Lazio"
    assert sel["netwin_odds"] == 1.52
    assert abs(sel["edge_pct"] - 21.6) < 0.01

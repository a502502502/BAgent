"""Test per il generatore di schedine certificate Sudamerica (scripts/generate_latam_tickets.py)."""

from scripts.generate_latam_tickets import (
    is_45_min_market,
    build_disjoint_tickets,
)
from services.betting.netwin_cache_reader import NetwinGem
from services.betting.strict_ticket_pipeline import MarketCandidate, ValidationReport


def _make_certified_item(match: str, tournament: str, market: str, odd: float, prob: float, edge: float, dna: str = "GREEN"):
    gem = NetwinGem(
        match_name=match,
        tournament=tournament,
        market=market,
        book_odd=odd,
        fair_odd=round(1.0 / prob, 2) if prob > 0 else 99.0,
        probability=prob,
        edge=edge,
        notes="test gem",
    )
    cand = MarketCandidate(
        match_name=match,
        tournament=tournament,
        market_name=market,
        bookmaker_odd=odd,
    )
    rep = ValidationReport(
        passed=True,
        candidate=cand,
        real_probability=prob,
        fair_odds=round(1.0 / prob, 2) if prob > 0 else 99.0,
        mathematical_edge=edge,
    )
    return {
        "gem": gem,
        "candidate": cand,
        "report": rep,
        "dna_status": dna,
        "priority": 2 if dna == "GREEN" else 1,
    }


def test_is_45_min_market():
    assert is_45_min_market("MultiGol 0-1 1° Tempo") is True
    assert is_45_min_market("Under 1.5 1°T") is True
    assert is_45_min_market("1X Primo Tempo") is True
    assert is_45_min_market("Under 3.5") is False
    assert is_45_min_market("1X + MultiGol 1-5") is False
    assert is_45_min_market("Chance Mix: 1 o Under 2.5") is False


def test_build_disjoint_tickets_enforces_no_overlap():
    items = [
        _make_certified_item("Match A vs Match B", "Brasile", "1X + Under 3.5", 1.45, 0.78, 0.13),
        _make_certified_item("Match C vs Match D", "Argentina", "Under 2.5", 1.50, 0.76, 0.14),
        _make_certified_item("Match E vs Match F", "Brasile", "DNB 1", 1.60, 0.74, 0.18),
        _make_certified_item("Match G vs Match H", "Argentina", "MultiGol 1-4", 1.35, 0.85, 0.15),
        _make_certified_item("Match I vs Match J", "Brasile", "NoGol o Under 2.5", 1.55, 0.75, 0.16),
    ]
    bankroll = 37.32
    tickets = build_disjoint_tickets(items, bankroll)

    # Con 5 match disgiunti: Raddoppio usa 2 match, Tripla usa i restanti 3 match
    assert len(tickets) == 2

    raddoppio = tickets[0]
    tripla = tickets[1]

    raddoppio_matches = {item["gem"].match_name for item in raddoppio["legs"]}
    tripla_matches = {item["gem"].match_name for item in tripla["legs"]}

    assert len(raddoppio_matches) == 2
    assert len(tripla_matches) == 3
    # NESSUNA SOVRAPPOSIZIONE tra i ticket!
    assert raddoppio_matches.isdisjoint(tripla_matches)


def test_build_disjoint_tickets_insufficient_matches():
    # Solo 1 selezione certificata: non si forza la schedina
    items = [
        _make_certified_item("Match A vs Match B", "Brasile", "1X + Under 3.5", 1.45, 0.78, 0.13),
    ]
    tickets = build_disjoint_tickets(items, bankroll=37.32)
    assert len(tickets) == 0  # NO BET


def test_quantitative_engine_first_half_pricing():
    from services.analysis.xg_poisson_engine import QuantitativeEngine
    engine = QuantitativeEngine()
    prob_mg = engine.goal_market_probability(1.1, 1.0, "MultiGol 0-1 1° Tempo")
    prob_u15 = engine.goal_market_probability(1.1, 1.0, "Under 1.5 1° Tempo")
    prob_1x = engine.goal_market_probability(1.1, 1.0, "1X 1° Tempo")

    assert prob_mg is not None and prob_mg > 0.70
    assert prob_u15 is not None and prob_u15 > 0.70
    assert prob_1x is not None and prob_1x > 0.70
    assert abs(prob_mg - prob_u15) < 1e-4  # MultiGol 0-1 coincides with Under 1.5 in goal count


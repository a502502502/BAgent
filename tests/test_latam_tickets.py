"""Test per il generatore di schedine certificate Sudamerica (scripts/generate_latam_tickets.py)."""

from scripts.generate_latam_tickets import (
    pick_best_gem_per_match,
    build_tickets,
)
from services.betting.netwin_cache_reader import NetwinGem


def _make_gem(match: str, tournament: str, market: str, odd: float, prob: float, edge: float) -> NetwinGem:
    return NetwinGem(
        match_name=match,
        tournament=tournament,
        market=market,
        book_odd=odd,
        fair_odd=round(1.0 / prob, 2) if prob > 0 else 99.0,
        probability=prob,
        edge=edge,
        notes="test gem",
    )


def test_pick_best_gem_per_match_deduplicates():
    gems = [
        _make_gem("Boca vs River", "Argentina", "1X", 1.30, 0.80, 0.04),
        _make_gem("Boca vs River", "Argentina", "1X + Under 3.5", 1.55, 0.76, 0.178),
        _make_gem("Flamengo vs Santos", "Brasile", "X2", 1.70, 0.70, 0.19),
    ]
    best = pick_best_gem_per_match(gems)
    # Deve esserci esattamente 1 gemma per partita
    assert len(best) == 2
    match_names = {g.match_name for g in best}
    assert match_names == {"Boca vs River", "Flamengo vs Santos"}

    # Su Boca vs River deve privilegiare la combo 1X + Under 3.5
    boca_gem = next(g for g in best if g.match_name == "Boca vs River")
    assert boca_gem.market == "1X + Under 3.5"


def test_build_tickets_generates_independent_tiers():
    best_gems = [
        _make_gem("Flamengo vs Santos", "Brasile", "X2", 1.76, 0.798, 0.405),
        _make_gem("Remo vs Gremio", "Brasile", "MultiGol 0-1 1° Tempo", 1.66, 0.764, 0.268),
        _make_gem("Tucuman vs Barracas", "Argentina", "MultiGol 0-1 Casa", 1.46, 0.858, 0.253),
        _make_gem("Vitoria vs Chapecoense", "Brasile", "MultiGol 0-1 1° Tempo", 1.65, 0.745, 0.230),
    ]
    bankroll = 37.32
    tickets = build_tickets(best_gems, bankroll)

    assert len(tickets) == 3

    # Raddoppio
    raddoppio = tickets[0]
    assert raddoppio["type"] == "RADDOPPIO_PROTETTO_LATAM"
    assert len(raddoppio["legs"]) == 2
    assert raddoppio["legs"][0].match_name != raddoppio["legs"][1].match_name
    assert raddoppio["total_odds"] >= 2.0
    assert raddoppio["recommended_stake_eur"] > 0

    # Tripla
    tripla = tickets[1]
    assert tripla["type"] == "TRIPLA_BLINDATA_LATAM"
    assert len(tripla["legs"]) == 3
    leg_matches = [leg.match_name for leg in tripla["legs"]]
    assert len(set(leg_matches)) == 3  # Indipendenza totale

    # Master
    master = tickets[2]
    assert master["type"] == "MASTER_LATAM_COMBO"
    assert len(master["legs"]) == 4
    master_matches = [leg.match_name for leg in master["legs"]]
    assert len(set(master_matches)) == 4

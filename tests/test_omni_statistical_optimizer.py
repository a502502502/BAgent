import pytest
from services.analysis.omni_statistical_optimizer import (
    MatchDossier,
    OmniStatisticalPricer,
    CombinatorialPortfolioOptimizer
)


def test_corner_1x2_pricing():
    pricer = OmniStatisticalPricer()
    # Team 1 averaging 6.5 corners, Team 2 averaging 3.5 corners
    probs = pricer.price_corner_1x2(6.5, 3.5)
    assert abs(sum(probs.values()) - 1.0) < 1e-4
    assert probs["1"] > probs["2"]
    assert probs["1"] > probs["X"]


def test_race_to_corners_pricing():
    pricer = OmniStatisticalPricer()
    # Team 1 strong on corners (7.5) vs Team 2 weak (2.5), race to 5
    races = pricer.price_race_to_corners(7.5, 2.5, target_corners=5)
    assert abs(sum(races.values()) - 1.0) < 1e-4
    assert races["TEAM 1"] > races["TEAM 2"]
    assert races["TEAM 1"] > races["NESSUNO"]


def test_player_fouls_over_pricing():
    pricer = OmniStatisticalPricer()
    # Player with 2.1 fouls average vs 1.5 threshold
    p = pricer.price_player_fouls_over(2.1, threshold=1.5)
    assert 0.55 < p < 0.70


def test_player_prop_ultra_pricing():
    pricer = OmniStatisticalPricer()
    # Attacking forward with xG/90 = 0.58
    p = pricer.price_player_prop_ultra(0.58, minutes=75.0)
    assert 0.40 < p < 0.65


def test_omni_pricer_multi_markets():
    pricer = OmniStatisticalPricer()
    dossier = MatchDossier(
        match_name="Italia vs Turchia",
        xg_home=2.05,
        xg_away=0.80,
        corners_home=6.5,
        corners_away=3.2,
        cards_home=1.8,
        cards_away=2.6,
        lineup_confirmed=True,
        corners_certified=True,
        players={
            "scamacca": {"xg_90": 0.58, "fouls_avg": 1.2, "minutes": 75},
            "celik": {"xg_90": 0.05, "fouls_avg": 2.1, "minutes": 90}
        }
    )

    refused = pricer.price_market(
        MatchDossier(match_name="Italia vs Turchia", players={"scamacca": {"xg_90": 0.58}}),
        "Marcatore Piu Ultra Scamacca G.",
        "SI",
        book_odd=1.80,
    )
    assert refused is None

    pick_prop = pricer.price_market(dossier, "Marcatore Piu Ultra Scamacca G.", "SI", book_odd=1.80)
    assert pick_prop is not None
    assert pick_prop.blocked is None
    assert pick_prop.score > 0

    pick_foul = pricer.price_market(dossier, "U/O Falli Commessi Giocatore: Celik Zeki U/O 1.5", "OVER", book_odd=2.00)
    assert pick_foul is not None
    assert pick_foul.blocked is None
    assert pick_foul.score > 0

    pick_corner = pricer.price_market(dossier, "Calci Angolo 1X2", "1", book_odd=1.35)
    assert pick_corner is not None
    assert pick_corner.blocked is None

    pick_mg = pricer.price_market(dossier, "MultiGol Squadra 1 Multiesiti", "1-3", book_odd=1.33)
    assert pick_mg is not None
    assert pick_mg.blocked == "tetto su attacco dominante"


def test_portfolio_optimizer_diversity():
    pricer = OmniStatisticalPricer()
    optimizer = CombinatorialPortfolioOptimizer(pricer=pricer)

    d1 = MatchDossier("Italia vs Turchia", xg_home=1.6, xg_away=1.1, corners_home=6.5, corners_away=3.2,
                      lineup_confirmed=True,
                      players={"scamacca": {"xg_90": 0.6, "fouls_avg": 1.0}, "celik": {"xg_90": 0.0, "fouls_avg": 2.1}})
    d2 = MatchDossier("Francia vs Belgio", xg_home=1.8, xg_away=1.0, corners_home=5.5, corners_away=4.0)
    d3 = MatchDossier("Romania vs Svezia", xg_home=1.1, xg_away=1.6, corners_home=3.5, corners_away=6.0, corners_certified=True)
    d4 = MatchDossier("Irlanda del Nord vs Georgia", xg_home=1.0, xg_away=0.9, corners_home=4.5, corners_away=4.0)

    markets_d1 = [
        {"market": "Marcatore Piu Ultra Scamacca", "line": "", "outcomes": [{"selection": "SI", "odds": 1.80}]},
        {"market": "U/O Falli Celik 1.5", "line": "", "outcomes": [{"selection": "OVER", "odds": 2.00}]}
    ]
    markets_d2 = [
        {"market": "MultiGol Squadra 1 Multiesiti", "line": "", "outcomes": [{"selection": "1-3", "odds": 1.33}]}
    ]
    markets_d3 = [
        {"market": "1X2 Corner", "line": "", "outcomes": [{"selection": "2", "odds": 1.60}]}
    ]
    markets_d4 = [
        {"market": "Combo Chance: 1 o NoGoal", "line": "", "outcomes": [{"selection": "1 O NOGOAL", "odds": 1.26}]}
    ]

    picks_by_match = {
        "Italia vs Turchia": optimizer.generate_candidate_picks(d1, markets_d1),
        "Francia vs Belgio": optimizer.generate_candidate_picks(d2, markets_d2),
        "Romania vs Svezia": optimizer.generate_candidate_picks(d3, markets_d3),
        "Irlanda del Nord vs Georgia": optimizer.generate_candidate_picks(d4, markets_d4),
    }

    portfolio = optimizer.build_diversified_portfolio(
        [d1, d2, d3, d4],
        picks_by_match,
        num_tickets=1,
        ticket_size=4,
        stake_per_ticket=2.50
    )

    assert len(portfolio["tickets"]) == 1
    t1 = portfolio["tickets"][0]
    assert len(t1["legs"]) == 4
    # All legs come from different matches
    matches = [leg["match"] for leg in t1["legs"]]
    assert len(set(matches)) == 4
    # Families are diversified
    families = [leg["market_family"] for leg in t1["legs"]]
    assert len(set(families)) >= 3

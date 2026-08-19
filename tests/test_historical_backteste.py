from application.analyzer import Analyzer

from application.factors.factor_registry import (
    FactorRegistry,
)

from application.factors.ranking_factor import (
    RankingFactor,
)

from application.factors.surface_factor import (
    SurfaceFactor,
)

from application.validation.historical_backtester import (
    HistoricalBacktester,
)

from application.validation.tennis_abstract_dataset import (
    TennisAbstractDataset,
)

from infrastructure.persistence.knowledge_repository import (
    KnowledgeRepository,
)


# =========================================================
# PLAYERS
# =========================================================

PLAYERS = {
    "JannikSinner": "Jannik Sinner",
    "CarlosAlcaraz": "Carlos Alcaraz",
    "NovakDjokovic": "Novak Djokovic",
    "AlexanderZverev": "Alexander Zverev",
    "DaniilMedvedev": "Daniil Medvedev",
    "TaylorFritz": "Taylor Fritz",
    "AndreyRublev": "Andrey Rublev",
    "AlexDeMinaur": "Alex De Minaur",
    "CasperRuud": "Casper Ruud",
    "HolgerRune": "Holger Rune",
    "StefanosTsitsipas": "Stefanos Tsitsipas",
    "AlexanderBublik": "Alexander Bublik",
    "BenShelton": "Ben Shelton",
    "TommyPaul": "Tommy Paul",
    "FranciscoCerundolo": "Francisco Cerundolo",
    "DaniilMedvedev": "Daniil Medvedev",
    "KarenKhachanov": "Karen Khachanov",
    "GrigorDimitrov": "Grigor Dimitrov",
    "LorenzoMusetti": "Lorenzo Musetti",
    "JackDraper": "Jack Draper",
}


# =========================================================
# DATASET
# =========================================================

print()
print("=" * 60)
print("TENNIS ABSTRACT HISTORICAL DATASET")
print("=" * 60)

print()
print(
    f"Requested players: {len(PLAYERS)}"
)

dataset = TennisAbstractDataset()

historical_matches = dataset.collect(
    PLAYERS
)

print()
print(
    f"Historical matches collected: "
    f"{len(historical_matches)}"
)

assert len(historical_matches) > 0


# =========================================================
# AVAILABLE PLAYERS
# =========================================================

available_players = set()

for historical in historical_matches:

    match = historical.match

    available_players.add(
        match.home.id
    )

    available_players.add(
        match.away.id
    )

print()
print(
    f"Players represented in dataset: "
    f"{len(available_players)}"
)

print()

for player_id in sorted(
    available_players
):

    player_name = PLAYERS.get(
        player_id,
        player_id
    )

    print(
        f"- {player_id}: "
        f"{player_name}"
    )


# =========================================================
# BACKTEST HELPER
# =========================================================

def build_backtester(
    use_surface: bool,
):

    knowledge_repository = (
        KnowledgeRepository()
    )

    registry = FactorRegistry()

    registry.register(
        RankingFactor()
    )

    if use_surface:

        registry.register(
            SurfaceFactor()
        )

    analyzer = Analyzer(
        knowledge_repository=(
            knowledge_repository
        ),
        registry=registry,
    )

    return HistoricalBacktester(
        analyzer=analyzer,
        ranking_history=None,
    )


# =========================================================
# RANKING + SURFACE
# =========================================================

print()
print("=" * 60)
print("RANKING + SURFACE BACKTEST")
print("=" * 60)

backtester = build_backtester(
    use_surface=True
)

report = backtester.run(
    historical_matches
)

print()
print(
    f"Matches: {report.matches}"
)

print(
    f"Accuracy: "
    f"{report.accuracy:.4f}"
)

print(
    f"Log Loss: "
    f"{report.log_loss:.4f}"
)

print(
    f"Brier Score: "
    f"{report.brier_score:.4f}"
)


# =========================================================
# SUMMARY
# =========================================================

surfaces = sorted(
    {
        historical.match.court_name
        for historical in historical_matches
        if historical.match.court_name
    }
)

print()
print("=" * 60)
print("DATASET SUMMARY")
print("=" * 60)

print(
    f"Requested players: "
    f"{len(PLAYERS)}"
)

print(
    f"Players represented: "
    f"{len(available_players)}"
)

print(
    f"Matches: "
    f"{len(historical_matches)}"
)

print(
    f"Surfaces: "
    f"{surfaces}"
)

print()
print(
    "HISTORICAL BACKTEST COMPLETED"
)
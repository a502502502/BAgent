from application.analyzer import Analyzer

from application.factors.factor_registry import FactorRegistry
from application.factors.ranking_factor import RankingFactor

from application.validation.ranking_history import (
    RankingHistory,
    RankingSnapshot,
)

from application.validation.historical_analizer import (
    HistoricalAnalyzer,
)

from application.validation.historical_match import (
    HistoricalMatch,
)

from domain.models.competition import Competition
from domain.models.competitor import Competitor
from domain.models.match import Match

from infrastructure.persistence.knowledge_repository import (
    KnowledgeRepository,
)


# ---------------------------------------------------------
# HISTORICAL RANKING
# ---------------------------------------------------------

ranking_history = RankingHistory(
    [
        RankingSnapshot(
            date="2026-01-01",
            rankings={
                "Sinner": 1,
                "Alcaraz": 2,
            },
        ),
    ]
)


# ---------------------------------------------------------
# FACTOR REGISTRY
# ---------------------------------------------------------

registry = FactorRegistry()

registry.register(
    RankingFactor()
)


# ---------------------------------------------------------
# ANALYZER
# ---------------------------------------------------------

analyzer = Analyzer(
    knowledge_repository=KnowledgeRepository(),
    registry=registry,
)


# ---------------------------------------------------------
# COMPETITION
# ---------------------------------------------------------

competition = Competition(
    id="ATP001",
    name="Test Tournament",
)


# ---------------------------------------------------------
# PLAYERS
# ---------------------------------------------------------

sinner = Competitor(
    id="Sinner",
    name="Jannik Sinner",
    country="Italy",
)

alcaraz = Competitor(
    id="Alcaraz",
    name="Carlos Alcaraz",
    country="Spain",
)


# ---------------------------------------------------------
# MATCH
# ---------------------------------------------------------

match = Match(
    id="TEST-001",
    competition=competition,
    home=sinner,
    away=alcaraz,
    round_name="F",
    court_name="Hard",
    status="Completed",
    start_time="2026-01-05",
    winner="Sinner",
)


historical_match = HistoricalMatch(
    match=match,
    winner_id="Sinner",
    date="2026-01-05",
)


# ---------------------------------------------------------
# HISTORICAL ANALYZER
# ---------------------------------------------------------

historical_analyzer = HistoricalAnalyzer(
    analyzer=analyzer,
    ranking_history=ranking_history,
)


analysis = historical_analyzer.analyze(
    historical_match
)


# ---------------------------------------------------------
# ASSERTIONS
# ---------------------------------------------------------

assert analysis is not None
assert analysis.rating is not None
assert analysis.probability is not None
assert analysis.fair_odds is not None

assert len(
    analysis.contributions
) == 1


# ---------------------------------------------------------
# OUTPUT
# ---------------------------------------------------------

print()
print("=" * 60)
print("HISTORICAL ANALYSIS")
print("=" * 60)

print(
    f"{match.home.name} vs {match.away.name}"
)

print(
    f"Rating: {analysis.rating}"
)

print(
    f"Home probability: "
    f"{analysis.probability.home:.4f}"
)

print(
    f"Away probability: "
    f"{analysis.probability.away:.4f}"
)

print(
    f"Home fair odds: "
    f"{analysis.fair_odds.home:.2f}"
)

print(
    f"Away fair odds: "
    f"{analysis.fair_odds.away:.2f}"
)

print()
print("HISTORICAL ANALYZER TEST PASSED")
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
# TENNIS ABSTRACT DATASET
# =========================================================

print()
print("=" * 60)
print("TENNIS ABSTRACT HISTORICAL DATASET")
print("=" * 60)

dataset = TennisAbstractDataset()

historical_matches = dataset.collect(
    {
        "JannikSinner": "Jannik Sinner",
        "CarlosAlcaraz": "Carlos Alcaraz",
    }
)

print()
print(
    f"Matches: {len(historical_matches)}"
)

assert len(historical_matches) == 47


# =========================================================
# KNOWLEDGE REPOSITORY
# =========================================================

knowledge_repository = KnowledgeRepository()


# =========================================================
# FACTOR REGISTRY
# =========================================================

registry = FactorRegistry()

registry.register(
    RankingFactor()
)

registry.register(
    SurfaceFactor()
)


# =========================================================
# ANALYZER
# =========================================================

analyzer = Analyzer(
    knowledge_repository=knowledge_repository,
    registry=registry,
)


# =========================================================
# HISTORICAL BACKTESTER
# =========================================================

backtester = HistoricalBacktester(
    analyzer=analyzer,
    ranking_history=None,
)


# =========================================================
# RUN
# =========================================================

report = backtester.run(
    historical_matches
)


# =========================================================
# FINAL SUMMARY
# =========================================================

print()
print("=" * 60)
print("TENNIS ABSTRACT HISTORICAL BACKTEST")
print("=" * 60)

print(
    f"Matches: {report.matches}"
)

print(
    f"Accuracy: {report.accuracy:.4f}"
)

print(
    f"Log Loss: {report.log_loss:.4f}"
)

print(
    f"Brier Score: {report.brier_score:.4f}"
)


# =========================================================
# ASSERTIONS
# =========================================================

assert report.matches == 47

assert 0.0 <= report.accuracy <= 1.0

assert report.log_loss >= 0.0

assert report.brier_score >= 0.0


print()
print("REAL HISTORICAL BACKTEST PASSED")
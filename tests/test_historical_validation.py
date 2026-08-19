from datetime import datetime

from infrastructure.persistence.knowledge_repository import (
    KnowledgeRepository
)

from application.analyzer import Analyzer
from application.factors.factor_registry import FactorRegistry
from application.factors.ranking_factor import RankingFactor
from application.validation.historical_loader import (
    HistoricalMatchLoader
)
from application.validation.validator import Validator

from domain.models.knowledge import Knowledge


DATASET = "data/historical/atp_matches.csv"


# ---------------------------------------------------------
# KNOWLEDGE
# ---------------------------------------------------------

repository = KnowledgeRepository()

repository.save(
    Knowledge(
        id="KN-001",
        entity_type="PLAYER",
        entity_id="JannikSinner",
        key="ATP_RANK",
        value=1,
        value_type="INTEGER",
        source="ATP",
        confidence=1.0,
        collected_at=datetime.utcnow()
    )
)

repository.save(
    Knowledge(
        id="KN-002",
        entity_type="PLAYER",
        entity_id="CarlosAlcaraz",
        key="ATP_RANK",
        value=2,
        value_type="INTEGER",
        source="ATP",
        confidence=1.0,
        collected_at=datetime.utcnow()
    )
)


# ---------------------------------------------------------
# ANALYZER
# ---------------------------------------------------------

registry = FactorRegistry()

registry.register(
    RankingFactor()
)

analyzer = Analyzer(
    knowledge_repository=repository,
    registry=registry
)


# ---------------------------------------------------------
# DATASET
# ---------------------------------------------------------

loader = HistoricalMatchLoader()

historical_matches = loader.load(
    DATASET
)


# ---------------------------------------------------------
# VALIDATION
# ---------------------------------------------------------

validator = Validator(
    analyzer=analyzer
)

report = validator.evaluate(
    historical_matches
)


print(
    report.summary()
)


# ---------------------------------------------------------
# ASSERTIONS
# ---------------------------------------------------------

assert report.matches == 3

assert 0.0 <= report.accuracy <= 1.0

assert report.log_loss >= 0.0

assert report.brier_score >= 0.0

print()
print("HISTORICAL VALIDATION PASSED")
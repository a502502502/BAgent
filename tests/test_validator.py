from datetime import datetime

from infrastructure.persistence.knowledge_repository import (
    KnowledgeRepository
)

from application.analyzer import Analyzer
from application.factors.factor_registry import FactorRegistry
from application.factors.ranking_factor import RankingFactor
from application.validation.validator import Validator

from domain.models.knowledge import Knowledge
from domain.models.match import Match
from domain.models.competition import Competition
from domain.models.competitor import Competitor


repository = KnowledgeRepository()


repository.save(
    Knowledge(
        id="KN-TEST-001",
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
        id="KN-TEST-002",
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


match = Match(
    id="MATCH-TEST-001",

    competition=Competition(
        id="ATP-TEST",
        name="ATP Test"
    ),

    home=Competitor(
        id="JannikSinner",
        name="Jannik Sinner",
        country="ITA"
    ),

    away=Competitor(
        id="CarlosAlcaraz",
        name="Carlos Alcaraz",
        country="ESP"
    ),

    round_name="Final",
    status="Completed",
    winner="JannikSinner"
)


registry = FactorRegistry()

registry.register(
    RankingFactor()
)


analyzer = Analyzer(
    knowledge_repository=repository,
    registry=registry
)


validator = Validator(
    analyzer=analyzer
)


report = validator.evaluate(
    [match]
)


print(
    report.summary()
)


assert report.matches == 1

assert 0.0 <= report.accuracy <= 1.0

assert report.log_loss >= 0.0

assert report.brier_score >= 0.0


print()
print("VALIDATION TEST PASSED")
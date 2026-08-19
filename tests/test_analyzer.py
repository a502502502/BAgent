from datetime import datetime

from infrastructure.persistence.knowledge_repository import (
    KnowledgeRepository
)

from application.analyzer import Analyzer
from application.factors.factor_registry import FactorRegistry
from application.factors.ranking_factor import RankingFactor

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

    round_name="Test",
    court_name=None,
    status="Scheduled",
    start_time=None
)


registry = FactorRegistry()

registry.register(
    RankingFactor()
)


analyzer = Analyzer(
    knowledge_repository=repository,
    registry=registry
)


analysis = analyzer.analyze(match)


print()
print(analysis.summary())
print()


assert analysis.probability.home > 0
assert analysis.probability.home < 1

assert analysis.probability.away > 0
assert analysis.probability.away < 1

assert abs(
    analysis.probability.home +
    analysis.probability.away -
    1.0
) < 1e-9

assert analysis.fair_odds.home > 1
assert analysis.fair_odds.away > 1

assert len(analysis.contributions) == 1

print("TEST PASSED")
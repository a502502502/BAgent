from datetime import datetime

from infrastructure.persistence.knowledge_repository import (
    KnowledgeRepository
)

from application.analyzer import Analyzer
from application.factors.factor_registry import FactorRegistry
from application.factors.ranking_factor import RankingFactor
from application.validation.historical_match import HistoricalMatch
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
        entity_id="Juventus",
        key="LEAGUE_POSITION",
        value=1,
        value_type="INTEGER",
        source="SEASON_TABLE",
        confidence=1.0,
        collected_at=datetime.utcnow()
    )
)


repository.save(
    Knowledge(
        id="KN-TEST-002",
        entity_type="PLAYER",
        entity_id="Milan",
        key="LEAGUE_POSITION",
        value=2,
        value_type="INTEGER",
        source="SEASON_TABLE",
        confidence=1.0,
        collected_at=datetime.utcnow()
    )
)


match = Match(
    id="MATCH-TEST-001",

    competition=Competition(
        id="SERIEA-TEST",
        name="Serie A"
    ),

    home=Competitor(
        id="Juventus",
        name="Juventus",
        country="ITA"
    ),

    away=Competitor(
        id="Milan",
        name="Milan",
        country="ITA"
    ),

    round_name="Final",
    status="Completed",
    winner="Juventus"
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
    [HistoricalMatch(match=match, winner_id=match.home.id)]
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
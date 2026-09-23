from application.validation.ranking_history import (
    RankingHistory,
    RankingSnapshot,
)

from application.validation.historical_knowledge import (
    HistoricalKnowledge,
)

from infrastructure.persistence.knowledge_repository import (
    KnowledgeRepository,
)


history = RankingHistory(
    [
        RankingSnapshot(
            date="2026-01-01",
            rankings={
                "Juventus": 1,
                "Milan": 2,
            },
        ),
        RankingSnapshot(
            date="2026-01-08",
            rankings={
                "Juventus": 2,
                "Milan": 1,
            },
        ),
    ]
)


repository = KnowledgeRepository()

knowledge = HistoricalKnowledge(
    history
)

knowledge.populate(
    repository=repository,
    player_ids=[
        "Juventus",
        "Milan",
    ],
    date="2026-01-05",
)


sinner = repository.find_by_key(
    "Juventus",
    "LEAGUE_POSITION",
)

alcaraz = repository.find_by_key(
    "Milan",
    "LEAGUE_POSITION",
)


assert sinner is not None
assert alcaraz is not None

assert sinner.value == 1
assert alcaraz.value == 2


print()
print("HISTORICAL KNOWLEDGE TEST PASSED")
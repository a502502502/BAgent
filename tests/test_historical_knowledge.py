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
                "Sinner": 1,
                "Alcaraz": 2,
            },
        ),
        RankingSnapshot(
            date="2026-01-08",
            rankings={
                "Sinner": 2,
                "Alcaraz": 1,
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
        "Sinner",
        "Alcaraz",
    ],
    date="2026-01-05",
)


sinner = repository.find_by_key(
    "Sinner",
    "ATP_RANK",
)

alcaraz = repository.find_by_key(
    "Alcaraz",
    "ATP_RANK",
)


assert sinner is not None
assert alcaraz is not None

assert sinner.value == 1
assert alcaraz.value == 2


print()
print("HISTORICAL KNOWLEDGE TEST PASSED")
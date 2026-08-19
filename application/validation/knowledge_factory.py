from datetime import datetime

from domain.models.knowledge import Knowledge


class HistoricalKnowledgeFactory:

    def __init__(self):
        self.counter = 0

    def ranking(
        self,
        player_id: str,
        ranking: int,
        date: str
    ) -> Knowledge:

        self.counter += 1

        return Knowledge(
            id=f"HIST-RANK-{self.counter:06d}",
            entity_type="PLAYER",
            entity_id=player_id,
            key="ATP_RANK",
            value=ranking,
            value_type="INTEGER",
            source="ATP_HISTORICAL",
            confidence=1.0,
            collected_at=datetime.fromisoformat(
                date
            )
        )
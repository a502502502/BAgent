from datetime import datetime
from typing import Dict, List

from domain.models.knowledge import Knowledge


class HistoricalKnowledgeBuilder:

    def __init__(self):
        self._rankings: Dict[str, int] = {}
        self._counter = 0

    def update_ranking(
        self,
        rankings: Dict[str, int]
    ):

        self._rankings = dict(rankings)

    def build_for_match(
        self,
        player_ids: List[str]
    ) -> List[Knowledge]:

        knowledge = []

        for player_id in player_ids:

            rank = self._rankings.get(player_id)

            if rank is None:
                continue

            self._counter += 1

            knowledge.append(
                Knowledge(
                    id=f"HIST-KN-{self._counter:06d}",
                    entity_type="PLAYER",
                    entity_id=player_id,
                    key="ATP_RANK",
                    value=rank,
                    value_type="INTEGER",
                    source="ATP",
                    confidence=1.0,
                    collected_at=datetime.utcnow()
                )
            )

        return knowledge
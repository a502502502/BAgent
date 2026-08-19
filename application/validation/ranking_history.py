from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RankingSnapshot:
    date: str
    rankings: Dict[str, int]


class RankingHistory:

    def __init__(
        self,
        snapshots: List[RankingSnapshot]
    ):
        self.snapshots = sorted(
            snapshots,
            key=lambda x: x.date
        )

    def get_ranking(
        self,
        player_id: str,
        date: str
    ) -> Optional[int]:

        ranking = None

        for snapshot in self.snapshots:

            if snapshot.date > date:
                break

            if player_id in snapshot.rankings:
                ranking = snapshot.rankings[player_id]

        return ranking
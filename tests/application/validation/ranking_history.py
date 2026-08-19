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
            key=lambda item: item.date
        )

    def get_snapshot(
        self,
        date: str
    ) -> Optional[RankingSnapshot]:

        selected = None

        for snapshot in self.snapshots:

            if snapshot.date > date:
                break

            selected = snapshot

        return selected

    def get_ranking(
        self,
        player_id: str,
        date: str
    ) -> Optional[int]:

        snapshot = self.get_snapshot(date)

        if snapshot is None:
            return None

        return snapshot.rankings.get(
            player_id
        )
from datetime import datetime
from typing import Iterable, List

from models.historical_match import (
    HistoricalFootballMatch,
)


class FootballHistoricalDataset:

    def __init__(
        self,
        matches: Iterable[HistoricalFootballMatch],
    ):

        self.matches = sorted(
            list(matches),
            key=lambda item: item.date,
        )

    def all(self) -> List[HistoricalFootballMatch]:

        return list(self.matches)

    def completed(self) -> List[HistoricalFootballMatch]:

        return [
            item
            for item in self.matches
            if item.is_completed
        ]

    def before(
        self,
        date: datetime,
    ) -> List[HistoricalFootballMatch]:

        return [
            item
            for item in self.matches
            if item.date < date
        ]

    def completed_before(
        self,
        date: datetime,
    ) -> List[HistoricalFootballMatch]:

        return [
            item
            for item in self.matches
            if item.date < date
            and item.is_completed
        ]

    def up_to(
        self,
        date: datetime,
    ) -> List[HistoricalFootballMatch]:

        return [
            item
            for item in self.matches
            if item.date <= date
        ]

    def __len__(self) -> int:

        return len(self.matches)

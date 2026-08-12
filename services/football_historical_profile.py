from datetime import datetime
from typing import Dict

from models.football_profile import (
    FootballTeamProfile,
)

from services.football_historical_dataset import (
    FootballHistoricalDataset,
)

from services.football_profile_builder import (
    FootballProfileBuilder,
)


class FootballHistoricalProfile:

    DEFAULT_RECENCY_DECAY = 2.0

    def __init__(
        self,
        dataset: FootballHistoricalDataset,
    ):

        self.dataset = dataset

        self.builder = (
            FootballProfileBuilder()
        )

    def build_as_of(
        self,
        date: datetime,
    ) -> Dict[str, FootballTeamProfile]:

        historical_matches = (
            self.dataset.completed_before(
                date
            )
        )

        return self.builder.build(
            historical_match.match
            for historical_match
            in historical_matches
        )

    def build_recency_as_of(
        self,
        date: datetime,
        decay: float = DEFAULT_RECENCY_DECAY,
    ) -> Dict[str, FootballTeamProfile]:

        historical_matches = (
            self.dataset.completed_before(
                date
            )
        )

        return self.builder.build_recency(
            (
                historical_match.match
                for historical_match
                in historical_matches
            ),
            reference_date=date,
            decay=decay,
        )

    def get_team_profile(
        self,
        team_id: str,
        date: datetime,
    ) -> FootballTeamProfile | None:

        profiles = self.build_as_of(
            date
        )

        return profiles.get(
            team_id
        )

    def get_team_profile_recency(
        self,
        team_id: str,
        date: datetime,
        decay: float = DEFAULT_RECENCY_DECAY,
    ) -> FootballTeamProfile | None:

        profiles = self.build_recency_as_of(
            date=date,
            decay=decay,
        )

        return profiles.get(
            team_id
        )

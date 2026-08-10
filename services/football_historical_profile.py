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

    def __init__(
        self,
        dataset: FootballHistoricalDataset,
    ):

        self.dataset = dataset
        self.builder = FootballProfileBuilder()

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
            historical_matches_item.match
            for historical_matches_item
            in historical_matches
        )

    def get_team_profile(
        self,
        team_id: str,
        date: datetime,
    ) -> FootballTeamProfile | None:

        profiles = self.build_as_of(date)

        return profiles.get(team_id)

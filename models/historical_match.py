from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.football import FootballMatch
from models.football_odds import FootballMatchOdds
from models.football_statistics import FootballMatchStatistics


@dataclass(frozen=True)
class HistoricalFootballMatch:

    match: FootballMatch
    date: datetime

    statistics: Optional[
        FootballMatchStatistics
    ] = None

    odds: Optional[
        FootballMatchOdds
    ] = None

    winner: Optional[str] = None

    @property
    def match_id(self) -> str:
        return self.match.id

    @property
    def home_team_id(self) -> str:
        return self.match.home.id

    @property
    def away_team_id(self) -> str:
        return self.match.away.id

    @property
    def is_completed(self) -> bool:
        return self.match.is_completed

    @property
    def result(self) -> Optional[str]:
        return self.match.result

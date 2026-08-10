from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FootballTeam:

    id: str
    name: str


@dataclass(frozen=True)
class FootballMatch:

    id: str

    competition: str
    season: Optional[str]

    home: FootballTeam
    away: FootballTeam

    start_time: str

    home_goals: Optional[int] = None
    away_goals: Optional[int] = None

    status: str = "Scheduled"

    home_corners: Optional[float] = None
    away_corners: Optional[float] = None

    home_yellow_cards: Optional[float] = None
    away_yellow_cards: Optional[float] = None

    home_red_cards: Optional[float] = None
    away_red_cards: Optional[float] = None

    home_xg: Optional[float] = None
    away_xg: Optional[float] = None

    @property
    def is_completed(self) -> bool:

        return (
            self.status == "Completed"
            and self.home_goals is not None
            and self.away_goals is not None
        )

    @property
    def total_goals(self) -> Optional[int]:

        if not self.is_completed:
            return None

        return (
            self.home_goals
            + self.away_goals
        )

    @property
    def goal_difference(self) -> Optional[int]:

        if not self.is_completed:
            return None

        return (
            self.home_goals
            - self.away_goals
        )

    @property
    def result(self) -> Optional[str]:

        if not self.is_completed:
            return None

        if self.home_goals > self.away_goals:
            return "HOME"

        if self.home_goals < self.away_goals:
            return "AWAY"

        return "DRAW"

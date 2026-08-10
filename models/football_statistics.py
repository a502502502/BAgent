from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class FootballMatchStatistics:

    home_shots: Optional[int] = None
    away_shots: Optional[int] = None

    home_shots_on_target: Optional[int] = None
    away_shots_on_target: Optional[int] = None

    home_fouls: Optional[int] = None
    away_fouls: Optional[int] = None

    home_corners: Optional[int] = None
    away_corners: Optional[int] = None

    home_yellow_cards: Optional[int] = None
    away_yellow_cards: Optional[int] = None

    home_red_cards: Optional[int] = None
    away_red_cards: Optional[int] = None

    home_half_time_goals: Optional[int] = None
    away_half_time_goals: Optional[int] = None

    @property
    def total_shots(self) -> Optional[int]:

        if (
            self.home_shots is None
            or self.away_shots is None
        ):
            return None

        return (
            self.home_shots
            + self.away_shots
        )

    @property
    def total_corners(self) -> Optional[int]:

        if (
            self.home_corners is None
            or self.away_corners is None
        ):
            return None

        return (
            self.home_corners
            + self.away_corners
        )

    @property
    def total_yellow_cards(self) -> Optional[int]:

        if (
            self.home_yellow_cards is None
            or self.away_yellow_cards is None
        ):
            return None

        return (
            self.home_yellow_cards
            + self.away_yellow_cards
        )

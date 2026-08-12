from dataclasses import dataclass
from typing import Optional


@dataclass
class FootballTeamProfile:

    team_id: str
    team_name: str

    matches: float = 0.0

    wins: float = 0.0
    draws: float = 0.0
    losses: float = 0.0

    goals_for: float = 0.0
    goals_against: float = 0.0

    home_matches: float = 0.0
    home_wins: float = 0.0
    home_draws: float = 0.0
    home_losses: float = 0.0

    away_matches: float = 0.0
    away_wins: float = 0.0
    away_draws: float = 0.0
    away_losses: float = 0.0

    corners_for: float = 0.0
    corners_against: float = 0.0

    yellow_cards: float = 0.0
    red_cards: float = 0.0

    xg_for: float = 0.0
    xg_against: float = 0.0

    clean_sheets: float = 0.0
    btts_matches: float = 0.0

    @property
    def win_rate(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return self.wins / self.matches

    @property
    def draw_rate(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return self.draws / self.matches

    @property
    def loss_rate(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return self.losses / self.matches

    @property
    def goals_for_per_match(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return self.goals_for / self.matches

    @property
    def goals_against_per_match(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return self.goals_against / self.matches

    @property
    def goal_difference(self) -> float:

        return (
            self.goals_for
            - self.goals_against
        )

    @property
    def clean_sheet_rate(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return (
            self.clean_sheets
            / self.matches
        )

    @property
    def btts_rate(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return (
            self.btts_matches
            / self.matches
        )

    @property
    def average_corners_for(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return (
            self.corners_for
            / self.matches
        )

    @property
    def average_corners_against(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return (
            self.corners_against
            / self.matches
        )

    @property
    def average_yellow_cards(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return (
            self.yellow_cards
            / self.matches
        )

    @property
    def average_red_cards(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return (
            self.red_cards
            / self.matches
        )

    @property
    def average_xg_for(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return (
            self.xg_for
            / self.matches
        )

    @property
    def average_xg_against(self) -> Optional[float]:

        if self.matches <= 0:
            return None

        return (
            self.xg_against
            / self.matches
        )

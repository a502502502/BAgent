from dataclasses import dataclass
from typing import Optional


@dataclass
class FootballTeamProfile:

    team_id: str
    team_name: str

    matches: int = 0

    wins: int = 0
    draws: int = 0
    losses: int = 0

    goals_for: int = 0
    goals_against: int = 0

    home_matches: int = 0
    home_wins: int = 0
    home_draws: int = 0
    home_losses: int = 0

    away_matches: int = 0
    away_wins: int = 0
    away_draws: int = 0
    away_losses: int = 0

    corners_for: float = 0.0
    corners_against: float = 0.0

    yellow_cards: float = 0.0
    red_cards: float = 0.0

    xg_for: float = 0.0
    xg_against: float = 0.0

    clean_sheets: int = 0
    btts_matches: int = 0

    @property
    def win_rate(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.wins / self.matches

    @property
    def draw_rate(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.draws / self.matches

    @property
    def loss_rate(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.losses / self.matches

    @property
    def goals_for_per_match(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.goals_for / self.matches

    @property
    def goals_against_per_match(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.goals_against / self.matches

    @property
    def goal_difference(self) -> int:

        return self.goals_for - self.goals_against

    @property
    def clean_sheet_rate(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.clean_sheets / self.matches

    @property
    def btts_rate(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.btts_matches / self.matches

    @property
    def average_corners_for(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.corners_for / self.matches

    @property
    def average_corners_against(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.corners_against / self.matches

    @property
    def average_yellow_cards(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.yellow_cards / self.matches

    @property
    def average_red_cards(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.red_cards / self.matches

    @property
    def average_xg_for(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.xg_for / self.matches

    @property
    def average_xg_against(self) -> Optional[float]:

        if self.matches == 0:
            return None

        return self.xg_against / self.matches

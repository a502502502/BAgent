import math
from typing import Optional

from models.contribution import Contribution
from models.football_profile import FootballTeamProfile


class FootballTeamStrengthFactor:

    PRIOR_WIN_RATE = 0.5
    PRIOR_WEIGHT = 5.0

    MIN_MATCHES_FOR_FULL_CONFIDENCE = 20

    def evaluate(
        self,
        home_profile: Optional[FootballTeamProfile],
        away_profile: Optional[FootballTeamProfile],
    ) -> Optional[Contribution]:

        if home_profile is None or away_profile is None:
            return None

        if (
            home_profile.matches <= 0
            or away_profile.matches <= 0
        ):
            return None

        home_rate = self._smoothed_win_rate(
            home_profile
        )

        away_rate = self._smoothed_win_rate(
            away_profile
        )

        difference = (
            home_rate
            - away_rate
        )

        value = math.tanh(
            difference * 3.0
        )

        confidence = self._confidence(
            home_profile,
            away_profile,
        )

        return Contribution(
            factor="TeamStrength",
            value=value,
            confidence=confidence,
            explanation=(
                "Historical team strength "
                "comparison using smoothed "
                "win rates."
            ),
            details={
                "home_team": home_profile.team_name,
                "away_team": away_profile.team_name,
                "home_matches": home_profile.matches,
                "away_matches": away_profile.matches,
                "home_smoothed_win_rate": home_rate,
                "away_smoothed_win_rate": away_rate,
                "difference": difference,
                "prior_win_rate": (
                    self.PRIOR_WIN_RATE
                ),
                "prior_weight": (
                    self.PRIOR_WEIGHT
                ),
            },
        )

    def _smoothed_win_rate(
        self,
        profile: FootballTeamProfile,
    ) -> float:

        return (
            profile.wins
            + (
                self.PRIOR_WEIGHT
                * self.PRIOR_WIN_RATE
            )
        ) / (
            profile.matches
            + self.PRIOR_WEIGHT
        )

    def _confidence(
        self,
        home_profile: FootballTeamProfile,
        away_profile: FootballTeamProfile,
    ) -> float:

        home_confidence = min(
            1.0,
            home_profile.matches
            / self.MIN_MATCHES_FOR_FULL_CONFIDENCE,
        )

        away_confidence = min(
            1.0,
            away_profile.matches
            / self.MIN_MATCHES_FOR_FULL_CONFIDENCE,
        )

        return (
            home_confidence
            + away_confidence
        ) / 2.0

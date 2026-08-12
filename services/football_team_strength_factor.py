import math
from typing import Optional

from models.contribution import Contribution
from models.football_profile import FootballTeamProfile


class FootballTeamStrengthFactor:

    PRIOR_WIN_RATE = 0.5
    PRIOR_WEIGHT = 5.0

    MIN_MATCHES_FOR_FULL_CONFIDENCE = 20

    WIN_RATE_WEIGHT = 3.0
    GOAL_DIFFERENCE_WEIGHT = 0.20

    # Neutral goal environment used ONLY when a team
    # has no historical profile.
    #
    # This does not represent historical data for that team.
    # It is simply a neutral prior.
    NEUTRAL_GOALS_FOR = 1.0
    NEUTRAL_GOALS_AGAINST = 1.0

    def evaluate(
        self,
        home_profile: Optional[FootballTeamProfile],
        away_profile: Optional[FootballTeamProfile],
    ) -> Optional[Contribution]:

        # --------------------------------------------------
        # We no longer abort when one team has no history.
        #
        # A missing profile receives a neutral prior:
        #
        #   win rate      = 0.50
        #   goal strength = 0.00
        #
        # This is especially important for newly promoted
        # teams or teams absent from the historical dataset.
        # --------------------------------------------------

        home_has_history = (
            home_profile is not None
            and home_profile.matches > 0
        )

        away_has_history = (
            away_profile is not None
            and away_profile.matches > 0
        )

        # If neither team has any history, this factor has
        # no information whatsoever.
        if (
            not home_has_history
            and not away_has_history
        ):
            return None

        # --------------------------------------------------
        # WIN RATE
        # --------------------------------------------------

        if home_has_history:

            home_rate = (
                self._smoothed_win_rate(
                    home_profile
                )
            )

        else:

            home_rate = (
                self.PRIOR_WIN_RATE
            )

        if away_has_history:

            away_rate = (
                self._smoothed_win_rate(
                    away_profile
                )
            )

        else:

            away_rate = (
                self.PRIOR_WIN_RATE
            )

        win_difference = (
            home_rate
            - away_rate
        )

        # --------------------------------------------------
        # GOAL STRENGTH
        # --------------------------------------------------

        if home_has_history:

            home_goal_rate = (
                home_profile.goals_for_per_match
                if (
                    home_profile.goals_for_per_match
                    is not None
                )
                else self.NEUTRAL_GOALS_FOR
            )

            home_conceded_rate = (
                home_profile.goals_against_per_match
                if (
                    home_profile.goals_against_per_match
                    is not None
                )
                else self.NEUTRAL_GOALS_AGAINST
            )

        else:

            home_goal_rate = (
                self.NEUTRAL_GOALS_FOR
            )

            home_conceded_rate = (
                self.NEUTRAL_GOALS_AGAINST
            )

        if away_has_history:

            away_goal_rate = (
                away_profile.goals_for_per_match
                if (
                    away_profile.goals_for_per_match
                    is not None
                )
                else self.NEUTRAL_GOALS_FOR
            )

            away_conceded_rate = (
                away_profile.goals_against_per_match
                if (
                    away_profile.goals_against_per_match
                    is not None
                )
                else self.NEUTRAL_GOALS_AGAINST
            )

        else:

            away_goal_rate = (
                self.NEUTRAL_GOALS_FOR
            )

            away_conceded_rate = (
                self.NEUTRAL_GOALS_AGAINST
            )

        home_goal_strength = (
            home_goal_rate
            - home_conceded_rate
        )

        away_goal_strength = (
            away_goal_rate
            - away_conceded_rate
        )

        goal_difference = (
            home_goal_strength
            - away_goal_strength
        )

        # --------------------------------------------------
        # COMBINED STRENGTH
        # --------------------------------------------------

        raw_strength = (
            self.WIN_RATE_WEIGHT
            * win_difference
            + self.GOAL_DIFFERENCE_WEIGHT
            * goal_difference
        )

        value = math.tanh(
            raw_strength
        )

        # --------------------------------------------------
        # CONFIDENCE
        #
        # Missing team = 0 confidence.
        # Existing team = confidence based on sample size.
        # --------------------------------------------------

        confidence = self._confidence(
            home_profile
            if home_has_history
            else None,
            away_profile
            if away_has_history
            else None,
        )

        home_team_name = (
            home_profile.team_name
            if home_has_history
            else "UNKNOWN"
        )

        away_team_name = (
            away_profile.team_name
            if away_has_history
            else "UNKNOWN"
        )

        home_matches = (
            home_profile.matches
            if home_has_history
            else 0
        )

        away_matches = (
            away_profile.matches
            if away_has_history
            else 0
        )

        # --------------------------------------------------
        # CONTRIBUTION
        # --------------------------------------------------

        return Contribution(
            factor="TeamStrength",
            value=value,
            confidence=confidence,
            explanation=(
                "Historical team strength comparison "
                "using smoothed win rates and goal "
                "strength. Missing team history uses "
                "a neutral prior."
            ),
            details={
                "home_team": home_team_name,
                "away_team": away_team_name,

                "home_matches": home_matches,
                "away_matches": away_matches,

                "home_has_history": (
                    home_has_history
                ),
                "away_has_history": (
                    away_has_history
                ),

                "home_smoothed_win_rate": (
                    home_rate
                ),
                "away_smoothed_win_rate": (
                    away_rate
                ),

                "difference": (
                    win_difference
                ),

                "home_goal_rate": (
                    home_goal_rate
                ),
                "away_goal_rate": (
                    away_goal_rate
                ),

                "home_conceded_rate": (
                    home_conceded_rate
                ),
                "away_conceded_rate": (
                    away_conceded_rate
                ),

                "home_goal_strength": (
                    home_goal_strength
                ),
                "away_goal_strength": (
                    away_goal_strength
                ),

                "goal_difference": (
                    goal_difference
                ),

                "raw_strength": (
                    raw_strength
                ),

                "win_rate_weight": (
                    self.WIN_RATE_WEIGHT
                ),

                "goal_difference_weight": (
                    self.GOAL_DIFFERENCE_WEIGHT
                ),

                "prior_win_rate": (
                    self.PRIOR_WIN_RATE
                ),

                "prior_weight": (
                    self.PRIOR_WEIGHT
                ),

                "missing_profile_policy": (
                    "neutral_prior"
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
        home_profile: Optional[
            FootballTeamProfile
        ],
        away_profile: Optional[
            FootballTeamProfile
        ],
    ) -> float:

        if home_profile is None:
            home_confidence = 0.0
        else:
            home_confidence = min(
                1.0,
                home_profile.matches
                / self.MIN_MATCHES_FOR_FULL_CONFIDENCE,
            )

        if away_profile is None:
            away_confidence = 0.0
        else:
            away_confidence = min(
                1.0,
                away_profile.matches
                / self.MIN_MATCHES_FOR_FULL_CONFIDENCE,
            )

        return (
            home_confidence
            + away_confidence
        ) / 2.0

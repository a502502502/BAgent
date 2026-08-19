from application.factors.factor import Factor

from domain.models.contribution import Contribution


class SurfaceFactor(Factor):

    PRIOR_WIN_RATE = 0.5

    # Peso del prior neutro.
    #
    # Con 5 match:
    #   il dato storico inizia a contare,
    #   ma resta ancora prudente.
    #
    # Con molti match:
    #   il dato osservato domina progressivamente.
    PRIOR_WEIGHT = 5.0

    def _smoothed_rate(
        self,
        wins: int,
        matches: int,
    ) -> float:

        if matches <= 0:
            return self.PRIOR_WIN_RATE

        return (
            wins
            + (
                self.PRIOR_WEIGHT
                * self.PRIOR_WIN_RATE
            )
        ) / (
            matches
            + self.PRIOR_WEIGHT
        )

    def evaluate(self, context):

        surface = context.match.court_name

        if not surface:
            return None

        surface_key = (
            f"SURFACE_WIN_RATE:{surface}"
        )

        home_knowledge = (
            context.subject_profile.get(
                surface_key
            )
        )

        away_knowledge = (
            context.opponent_profile.get(
                surface_key
            )
        )

        home_matches = 0
        home_wins = 0

        away_matches = 0
        away_wins = 0

        if home_knowledge is not None:

            metadata = (
                home_knowledge.metadata
                or {}
            )

            home_matches = int(
                metadata.get(
                    "matches",
                    0
                )
            )

            home_wins = int(
                metadata.get(
                    "wins",
                    0
                )
            )

        if away_knowledge is not None:

            metadata = (
                away_knowledge.metadata
                or {}
            )

            away_matches = int(
                metadata.get(
                    "matches",
                    0
                )
            )

            away_wins = int(
                metadata.get(
                    "wins",
                    0
                )
            )

        if (
            home_matches == 0
            and away_matches == 0
        ):
            return None

        home_rate = self._smoothed_rate(
            wins=home_wins,
            matches=home_matches,
        )

        away_rate = self._smoothed_rate(
            wins=away_wins,
            matches=away_matches,
        )

        difference = (
            home_rate -
            away_rate
        )

        total_matches = (
            home_matches +
            away_matches
        )

        confidence = min(
            1.0,
            total_matches / 20.0
        )

        return Contribution(
            factor="Surface",
            value=difference,
            confidence=confidence,
            explanation=(
                "Historical surface performance "
                "comparison with Bayesian-style "
                "smoothing toward a neutral prior."
            ),
            details={
                "surface": surface,

                "home_win_rate": home_rate,
                "away_win_rate": away_rate,

                "home_raw_wins": home_wins,
                "home_raw_matches": home_matches,

                "away_raw_wins": away_wins,
                "away_raw_matches": away_matches,

                "difference": difference,

                "confidence": confidence,

                "prior_win_rate": (
                    self.PRIOR_WIN_RATE
                ),

                "prior_weight": (
                    self.PRIOR_WEIGHT
                ),
            },
        )
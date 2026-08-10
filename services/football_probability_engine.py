import math

from models.football_probability import (
    FootballProbability,
)


class FootballProbabilityEngine:

    DRAW_BASE = 0.27

    def calculate(
        self,
        rating: float,
    ) -> FootballProbability:

        strength = math.tanh(
            rating
        )

        draw = (
            self.DRAW_BASE
            * (
                1.0
                - 0.35 * abs(strength)
            )
        )

        remaining = 1.0 - draw

        home_share = (
            1.0 + strength
        ) / 2.0

        home = (
            remaining
            * home_share
        )

        away = (
            remaining
            - home
        )

        return FootballProbability(
            home=home,
            draw=draw,
            away=away,
        )

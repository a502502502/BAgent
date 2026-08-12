import math

from models.football_probability import (
    FootballProbability,
)


class FootballProbabilityEngine:

    DRAW_BASE = 0.27

    DRAW_BALANCE_BOOST = 0.07

    def calculate(
        self,
        rating: float,
        balance: float = 1.0,
    ) -> FootballProbability:

        strength = math.tanh(
            rating
        )

        balance = max(
            0.0,
            min(1.0, balance),
        )

        draw = (
            self.DRAW_BASE
            + (
                self.DRAW_BALANCE_BOOST
                * balance
            )
        )

        draw *= (
            1.0
            - 0.15 * abs(strength)
        )

        draw = max(
            0.0,
            min(0.95, draw),
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






from math import exp

from domain.models.rating import Rating
from domain.models.probability import Probability


class ProbabilityEngine:

    def calculate(
        self,
        rating: Rating
    ) -> Probability:

        home = 1 / (
            1 + exp(-rating.value)
        )

        away = 1 - home

        return Probability(
            home=home,
            away=away
        )
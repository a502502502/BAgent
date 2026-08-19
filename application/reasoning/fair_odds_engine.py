from domain.models.fair_odds import FairOdds
from domain.models.probability import Probability


class FairOddsEngine:

    def calculate(
        self,
        probability: Probability
    ) -> FairOdds:

        return FairOdds(
            home=1 / probability.home,
            away=1 / probability.away
        )
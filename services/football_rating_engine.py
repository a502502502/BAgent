from typing import Iterable

from models.contribution import Contribution


class FootballRatingEngine:

    def calculate(
        self,
        contributions: Iterable[Contribution],
    ) -> float:

        contributions = list(contributions)

        if not contributions:
            return 0.0

        numerator = 0.0
        denominator = 0.0

        for contribution in contributions:

            if contribution.confidence <= 0:
                continue

            numerator += (
                contribution.value
                * contribution.confidence
            )

            denominator += contribution.confidence

        if denominator == 0:
            return 0.0

        return numerator / denominator

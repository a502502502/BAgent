from domain.models.contribution import Contribution
from domain.models.rating import Rating


class RatingEngine:

    def calculate(
        self,
        contributions: list[Contribution]
    ) -> Rating:

        if not contributions:
            return Rating(0.0)

        numerator = 0.0
        denominator = 0.0

        for contribution in contributions:

            numerator += (
                contribution.value *
                contribution.confidence
            )

            denominator += contribution.confidence

        if denominator == 0:
            return Rating(0.0)

        return Rating(
            numerator / denominator
        )
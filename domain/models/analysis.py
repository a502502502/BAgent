from dataclasses import dataclass

from domain.models.match import Match
from domain.models.rating import Rating
from domain.models.probability import Probability
from domain.models.fair_odds import FairOdds
from domain.models.contribution import Contribution


@dataclass(frozen=True)
class Analysis:

    match: Match

    rating: Rating

    probability: Probability

    fair_odds: FairOdds

    contributions: list[Contribution]

    def summary(self):

        lines = []

        lines.append("=" * 60)
        lines.append("BAgent Analysis")
        lines.append("=" * 60)
        lines.append("")

        lines.append(
            f"{self.match.home.name} vs {self.match.away.name}"
        )

        lines.append("")

        lines.append("CONTRIBUTIONS")
        lines.append("-" * 60)

        for contribution in self.contributions:

            lines.append(
                f"{contribution.factor:<20}"
                f"{contribution.value:+.3f}"
            )

        lines.append("")
        lines.append("-" * 60)

        lines.append(
            f"RATING               {self.rating.value:+.3f}"
        )

        lines.append("")

        lines.append(
            f"HOME PROBABILITY     {self.probability.home:.2%}"
        )

        lines.append(
            f"AWAY PROBABILITY     {self.probability.away:.2%}"
        )

        lines.append("")

        lines.append(
            f"HOME FAIR ODDS       {self.fair_odds.home:.2f}"
        )

        lines.append(
            f"AWAY FAIR ODDS       {self.fair_odds.away:.2f}"
        )

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
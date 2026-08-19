import math

from application.factors.factor import Factor

from domain.enums import KnowledgeKey
from domain.models.contribution import Contribution


class RankingFactor(Factor):

    def evaluate(self, context):

        home_rank = context.subject_profile.get(
            KnowledgeKey.ATP_RANK.value
        )

        away_rank = context.opponent_profile.get(
            KnowledgeKey.ATP_RANK.value
        )

        if home_rank is None or away_rank is None:
            return None

        difference = (
            away_rank.value -
            home_rank.value
        )

        value = math.tanh(
            difference / 30
        )

        return Contribution(
            factor="Ranking",
            value=value,
            confidence=1.0,
            explanation="ATP ranking comparison.",
            details={
                "home_rank": home_rank.value,
                "away_rank": away_rank.value,
                "difference": difference
            }
        )
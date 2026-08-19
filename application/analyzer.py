from domain.models.analysis import Analysis
from domain.models.analysis_context import AnalysisContext
from domain.models.profile import Profile

from application.reasoning.rating_engine import RatingEngine
from application.reasoning.probability_engine import ProbabilityEngine
from application.reasoning.fair_odds_engine import FairOddsEngine


class Analyzer:

    def __init__(self, knowledge_repository, registry):

        self.knowledge_repository = knowledge_repository
        self.registry = registry

        self.rating_engine = RatingEngine()
        self.probability_engine = ProbabilityEngine()
        self.fair_odds_engine = FairOddsEngine()

    def _build_profile(self, entity_id: str) -> Profile:

        profile = Profile(
            entity_type="PLAYER",
            entity_id=entity_id
        )

        for knowledge in self.knowledge_repository.find_by_entity(
            entity_id
        ):
            profile.add(knowledge)

        return profile

    def analyze(self, match):

        home = self._build_profile(match.home.id)

        away = self._build_profile(match.away.id)

        context = AnalysisContext(
            match=match,
            subject_profile=home,
            opponent_profile=away
        )

        contributions = []

        for factor in self.registry.all():

            contribution = factor.evaluate(context)

            if contribution is not None:
                contributions.append(contribution)

        rating = self.rating_engine.calculate(
            contributions
        )

        probability = self.probability_engine.calculate(
            rating
        )

        fair_odds = self.fair_odds_engine.calculate(
            probability
        )

        return Analysis(
            match=match,
            rating=rating,
            probability=probability,
            fair_odds=fair_odds,
            contributions=contributions
        )
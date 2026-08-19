from application.reasoning.probability_engine import ProbabilityEngine
from application.reasoning.fair_odds_engine import FairOddsEngine


class Analyzer:

    def __init__(

        self,

        profile_assembler,

        factors

    ):

        self.profile_assembler = profile_assembler

        self.factors = factors

        self.probability_engine = ProbabilityEngine()

        self.fair_odds_engine = FairOddsEngine()
        
        def analyze(self, match):

            home = self.profile_assembler.assemble(match.home.id)

            away = self.profile_assembler.assemble(match.away.id)

            context = AnalysisContext(

                match=match,

                subject_profile=home,

                opponent_profile=away

            )

            contributions = []

            for factor in self.factors:

                contribution = factor.evaluate(context)

                if contribution:

                    contributions.append(contribution)

            probability = self.probability_engine.calculate(

                contributions

            )

            fair_odds = self.fair_odds_engine.calculate(

                probability

            )

            return Analysis(

                match=match,

                probability=probability,

                fair_odds=fair_odds,

                contributions=contributions

            )
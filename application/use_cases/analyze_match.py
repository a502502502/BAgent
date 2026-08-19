import uuid

from domain.models.analysis_context import AnalysisContext
from domain.models.case import Case


class AnalyzeMatchUseCase:

    def __init__(

        self,

        profile_assembler,

        analysis_engine

    ):

        self.profile_assembler = profile_assembler

        self.analysis_engine = analysis_engine

    def execute(self, match):

        home_profile = self.profile_assembler.assemble(

            match.home.id

        )

        away_profile = self.profile_assembler.assemble(

            match.away.id

        )

        context = AnalysisContext(

            match=match,

            subject_profile=home_profile,

            opponent_profile=away_profile

        )

        evidences = self.analysis_engine.analyze(context)

        case = Case(

            id=str(uuid.uuid4()),

            context=context

        )

        for evidence in evidences:

            case.add_evidence(evidence)

        return case
from dataclasses import dataclass, field
from datetime import datetime

from domain.models.analysis_context import AnalysisContext
from domain.models.evidence import Evidence


@dataclass
class Case:

    id: str

    context: AnalysisContext

    evidences: list[Evidence] = field(default_factory=list)

    created_at: datetime = field(default_factory=datetime.utcnow)

    def add_evidence(self, evidence: Evidence):

        self.evidences.append(evidence)
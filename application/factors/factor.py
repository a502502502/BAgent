from abc import ABC, abstractmethod
from typing import Optional

from domain.models.analysis_context import AnalysisContext
from domain.models.contribution import Contribution


class Factor(ABC):

    @abstractmethod
    def evaluate(
        self,
        context: AnalysisContext
    ) -> Optional[Contribution]:
        """
        Restituisce il contributo del fattore oppure None
        se il fattore non è applicabile.
        """
        pass
from dataclasses import dataclass
from typing import Optional

from domain.models.match import Match
from domain.models.profile import Profile


@dataclass(frozen=True)
class AnalysisContext:

    match: Match

    subject_profile: Profile

    opponent_profile: Profile

    metadata: Optional[dict] = None
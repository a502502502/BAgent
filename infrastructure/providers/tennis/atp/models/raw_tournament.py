from dataclasses import dataclass, field
from typing import List

from providers.tennis.atp.models.raw_match import RawMatch


@dataclass
class RawTournament:

    tournament_id: str

    name: str

    city: str

    country: str

    matches: List[RawMatch] = field(default_factory=list)
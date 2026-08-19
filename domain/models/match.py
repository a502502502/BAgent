from dataclasses import dataclass
from typing import Optional

from domain.models.competition import Competition
from domain.models.competitor import Competitor


@dataclass(frozen=True)
class Match:

    id: str

    competition: Competition

    home: Competitor

    away: Competitor

    round_name: Optional[str] = None

    court_name: Optional[str] = None

    status: Optional[str] = None

    start_time: Optional[str] = None

    winner: Optional[str] = None
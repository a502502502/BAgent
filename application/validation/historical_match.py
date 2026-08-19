from dataclasses import dataclass
from typing import Optional

from domain.models.match import Match


@dataclass(frozen=True)
class HistoricalMatch:

    match: Match

    winner_id: str

    date: Optional[str] = None

    source: str = "TennisAbstract"
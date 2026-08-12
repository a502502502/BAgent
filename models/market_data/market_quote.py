from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MarketQuote:

    event_id: str
    home_team: str
    away_team: str

    bookmaker: str
    market: str
    selection: str

    odds: float
    point: Optional[float] = None

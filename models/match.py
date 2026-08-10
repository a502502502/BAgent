from dataclasses import dataclass
from typing import Optional


@dataclass
class Player:
    name: str
    ranking: Optional[int] = None
    elo: Optional[int] = None
    form: Optional[float] = None
    surface: Optional[str] = None


@dataclass
class Match:

    tournament: str
    player1: Player
    player2: Player

    start_time: str

    odd1: Optional[float] = None
    odd2: Optional[float] = None

    prediction: Optional[str] = None
    confidence: Optional[float] = None
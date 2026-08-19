from dataclasses import dataclass

from .competition import Competition
from .competitor import Competitor


@dataclass
class Event:
    id: str
    competition: Competition
    competitors: list
    start_time: str
    status: str = "scheduled"
from dataclasses import dataclass


@dataclass(frozen=True)
class Probability:

    home: float

    away: float
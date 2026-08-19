from dataclasses import dataclass


@dataclass(frozen=True)
class FairOdds:

    home: float

    away: float
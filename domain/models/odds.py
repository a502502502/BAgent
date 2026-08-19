from dataclasses import dataclass


@dataclass
class Odds:
    bookmaker: str
    market: str
    selection: str
    price: float
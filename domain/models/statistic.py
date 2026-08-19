from dataclasses import dataclass


@dataclass
class Statistic:
    name: str
    value: float
    source: str
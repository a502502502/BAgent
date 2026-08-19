from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Competitor:

    id: str

    name: str

    country: Optional[str] = None
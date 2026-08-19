from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Evidence:

    id: str

    match_id: str

    category: str

    source: str

    score: float

    confidence: float

    description: Optional[str] = None
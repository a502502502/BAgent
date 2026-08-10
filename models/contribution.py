from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class Contribution:

    factor: str
    value: float
    confidence: float
    explanation: str
    details: Dict[str, Any]

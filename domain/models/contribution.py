from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Contribution:
    """
    Contributo di un singolo fattore al modello probabilistico.

    value:
        -1.0 = massimo vantaggio Away
         0.0 = neutro
        +1.0 = massimo vantaggio Home
    """

    factor: str
    value: float
    confidence: float
    explanation: str
    details: dict[str, Any] = field(default_factory=dict)
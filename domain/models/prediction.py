from dataclasses import dataclass


@dataclass(frozen=True)
class Prediction:

    match_id: str

    winner_id: str

    confidence: float

    expected_value: float

    explanation: str
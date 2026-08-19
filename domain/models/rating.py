from dataclasses import dataclass


@dataclass(frozen=True)
class Rating:
    """
    Rating complessivo del modello.

    Valori positivi -> vantaggio Home
    Valori negativi -> vantaggio Away
    """

    value: float
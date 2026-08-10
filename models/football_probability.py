from dataclasses import dataclass


@dataclass(frozen=True)
class FootballProbability:

    home: float
    draw: float
    away: float

    def __post_init__(self):

        values = (
            self.home,
            self.draw,
            self.away,
        )

        if any(
            value < 0.0 or value > 1.0
            for value in values
        ):
            raise ValueError(
                "Probabilities must be between 0 and 1."
            )

        total = sum(values)

        if abs(total - 1.0) > 1e-9:
            raise ValueError(
                "Probabilities must sum to 1."
            )

    @property
    def most_likely(self) -> str:

        values = {
            "HOME": self.home,
            "DRAW": self.draw,
            "AWAY": self.away,
        }

        return max(
            values,
            key=values.get,
        )

from dataclasses import dataclass


@dataclass(frozen=True)
class FootballBacktestSummary:

    total_predictions: int
    accuracy: float
    average_log_loss: float
    average_brier_score: float

    home_predictions: int
    home_correct: int

    draw_predictions: int
    draw_correct: int

    away_predictions: int
    away_correct: int

    @property
    def home_accuracy(self) -> float:
        if self.home_predictions == 0:
            return 0.0

        return (
            self.home_correct
            / self.home_predictions
        )

    @property
    def draw_accuracy(self) -> float:
        if self.draw_predictions == 0:
            return 0.0

        return (
            self.draw_correct
            / self.draw_predictions
        )

    @property
    def away_accuracy(self) -> float:
        if self.away_predictions == 0:
            return 0.0

        return (
            self.away_correct
            / self.away_predictions
        )

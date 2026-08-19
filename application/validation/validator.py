from dataclasses import dataclass

from application.validation.metrics import Metrics


@dataclass(frozen=True)
class ValidationReport:

    matches: int
    accuracy: float
    log_loss: float
    brier_score: float

    def summary(self):

        return "\n".join([
            "",
            "=" * 50,
            "MODEL VALIDATION",
            "=" * 50,
            "",
            f"Matches       : {self.matches}",
            f"Accuracy      : {self.accuracy:.2%}",
            f"Log Loss      : {self.log_loss:.4f}",
            f"Brier Score   : {self.brier_score:.4f}",
            "",
            "=" * 50,
        ])


class Validator:

    def __init__(self, analyzer):

        self.analyzer = analyzer

    def evaluate(self, historical_matches):

        predictions = []

        for historical in historical_matches:

            analysis = self.analyzer.analyze(
                historical.match
            )

            if historical.winner_id == historical.match.home.id:

                actual = 1

            elif historical.winner_id == historical.match.away.id:

                actual = 0

            else:

                raise ValueError(
                    f"Winner {historical.winner_id} "
                    f"does not belong to match "
                    f"{historical.match.id}"
                )

            predictions.append(
                (
                    analysis.probability.home,
                    actual
                )
            )

        return ValidationReport(
            matches=len(predictions),
            accuracy=Metrics.accuracy(predictions),
            log_loss=Metrics.log_loss(predictions),
            brier_score=Metrics.brier_score(predictions)
        )
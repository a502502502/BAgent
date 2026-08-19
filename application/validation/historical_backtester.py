from typing import List

from application.validation.historical_match import (
    HistoricalMatch,
)

from application.validation.historical_analizer import (
    HistoricalAnalyzer,
)

from application.validation.validator import (
    ValidationReport,
)

from application.validation.metrics import (
    Metrics,
)


class HistoricalBacktester:

    def __init__(
        self,
        analyzer,
        ranking_history,
    ):

        self.historical_analyzer = HistoricalAnalyzer(
            analyzer=analyzer,
            ranking_history=ranking_history,
        )

    def run(
        self,
        historical_matches: List[HistoricalMatch],
    ) -> ValidationReport:

        predictions = []

        ordered_matches = sorted(
            historical_matches,
            key=lambda item: item.date or "",
        )

        print()
        print("=" * 60)
        print("HISTORICAL PREDICTIONS")
        print("=" * 60)

        for historical in ordered_matches:

            analysis = self.historical_analyzer.analyze(
                historical
            )

            match = historical.match

            home_probability = (
                analysis.probability.home
            )

            if historical.winner_id == match.home.id:

                actual = 1
                winner = match.home.name

            elif historical.winner_id == match.away.id:

                actual = 0
                winner = match.away.name

            else:

                raise ValueError(
                    f"Winner {historical.winner_id} "
                    f"does not belong to match "
                    f"{match.id}"
                )

            predicted_home = (
                home_probability >= 0.5
            )

            correct = (
                predicted_home
                and actual == 1
            ) or (
                not predicted_home
                and actual == 0
            )

            print(
                f"{historical.date} | "
                f"{match.competition.name} | "
                f"{match.home.name} vs "
                f"{match.away.name} | "
                f"P(home)={home_probability:.4f} | "
                f"winner={winner} | "
                f"{'OK' if correct else 'ERROR'}"
            )

            predictions.append(
                (
                    home_probability,
                    actual,
                )
            )

        report = ValidationReport(
            matches=len(predictions),
            accuracy=Metrics.accuracy(
                predictions
            ),
            log_loss=Metrics.log_loss(
                predictions
            ),
            brier_score=Metrics.brier_score(
                predictions
            ),
        )

        print()
        print("=" * 60)
        print("BACKTEST SUMMARY")
        print("=" * 60)

        print(
            f"Matches: {report.matches}"
        )

        print(
            f"Accuracy: {report.accuracy:.4f}"
        )

        print(
            f"Log Loss: {report.log_loss:.4f}"
        )

        print(
            f"Brier Score: {report.brier_score:.4f}"
        )

        return report
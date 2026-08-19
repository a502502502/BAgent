from application.validation.historical_knowledge import (
    HistoricalKnowledge,
)

from infrastructure.persistence.knowledge_repository import (
    KnowledgeRepository,
)


class HistoricalAnalyzer:

    def __init__(
        self,
        analyzer,
        ranking_history,
    ):
        self.analyzer = analyzer
        self.ranking_history = ranking_history

    def analyze(
        self,
        historical_match,
        previous_matches=None,
    ):

        match = historical_match.match

        repository = KnowledgeRepository()

        historical_knowledge = HistoricalKnowledge(
            self.ranking_history
        )

        historical_knowledge.populate(
            repository=repository,
            player_ids=[
                match.home.id,
                match.away.id,
            ],
            date=historical_match.date,
        )

        historical_knowledge.populate_surface(
            repository=repository,
            player_ids=[
                match.home.id,
                match.away.id,
            ],
            surface=match.court_name,
            previous_matches=previous_matches or [],
        )

        self.analyzer.knowledge_repository = repository

        analysis = self.analyzer.analyze(
            match
        )

        surface_applicable = any(
            contribution.factor == "Surface"
            for contribution in analysis.contributions
        )

        if surface_applicable:

            print(
                f"SURFACE USED | "
                f"{historical_match.date} | "
                f"{match.home.name} vs "
                f"{match.away.name}"
            )

            for contribution in analysis.contributions:

                print(
                    f"  FACTOR={contribution.factor} "
                    f"value={contribution.value:.6f} "
                    f"confidence={contribution.confidence:.6f}"
                )

            print(
                f"  RATING={analysis.rating.value:.6f} "
                f"P_HOME={analysis.probability.home:.6f}"
            )

        return analysis
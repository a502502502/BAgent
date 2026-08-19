from datetime import datetime, timedelta

from application.validation.ranking_history import RankingHistory

from application.validation.knowledge_factory import (
    HistoricalKnowledgeFactory,
)

from application.validation.player_mapping import (
    PlayerMapping,
)

from infrastructure.providers.tennis.atp.ranking_provider import (
    ATPRankingProvider,
)

from domain.models.knowledge import Knowledge


class HistoricalKnowledge:

    def __init__(
        self,
        ranking_history: RankingHistory
    ):
        self.ranking_history = ranking_history
        self.factory = HistoricalKnowledgeFactory()
        self.ranking_provider = ATPRankingProvider()

    def _parse_date(
        self,
        date: str
    ):

        formats = [
            "%Y-%m-%d",
            "%d-%b-%Y",
        ]

        for date_format in formats:

            try:

                return datetime.strptime(
                    date,
                    date_format
                ).date()

            except ValueError:
                continue

        raise ValueError(
            f"Unsupported historical date format: "
            f"{date}"
        )

    def _previous_ranking_week(
        self,
        date: str
    ) -> str:

        match_date = self._parse_date(
            date
        )

        days_since_monday = (
            match_date.weekday()
        )

        if days_since_monday == 0:
            days_back = 7
        else:
            days_back = days_since_monday

        ranking_date = (
            match_date -
            timedelta(days=days_back)
        )

        return ranking_date.isoformat()

    def populate(
        self,
        repository,
        player_ids,
        date
    ):

        if not date:
            return

        ranking_date = (
            self._previous_ranking_week(date)
        )

        rankings = (
            self.ranking_provider.fetch_week(
                ranking_date
            )
        )

        mapping = PlayerMapping(
            rankings
        )

        for player_id in player_ids:

            ranking = mapping.find(
                player_id
            )

            if ranking is None:
                continue

            knowledge = self.factory.ranking(
                player_id=player_id,
                ranking=ranking,
                date=ranking_date
            )

            repository.save(
                knowledge
            )

    def populate_surface(
        self,
        repository,
        player_ids,
        surface,
        previous_matches,
    ):

        if not surface:
            return

        if not previous_matches:
            return

        for player_id in player_ids:

            wins = 0
            matches = 0

            for historical in previous_matches:

                match = historical.match

                if match.court_name != surface:
                    continue

                if player_id not in [
                    match.home.id,
                    match.away.id,
                ]:
                    continue

                matches += 1

                if historical.winner_id == player_id:
                    wins += 1

            if matches == 0:
                continue

            win_rate = (
                wins / matches
            )

            knowledge = Knowledge(
                id=(
                    f"HIST-SURFACE-"
                    f"{player_id}-"
                    f"{surface}"
                ),
                entity_type="PLAYER",
                entity_id=player_id,
                key=(
                    f"SURFACE_WIN_RATE:"
                    f"{surface}"
                ),
                value=win_rate,
                value_type="FLOAT",
                source="TENNIS_ABSTRACT_HISTORICAL",
                confidence=1.0,
                collected_at=datetime.utcnow(),
                metadata={
                    "surface": surface,
                    "matches": matches,
                    "wins": wins,
                    "losses": (
                        matches - wins
                    ),
                    "win_rate": win_rate,
                },
            )

            repository.save(
                knowledge
            )
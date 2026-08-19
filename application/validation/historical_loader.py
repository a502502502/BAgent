import csv
from datetime import datetime
from typing import List

from application.validation.historical_match import HistoricalMatch

from domain.models.match import Match
from domain.models.competition import Competition
from domain.models.competitor import Competitor


class HistoricalMatchLoader:

    def load(self, filename: str) -> List[HistoricalMatch]:

        matches = []

        with open(
            filename,
            "r",
            encoding="utf-8",
            newline=""
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                player_a = row["player_a"]
                player_b = row["player_b"]
                winner = row["winner"]

                match_id = row.get(
                    "match_id",
                    f"{row.get('date', '')}-{player_a}-{player_b}"
                )

                competition = Competition(
                    id=row.get("tournament", "UNKNOWN"),
                    name=row.get("tournament", "Unknown")
                )

                match = Match(
                    id=match_id,

                    competition=competition,

                    home=Competitor(
                        id=player_a,
                        name=player_a
                    ),

                    away=Competitor(
                        id=player_b,
                        name=player_b
                    ),

                    round_name=row.get("round"),

                    court_name=row.get("surface"),

                    status="Completed",

                    start_time=row.get("date"),

                    winner=winner
                )

                matches.append(
                    HistoricalMatch(
                        match=match,
                        winner_id=winner,
                        date=row.get("date"),
                    )
                )

        return matches
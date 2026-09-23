import csv
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

                home_name = row["home_team"]
                away_name = row["away_team"]
                winner = row.get("winner")
                league = row.get("league", "UNKNOWN")

                match_id = row.get(
                    "match_id",
                    f"{row.get('date', '')}-{home_name}-{away_name}"
                )

                competition = Competition(
                    id=league,
                    name=league
                )

                match = Match(
                    id=match_id,

                    competition=competition,

                    home=Competitor(
                        id=home_name,
                        name=home_name
                    ),

                    away=Competitor(
                        id=away_name,
                        name=away_name
                    ),

                    round_name=row.get("round"),

                    venue=row.get("venue"),

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
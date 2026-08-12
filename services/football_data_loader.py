from datetime import datetime
from pathlib import Path
from typing import Union

import pandas as pd

from models.football import (
    FootballMatch,
    FootballTeam,
)

from models.football_odds import (
    FootballMatchOdds,
)

from models.football_statistics import (
    FootballMatchStatistics,
)

from models.historical_match import (
    HistoricalFootballMatch,
)


class FootballDataLoader:

    def load(
        self,
        path: Union[str, Path],
    ) -> list[HistoricalFootballMatch]:

        path = Path(path)

        dataframe = pd.read_csv(path)

        matches = []

        for index, row in dataframe.iterrows():

            date = self._parse_date(
                row["Date"],
                row["Time"],
            )

            home_name = str(row["HomeTeam"])
            away_name = str(row["AwayTeam"])

            home_team = FootballTeam(
                id=home_name,
                name=home_name,
            )

            away_team = FootballTeam(
                id=away_name,
                name=away_name,
            )

            match = FootballMatch(
                id=f"{path.stem}-{index + 1}",
                competition=self._competition(
                    row["Div"]
                ),
                season=self._season(path),
                home=home_team,
                away=away_team,
                start_time=date.isoformat(),
                home_goals=self._int_or_none(
                    row["FTHG"]
                ),
                away_goals=self._int_or_none(
                    row["FTAG"]
                ),
                status="Completed",
                home_corners=self._int_or_none(row["HC"]),
                away_corners=self._int_or_none(row["AC"]),
                home_yellow_cards=self._int_or_none(row["HY"]),
                away_yellow_cards=self._int_or_none(row["AY"]),
                home_red_cards=self._int_or_none(row["HR"]),
                away_red_cards=self._int_or_none(row["AR"]),
            )

            statistics = FootballMatchStatistics(
                home_shots=self._int_or_none(row["HS"]),
                away_shots=self._int_or_none(row["AS"]),
                home_shots_on_target=self._int_or_none(row["HST"]),
                away_shots_on_target=self._int_or_none(row["AST"]),
                home_fouls=self._int_or_none(row["HF"]),
                away_fouls=self._int_or_none(row["AF"]),
                home_corners=self._int_or_none(row["HC"]),
                away_corners=self._int_or_none(row["AC"]),
                home_yellow_cards=self._int_or_none(row["HY"]),
                away_yellow_cards=self._int_or_none(row["AY"]),
                home_red_cards=self._int_or_none(row["HR"]),
                away_red_cards=self._int_or_none(row["AR"]),
                home_half_time_goals=self._int_or_none(row["HTHG"]),
                away_half_time_goals=self._int_or_none(row["HTAG"]),
            )

            odds = FootballMatchOdds(
                home=self._float_or_none(row["B365H"]),
                draw=self._float_or_none(row["B365D"]),
                away=self._float_or_none(row["B365A"]),
                over_2_5=self._float_or_none(
                    row["B365>2.5"]
                ),
                under_2_5=self._float_or_none(
                    row["B365<2.5"]
                ),
            )

            matches.append(
                HistoricalFootballMatch(
                    match=match,
                    date=date,
                    statistics=statistics,
                    odds=odds,
                    winner=match.result,
                )
            )

        matches.sort(
            key=lambda match: match.date
        )

        return matches

    @staticmethod
    def _parse_date(
        date_value,
        time_value,
    ) -> datetime:

        date_text = str(date_value).strip()
        time_text = str(time_value).strip()

        return datetime.strptime(
            f"{date_text} {time_text}",
            "%d/%m/%Y %H:%M",
        )

    @staticmethod
    def _int_or_none(value):

        if pd.isna(value):
            return None

        return int(value)

    @staticmethod
    def _float_or_none(value):

        if pd.isna(value):
            return None

        return float(value)

    @staticmethod
    def _competition(value) -> str:

        divisions = {
            "E0": "Premier League",
        }

        value = str(value).strip()

        return divisions.get(
            value,
            value,
        )

    @staticmethod
    def _season(path: Path) -> str:

        if path.stem == "E0_2025_2026":
            return "2025/26"

        return path.stem

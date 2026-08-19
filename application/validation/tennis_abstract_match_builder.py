from typing import List

from application.validation.historical_match import (
    HistoricalMatch,
)

from domain.models.competition import Competition
from domain.models.competitor import Competitor
from domain.models.match import Match


class TennisAbstractMatchBuilder:

    def build(
        self,
        results,
        player_id: str,
        player_name: str,
    ) -> List[HistoricalMatch]:

        matches = []

        player_last_name = (
            self._clean_name(player_name)
            .strip()
            .split()[-1]
            .lower()
        )

        for index, result in enumerate(results):

            matchup = result.get(
                "",
                ""
            )

            if not matchup:
                continue

            if " d. " not in matchup:
                continue

            left, right = matchup.split(
                " d. ",
                1,
            )

            winner_name_raw = left.strip()
            loser_name_raw = right.strip()

            winner_name = self._clean_name(
                winner_name_raw
            )

            loser_name = self._clean_name(
                loser_name_raw
            )

            winner_id = self._normalise_id(
                winner_name
            )

            loser_id = self._normalise_id(
                loser_name
            )

            # -------------------------------------------------
            # Il giocatore richiesto è il vincitore
            # -------------------------------------------------

            if (
                player_last_name
                in winner_name.lower()
            ):

                home_id = player_id
                home_name = player_name

                away_id = loser_id
                away_name = loser_name

                winner_id = player_id

            # -------------------------------------------------
            # Il giocatore richiesto è il perdente
            # -------------------------------------------------

            elif (
                player_last_name
                in loser_name.lower()
            ):

                home_id = player_id
                home_name = player_name

                away_id = winner_id
                away_name = winner_name

                winner_id = winner_id

            else:

                continue

            match_id = (
                f"TA-{player_id}-"
                f"{result.get('Date', '')}-"
                f"{index}"
            )

            tournament = result.get(
                "Tournament",
                "Unknown",
            )

            match = Match(
                id=match_id,

                competition=Competition(
                    id=tournament,
                    name=tournament,
                ),

                home=Competitor(
                    id=home_id,
                    name=home_name,
                ),

                away=Competitor(
                    id=away_id,
                    name=away_name,
                ),

                round_name=result.get(
                    "Rd"
                ),

                court_name=result.get(
                    "Surface"
                ),

                status="Completed",

                start_time=result.get(
                    "Date"
                ),

                winner=winner_id,
            )

            matches.append(
                HistoricalMatch(
                    match=match,
                    winner_id=winner_id,
                    date=result.get(
                        "Date"
                    ),
                )
            )

        return matches

    @staticmethod
    def _clean_name(
        name: str,
    ) -> str:

        value = name or ""

        # -------------------------------------------------
        # Rimuove ranking / qualificazioni / wildcard
        # -------------------------------------------------

        tokens = [
            "(1)", "(2)", "(3)", "(4)",
            "(5)", "(6)", "(7)", "(8)",
            "(9)", "(10)", "(11)", "(12)",
            "(13)", "(14)", "(15)", "(16)",
            "(17)", "(18)", "(19)", "(20)",
            "(21)", "(22)", "(23)", "(24)",
            "(25)", "(26)", "(27)", "(28)",
            "(29)", "(30)", "(31)", "(32)",
            "(Q)",
            "(WC)",
            "(LL)",
            "(SR)",
        ]

        for token in tokens:

            value = value.replace(
                token,
                "",
            )

        # -------------------------------------------------
        # Rimuove il paese:
        #
        # Carlos Alcaraz [ESP]
        # ->
        # Carlos Alcaraz
        # -------------------------------------------------

        if "[" in value:

            value = value.split(
                "[",
                1,
            )[0]

        return " ".join(
            value.strip().split()
        )

    @staticmethod
    def _normalise_id(
        name: str,
    ) -> str:

        value = (
            TennisAbstractMatchBuilder
            ._clean_name(name)
        )

        return (
            value
            .strip()
            .replace(" ", "")
        )
from bs4 import BeautifulSoup


class TennisAbstractPlayerParser:

    def parse(
        self,
        html: str,
    ):

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        return soup.find_all(
            "table"
        )

    def parse_results(
        self,
        html: str,
    ):

        soup = BeautifulSoup(
            html,
            "html.parser"
        )

        tables = soup.find_all(
            "table"
        )

        for table in tables:

            rows = table.find_all(
                "tr"
            )

            if not rows:
                continue

            headers = [
                cell.get_text(
                    " ",
                    strip=True
                )
                for cell in rows[0].find_all(
                    ["th", "td"]
                )
            ]

            required = {
                "Date",
                "Tournament",
                "Surface",
                "Rd",
                "Rk",
                "vRk",
                "Score",
            }

            if not required.issubset(
                set(headers)
            ):
                continue

            results = []

            carried = {}

            for row in rows[1:]:

                cells = row.find_all(
                    ["td", "th"]
                )

                if not cells:
                    continue

                values = []
                column = 0

                for cell in cells:

                    while column in carried:

                        values.append(
                            carried[column][
                                "value"
                            ]
                        )

                        carried[column][
                            "remaining"
                        ] -= 1

                        if (
                            carried[column][
                                "remaining"
                            ] <= 0
                        ):

                            del carried[
                                column
                            ]

                        column += 1

                    value = cell.get_text(
                        " ",
                        strip=True
                    )

                    values.append(
                        value
                    )

                    rowspan = int(
                        cell.get(
                            "rowspan",
                            "1"
                        )
                    )

                    if rowspan > 1:

                        carried[column] = {
                            "value": value,
                            "remaining": (
                                rowspan - 1
                            ),
                        }

                    column += 1

                while column in carried:

                    values.append(
                        carried[column][
                            "value"
                        ]
                    )

                    carried[column][
                        "remaining"
                    ] -= 1

                    if (
                        carried[column][
                            "remaining"
                        ] <= 0
                    ):

                        del carried[
                            column
                        ]

                    column += 1

                if len(values) < len(
                    headers
                ):
                    continue

                result = {}

                for index, header in enumerate(
                    headers
                ):

                    if index >= len(
                        values
                    ):
                        break

                    result[header] = (
                        values[index]
                    )

                results.append(
                    result
                )

            if results:
                return results

        raise ValueError(
            "Tabella dei risultati "
            "non trovata."
        )

    def extract_match_info(
        self,
        result,
        player_name,
    ):

        matchup = result.get(
            "",
            ""
        )

        if not matchup:

            raise ValueError(
                "Matchup non trovato."
            )

        player_name = (
            player_name.lower()
        )

        if " d. " not in matchup:

            raise ValueError(
                "Formato matchup "
                f"sconosciuto: {matchup}"
            )

        left, right = matchup.split(
            " d. ",
            1
        )

        winner_text = left.strip()
        loser_text = right.strip()

        if (
            player_name
            in winner_text.lower()
        ):

            opponent = loser_text
            won = True

        elif (
            player_name
            in loser_text.lower()
        ):

            opponent = winner_text
            won = False

        else:

            raise ValueError(
                f"Giocatore {player_name} "
                f"non trovato in: "
                f"{matchup}"
            )

        return {
            "opponent": opponent,
            "won": won,
        }
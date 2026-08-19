from typing import Dict

import requests


class ATPRankingProvider:

    BASE_URL = (
        "https://atp-rankings.ishanjha.com"
    )

    def fetch_week(
        self,
        date: str
    ) -> Dict[str, int]:

        url = (
            f"{self.BASE_URL}/api/week/{date}"
        )

        response = requests.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        rankings = {}

        for item in data.get("rankings", []):

            name = item.get("name")
            rank = item.get("rank")

            if not name:
                continue

            if rank is None:
                continue

            try:
                rankings[name] = int(rank)

            except (
                TypeError,
                ValueError
            ):
                continue

        return rankings
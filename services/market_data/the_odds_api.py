import os
from typing import Any

from services.http_client import HttpClient


class TheOddsApi:

    BASE_URL = "https://api.the-odds-api.com/v4"

    def __init__(self):
        self.api_key = os.getenv("ODDS_API_KEY")

        if not self.api_key:
            raise RuntimeError(
                "ODDS_API_KEY non configurata"
            )

        self.http = HttpClient()

    def get_soccer_odds(
        self,
        sport: str = "soccer_epl",
        regions: str = "eu",
        markets: str = "h2h,totals",
        odds_format: str = "decimal",
    ) -> Any:

        url = (
            f"{self.BASE_URL}/sports/"
            f"{sport}/odds"
            f"?apiKey={self.api_key}"
            f"&regions={regions}"
            f"&markets={markets}"
            f"&oddsFormat={odds_format}"
        )

        return self.http.get_json(url)

    def close(self):
        self.http.close()

import requests

from scraper.base_scraper import BaseScraper


class TennisStats(BaseScraper):

    def __init__(self):

        super().__init__("TennisStats")

        self.session = requests.Session()

    def fetch_matches(self):

        print("Recupero partite da TennisStats...")

        return []
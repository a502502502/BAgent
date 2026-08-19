class ScraperManager:

    def __init__(self):

        self.scrapers = []

    def register(self, scraper):

        self.scrapers.append(scraper)

    def fetch_all(self):

        matches = []

        for scraper in self.scrapers:

            print(f"Avvio {scraper.name}")

            data = scraper.fetch_matches()

            matches.extend(data)

        return matches
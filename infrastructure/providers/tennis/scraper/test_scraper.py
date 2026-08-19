from pathlib import Path

from services.http_client import HttpClient
from services.logger import info, success


class TestScraper:

    def run(self):

        url = "https://www.atptour.com"

        info(f"Download: {url}")

        client = HttpClient()

        html = client.get(url)

        client.close()

        Path("output").mkdir(exist_ok=True)

        with open("output/atp_home.html", "w", encoding="utf-8") as f:
            f.write(html)

        success(f"Pagina salvata ({len(html)} caratteri)")
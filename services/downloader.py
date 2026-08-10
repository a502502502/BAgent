from pathlib import Path
from datetime import datetime

from services.http_client import HttpClient
from services.logger import info, success


class Downloader:

    def __init__(self):

        self.client = HttpClient()

        Path("data/cache").mkdir(parents=True, exist_ok=True)

    def download(self, url: str, filename: str):

        info(f"Download {url}")

        html = self.client.get(url)

        filepath = Path("data/cache") / filename

        filepath.write_text(html, encoding="utf-8")

        success(f"Salvato in {filepath}")

        return html

    def close(self):

        self.client.close()
import httpx

from config.settings import TIMEOUT
from config.settings import USER_AGENT


class HttpClient:

    def __init__(self):

        self.client = httpx.Client(
            timeout=TIMEOUT,
            follow_redirects=True,
            headers={
                "User-Agent": USER_AGENT
            }
        )

    def get(self, url: str):

        response = self.client.get(url)

        response.raise_for_status()

        return response.text

    def close(self):
        self.client.close()
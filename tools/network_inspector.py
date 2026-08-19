import json
from pathlib import Path

from core.browser.browser import Browser


URL = "https://www.atptour.com/en/scores/current"


class NetworkInspector:

    def __init__(self):

        self.requests = []

    def handle_response(self, response):

        url = response.url

        if "livematches" not in url.lower():
            return

        print("\n========================================")
        print("LIVE MATCHES API")
        print("========================================")
        print(f"Status : {response.status}")
        print(f"URL    : {url}")

        try:

            data = response.json()

            print(f"\nTipo risposta: {type(data).__name__}")

            if isinstance(data, dict):

                print("\nChiavi principali:")

                for key in data.keys():
                    print(f" - {key}")

            elif isinstance(data, list):

                print(f"\nLista con {len(data)} elementi")

            Path("storage/snapshots/atp").mkdir(
                parents=True,
                exist_ok=True
            )

            with open(
                "storage/snapshots/atp/livematches.json",
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    data,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

            print("\n✅ JSON salvato in:")
            print("storage/snapshots/atp/livematches.json")

        except Exception as ex:

            print("\n❌ Errore nella lettura del JSON")
            print(ex)

    def run(self):

        browser = Browser(debug=True)

        try:

            page = browser.page

            page.on("response", self.handle_response)

            browser.get(URL)

            print("\n========================================")
            print("Attendo le richieste di rete...")
            print("========================================")

        finally:

            browser.close()


if __name__ == "__main__":

    inspector = NetworkInspector()

    inspector.run()
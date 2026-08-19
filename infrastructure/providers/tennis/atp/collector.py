from core.browser.browser import Browser


class TennisAbstractCollector:

    BASE_URL = (
        "https://www.tennisabstract.com/cgi-bin/player.cgi?p="
    )

    def collect(self, player_slug: str) -> str:

        browser = Browser(debug=True)

        try:
            url = f"{self.BASE_URL}{player_slug}"

            print(f"\nApertura: {url}\n")

            html = browser.get(url)

            browser.save_html(
                "tennis_abstract_player.html"
            )

            browser.screenshot(
                "tennis_abstract_player.png"
            )

            print("✅ Snapshot HTML salvato")
            print("✅ Screenshot salvato")

            return html

        finally:
            browser.close()
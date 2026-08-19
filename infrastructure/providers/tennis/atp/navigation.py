from core.browser.browser import Browser


class ATPCollector:

    URL = "https://www.atptour.com/en/scores/current"

    def collect(self) -> str:

        browser = Browser(debug=True)

        try:

            html = browser.get(self.URL)

            browser.save_html("atp_current.html")

            browser.screenshot("atp_current.png")

            return html

        finally:

            browser.close()
from pathlib import Path

from playwright.sync_api import sync_playwright


class Browser:

    def __init__(self, debug=False):

        self.debug = debug

        self.playwright = (
            sync_playwright().start()
        )

        self.browser = (
            self.playwright.chromium.launch(
                headless=False,
                slow_mo=100
            )
        )

        self.page = self.browser.new_page(
            viewport={
                "width": 1400,
                "height": 900
            },
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36"
            )
        )

        self.page.set_default_timeout(
            60000
        )

    def get(
        self,
        url: str
    ):

        self.page.goto(
            url,
            wait_until="domcontentloaded"
        )

        return self.page.content()

    def click(
        self,
        selector: str
    ):

        self.page.click(
            selector
        )

    def wait(
        self,
        selector: str
    ):

        self.page.wait_for_selector(
            selector
        )

    def text(
        self,
        selector: str
    ):

        return self.page.locator(
            selector
        ).inner_text()

    def html(self):

        return self.page.content()

    def screenshot(
        self,
        filename: str
    ):

        path = Path(
            filename
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        self.page.screenshot(
            path=str(path)
        )

    def save_html(
        self,
        filename: str
    ):

        path = Path(
            filename
        )

        path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as f:

            f.write(
                self.page.content()
            )

    def close(self):

        try:

            if self.browser:

                self.browser.close()

        finally:

            if self.playwright:

                self.playwright.stop()
from pathlib import Path

from playwright.sync_api import sync_playwright


class Browser:

    def __init__(self):

        self.playwright = sync_playwright().start()

        self.browser = self.playwright.chromium.launch(
            headless=False
        )

        self.page = self.browser.new_page()

    def open(self, url):

        self.page.goto(url, wait_until="networkidle")

    def click(self, selector):

        self.page.click(selector)

    def wait(self, selector):

        self.page.wait_for_selector(selector)

    def text(self, selector):

        return self.page.locator(selector).inner_text()

    def html(self):

        return self.page.content()

    def screenshot(self, filename):

        Path("output").mkdir(exist_ok=True)

        self.page.screenshot(path=f"output/{filename}")

    def save_html(self, filename):

        Path("output").mkdir(exist_ok=True)

        with open(f"output/{filename}", "w", encoding="utf-8") as f:
            f.write(self.html())

    def close(self):

        self.browser.close()

        self.playwright.stop()
from core.browser.browser import Browser


URL = "https://www.atptour.com/en/scores/current"


def print_count(page, selector):

    try:
        count = page.locator(selector).count()
        print(f"{selector:<15} {count}")
    except Exception:
        print(f"{selector:<15} ERROR")


def main():

    browser = Browser(debug=True)

    try:

        browser.get(URL)

        page = browser.page

        print("\n========================================")
        print("PAGE")
        print("========================================\n")

        print(page.title())

        print("\n========================================")
        print("ELEMENT COUNT")
        print("========================================\n")

        selectors = [
            "article",
            "section",
            "table",
            "div",
            "span",
            "a",
            "button",
            "ul",
            "li",
            "img",
            "svg"
        ]

        for selector in selectors:
            print_count(page, selector)

        print("\n========================================")
        print("HEADINGS")
        print("========================================\n")

        for tag in ["h1", "h2", "h3"]:

            headings = page.locator(tag)

            print(f"\n{tag.upper()}")

            for i in range(min(headings.count(), 20)):
                text = headings.nth(i).inner_text().strip()

                if text:
                    print("-", text)

        print("\n========================================")
        print("LINKS")
        print("========================================\n")

        links = page.locator("a")

        for i in range(min(20, links.count())):

            text = links.nth(i).inner_text().strip()

            if text:
                print("-", text)

        browser.screenshot("page_inspector.png")

    finally:

        browser.close()


if __name__ == "__main__":
    main()
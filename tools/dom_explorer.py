from core.browser.browser import Browser


URL = "https://www.atptour.com/en/scores/current"


def main():

    browser = Browser(debug=True)

    try:

        page = browser.page

        browser.get(URL)

        print("\n============================")
        print("PAGE TITLE")
        print("============================")
        print(page.title())

        print("\n============================")
        print("H1")
        print("============================")

        try:
            print(page.locator("h1").first.inner_text())
        except Exception:
            print("Nessun H1 trovato.")

        print("\n============================")
        print("ALL TABLES")
        print("============================")

        tables = page.locator("table")

        print(f"Tabelle trovate: {tables.count()}")

        print("\n============================")
        print("ALL DIVS")
        print("============================")

        divs = page.locator("div")

        print(f"Div trovati: {divs.count()}")

        browser.screenshot("dom_explorer.png")
        browser.save_html("dom_explorer.html")

    finally:

        browser.close()


if __name__ == "__main__":
    main()
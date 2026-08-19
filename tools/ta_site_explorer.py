from core.browser.browser import Browser

browser = Browser(debug=True)

browser.get("https://www.tennisabstract.com/")

links = browser.page.locator("a").all()

print("\n" + "=" * 80)
print("LINKS")
print("=" * 80)

found = set()

for link in links:

    try:

        href = link.get_attribute("href")

        text = link.inner_text().strip()

        if not href:
            continue

        if href in found:
            continue

        found.add(href)

        print(f"{text:35} -> {href}")

    except Exception:
        pass

browser.close()
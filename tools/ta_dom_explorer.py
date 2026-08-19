from pathlib import Path

from bs4 import BeautifulSoup


html = Path(
    "providers/tennis/tennis_abstract/snapshots/player.html"
).read_text(
    encoding="utf-8"
)

soup = BeautifulSoup(html, "html.parser")

tables = soup.find_all("table")

print("\n" + "=" * 70)
print("TITLE")
print("=" * 70)

if soup.title:
    print(soup.title.get_text(strip=True))
else:
    print("Nessun titolo")

print("\n" + "=" * 70)
print("TABELLE TROVATE")
print("=" * 70)

print(len(tables))

for i, table in enumerate(tables):

    print()
    print("=" * 70)
    print(f"TABLE {i}")
    print("=" * 70)

    rows = table.find_all("tr")

    for row in rows[:10]:

        cells = row.find_all(["th", "td"])

        values = [
            c.get_text(" ", strip=True)
            for c in cells
        ]

        print(values)
from application.validation.historical_loader import (
    HistoricalMatchLoader
)


loader = HistoricalMatchLoader()

matches = loader.load(
    "data/historical/atp_matches.csv"
)

print()

print(
    f"Loaded matches: {len(matches)}"
)

for historical in matches:

    match = historical.match

    print(
        f"{match.home.name} vs "
        f"{match.away.name} -> "
        f"{historical.winner_id}"
    )

assert len(matches) == 3

assert (
    matches[0].winner_id ==
    "JannikSinner"
)

print()
print("HISTORICAL LOADER TEST PASSED")
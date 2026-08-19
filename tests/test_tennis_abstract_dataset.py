from application.validation.tennis_abstract_dataset import (
    TennisAbstractDataset,
)


PLAYERS = {
    "JannikSinner": "Sinner",
    "CarlosAlcaraz": "Alcaraz",
}


dataset = TennisAbstractDataset()

matches = dataset.collect(
    PLAYERS
)

assert matches

print()
print("=" * 60)
print("TENNIS ABSTRACT DATASET")
print("=" * 60)

print(
    f"Players: {len(PLAYERS)}"
)

print(
    f"Unique historical matches: {len(matches)}"
)

for historical in matches[:10]:

    match = historical.match

    print(
        f"{historical.date} | "
        f"{match.competition.name} | "
        f"{match.home.name} vs "
        f"{match.away.name} | "
        f"winner={historical.winner_id}"
    )

print()
print("DATASET TEST PASSED")
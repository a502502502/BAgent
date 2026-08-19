from application.validation.tennis_abstract_pipeline import (
    TennisAbstractPipeline,
)


pipeline = TennisAbstractPipeline()

matches = pipeline.load_player_matches(
    player_id="JannikSinner",
    player_name="Sinner",
)

assert matches
assert len(matches) > 0

print()
print("=" * 60)
print("TENNIS ABSTRACT PIPELINE V2")
print("=" * 60)

print(f"Historical matches: {len(matches)}")

for historical in matches[:5]:

    match = historical.match

    print(
        f"{historical.date} | "
        f"{match.competition.name} | "
        f"{match.home.name} vs "
        f"{match.away.name} | "
        f"winner={historical.winner_id}"
    )

print()
print("PIPELINE V2 PASSED")
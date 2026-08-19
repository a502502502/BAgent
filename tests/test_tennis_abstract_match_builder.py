from infrastructure.providers.tennis.tennis_abstract.collector import (
    TennisAbstractCollector
)

from infrastructure.providers.tennis.tennis_abstract.player_parser import (
    TennisAbstractPlayerParser
)

from application.validation.tennis_abstract_match_builder import (
    TennisAbstractMatchBuilder
)


collector = TennisAbstractCollector()

html = collector.collect(
    "JannikSinner"
)


parser = TennisAbstractPlayerParser()

results = parser.parse_results(
    html
)


builder = TennisAbstractMatchBuilder()

matches = builder.build(
    results=results,
    player_id="JannikSinner",
    player_name="Sinner"
)


print()
print("=" * 60)
print("TENNIS ABSTRACT → HISTORICAL MATCH")
print("=" * 60)

print(
    f"Matches built: {len(matches)}"
)

for historical in matches[:10]:

    match = historical.match

    print(
        f"{match.start_time} | "
        f"{match.competition.name} | "
        f"{match.home.name} vs "
        f"{match.away.name} | "
        f"winner={historical.winner_id}"
    )


assert len(matches) > 0

assert all(
    historical.winner_id
    for historical in matches
)

print()
print("MATCH BUILDER TEST PASSED")
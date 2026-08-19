from infrastructure.providers.tennis.tennis_abstract.collector import (
    TennisAbstractCollector
)

from infrastructure.providers.tennis.tennis_abstract.player_parser import (
    TennisAbstractPlayerParser
)


collector = TennisAbstractCollector()

html = collector.collect(
    "JannikSinner"
)

assert html


parser = TennisAbstractPlayerParser()

results = parser.parse_results(
    html
)

assert results


print()
print("=" * 60)
print("TENNIS ABSTRACT - PARSED MATCHES")
print("=" * 60)

print(
    f"Matches found: {len(results)}"
)

for result in results[:10]:

    info = parser.extract_match_info(
        result,
        "Sinner"
    )

    print(
        result["Date"],
        "|",
        result["Tournament"],
        "|",
        result["Surface"],
        "|",
        result["Rd"],
        "|",
        "vs",
        info["opponent"],
        "|",
        "WIN" if info["won"] else "LOSS"
    )


print()
print("RESULT PARSER TEST PASSED")
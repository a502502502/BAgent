from providers.tennis.atp.parser import ATPParser
from providers.tennis.atp.normalizer import ATPNormalizer

parser = ATPParser()
normalizer = ATPNormalizer()

tournaments = parser.parse()

print("\n" + "=" * 70)
print("ATP NORMALIZER")
print("=" * 70)

for raw_tournament in tournaments:

    competition = normalizer.competition(raw_tournament)

    print(f"\n🏆 {competition.name}")

    for raw_match in raw_tournament.matches:

        match = normalizer.match(raw_match, competition)

        print(
            f"  • {match.home.name} vs {match.away.name}"
            f" | {match.round_name}"
            f" | {match.status}"
        )
from providers.tennis.atp.parser import ATPParser


parser = ATPParser()

tournaments = parser.parse()

print()

print("=" * 60)

print("ATP PARSER")

print("=" * 60)

for tournament in tournaments:

    print()

    print(tournament.name)

    print("-" * len(tournament.name))

    print(
        f"Partite: {len(tournament.matches)}"
    )

    for match in tournament.matches:

        print(

            f"{match.player.first_name} "
            f"{match.player.last_name}"

            "  vs  "

            f"{match.opponent.first_name} "
            f"{match.opponent.last_name}"

        )
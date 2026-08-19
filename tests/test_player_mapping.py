from application.validation.player_mapping import (
    PlayerMapping,
)

from infrastructure.providers.tennis.atp.ranking_provider import (
    ATPRankingProvider,
)


provider = ATPRankingProvider()

rankings = provider.fetch_week(
    "2026-06-22"
)

mapping = PlayerMapping(
    rankings
)


assert mapping.find(
    "Jannik Sinner"
) == 1

assert mapping.find(
    "Carlos Alcaraz"
) == 2

assert mapping.find(
    "Alexander Zverev"
) == 3

assert mapping.find(
    "Novak Djokovic"
) == 8


print()
print("=" * 60)
print("PLAYER MAPPING")
print("=" * 60)

for name in [
    "Jannik Sinner",
    "Carlos Alcaraz",
    "Alexander Zverev",
    "Novak Djokovic",
]:

    print(
        f"{name}: "
        f"rank={mapping.find(name)}"
    )

print()
print("PLAYER MAPPING TEST PASSED")
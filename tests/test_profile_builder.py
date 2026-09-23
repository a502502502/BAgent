from infrastructure.persistence.knowledge_repository import KnowledgeRepository

from services.profiles.profile_builder import ProfileBuilder

from domain.models.knowledge import Knowledge


repository = KnowledgeRepository()

repository.save(

    Knowledge(

        id="1",

        entity_type="PLAYER",

        entity_id="Juventus",

        key="LEAGUE_POSITION",

        value=1,

        value_type="INTEGER",

        source="SEASON_TABLE"

    )

)

repository.save(

    Knowledge(

        id="2",

        entity_type="PLAYER",

        entity_id="Juventus",

        key="ELO",

        value=2314,

        value_type="INTEGER",

        source="TennisAbstract"

    )

)

repository.save(

    Knowledge(

        id="3",

        entity_type="PLAYER",

        entity_id="Juventus",

        key="COUNTRY",

        value="ITA",

        value_type="STRING",

        source="SEASON_TABLE"

    )

)


builder = ProfileBuilder(repository)

profile = builder.build("Juventus")

print()

print("=" * 70)

print("PROFILE")

print("=" * 70)

print(profile)

print()

print("=" * 70)

print("KEYS")

print("=" * 70)

print(profile.keys())

print()

print("=" * 70)

print("LEAGUE POSITION")

print("=" * 70)

print(profile.get("LEAGUE_POSITION"))

print()

print("=" * 70)

print("ELO")

print("=" * 70)

print(profile.get("ELO"))
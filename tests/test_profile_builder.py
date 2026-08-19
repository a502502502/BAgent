from repository.knowledge_repository import KnowledgeRepository

from services.profiles.profile_builder import ProfileBuilder

from domain.models.knowledge import Knowledge


repository = KnowledgeRepository()

repository.save(

    Knowledge(

        id="1",

        entity_type="PLAYER",

        entity_id="JannikSinner",

        key="ATP_RANK",

        value=1,

        value_type="INTEGER",

        source="ATP"

    )

)

repository.save(

    Knowledge(

        id="2",

        entity_type="PLAYER",

        entity_id="JannikSinner",

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

        entity_id="JannikSinner",

        key="COUNTRY",

        value="ITA",

        value_type="STRING",

        source="ATP"

    )

)


builder = ProfileBuilder(repository)

profile = builder.build("JannikSinner")

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

print("ATP RANK")

print("=" * 70)

print(profile.get("ATP_RANK"))

print()

print("=" * 70)

print("ELO")

print("=" * 70)

print(profile.get("ELO"))
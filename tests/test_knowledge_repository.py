from infrastructure.persistence.knowledge_repository import KnowledgeRepository

from domain.models.knowledge import Knowledge


repository = KnowledgeRepository()


repository.save(

    Knowledge(

        id="KN-001",

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

        id="KN-002",

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

        id="KN-003",

        entity_type="PLAYER",

        entity_id="Milan",

        key="LEAGUE_POSITION",

        value=2,

        value_type="INTEGER",

        source="SEASON_TABLE"

    )

)


print()

print("=" * 70)

print("ALL KNOWLEDGE")

print("=" * 70)

for item in repository.find_all():

    print(item)

print()

print("=" * 70)

print("JUVENTUS")

print("=" * 70)

for item in repository.find_by_entity("Juventus"):

    print(item)

print()

print("=" * 70)

print("LEAGUE POSITION")

print("=" * 70)

print(

    repository.find_by_key(

        "Juventus",

        "LEAGUE_POSITION"

    )

)

print()
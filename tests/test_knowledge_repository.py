from repository.knowledge_repository import KnowledgeRepository

from domain.models.knowledge import Knowledge


repository = KnowledgeRepository()


repository.save(

    Knowledge(

        id="KN-001",

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

        id="KN-002",

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

        id="KN-003",

        entity_type="PLAYER",

        entity_id="CarlosAlcaraz",

        key="ATP_RANK",

        value=2,

        value_type="INTEGER",

        source="ATP"

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

print("JANNIK SINNER")

print("=" * 70)

for item in repository.find_by_entity("JannikSinner"):

    print(item)

print()

print("=" * 70)

print("ATP RANK")

print("=" * 70)

print(

    repository.find_by_key(

        "JannikSinner",

        "ATP_RANK"

    )

)

print()
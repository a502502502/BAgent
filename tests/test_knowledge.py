from domain.models.knowledge import Knowledge


knowledge = Knowledge(

    id="KN-0001",

    entity_type="PLAYER",

    entity_id="Juventus",

    key="LEAGUE_POSITION",

    value=1,

    value_type="INTEGER",

    source="SEASON_TABLE"

)

print()

print(knowledge)

print()
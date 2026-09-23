"""Costruisce il profilo di una squadra dalle conoscenze salvate."""


class ProfileBuilder:

    def __init__(self, repository):
        self.repository = repository

    def build(self, entity_id: str) -> dict:
        items = self.repository.find_by_entity(entity_id)
        return {item.key: item for item in items}

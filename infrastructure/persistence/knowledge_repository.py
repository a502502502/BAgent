from typing import Dict, List, Optional

from domain.models.knowledge import Knowledge


class KnowledgeRepository:

    def __init__(self):

        self._items: List[Knowledge] = []

    def save(self, knowledge: Knowledge):

        self._items.append(knowledge)

    def find_all(self) -> List[Knowledge]:

        return list(self._items)

    def find_by_entity(self, entity_id: str) -> List[Knowledge]:

        return [

            k

            for k in self._items

            if k.entity_id == entity_id

        ]

    def find_by_key(

        self,

        entity_id: str,

        key: str

    ) -> Optional[Knowledge]:

        for knowledge in self._items:

            if (

                knowledge.entity_id == entity_id

                and knowledge.key == key

            ):

                return knowledge

        return None
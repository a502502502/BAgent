from dataclasses import dataclass, field
from typing import Dict, Optional

from domain.models.knowledge import Knowledge


@dataclass
class Profile:

    entity_type: str

    entity_id: str

    knowledge: Dict[str, Knowledge] = field(default_factory=dict)

    def add(self, item: Knowledge):

        self.knowledge[item.key] = item

    def get(self, key: str) -> Optional[Knowledge]:

        return self.knowledge.get(key)

    def has(self, key: str) -> bool:

        return key in self.knowledge

    def keys(self):

        return sorted(self.knowledge.keys())

    def __len__(self):

        return len(self.knowledge)
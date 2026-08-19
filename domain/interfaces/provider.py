from abc import ABC, abstractmethod

from domain.models.event import Event


class Provider(ABC):

    @abstractmethod
    def fetch_events(self) -> list:
        """Restituisce gli eventi trovati."""
        pass
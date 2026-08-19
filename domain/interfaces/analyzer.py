from abc import ABC, abstractmethod

from domain.models.event import Event


class Analyzer(ABC):

    @abstractmethod
    def analyze(self, event: Event):
        pass
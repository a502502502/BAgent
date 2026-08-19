from abc import ABC, abstractmethod


class Strategy(ABC):

    @abstractmethod
    def select(self, predictions):
        pass
from abc import ABC, abstractmethod


class Repository(ABC):

    @abstractmethod
    def save_competition(self, competition):
        pass

    @abstractmethod
    def save_competitor(self, competitor):
        pass

    @abstractmethod
    def save_match(self, match):
        pass
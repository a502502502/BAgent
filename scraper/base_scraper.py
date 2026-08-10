from abc import ABC, abstractmethod


class BaseScraper(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def fetch_matches(self):
        pass

    def status(self):
        return f"{self.name} pronto"
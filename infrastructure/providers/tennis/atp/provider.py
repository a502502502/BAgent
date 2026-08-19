from domain.interfaces.provider import Provider

from .collector import ATPCollector
from .normalizer import ATPNormalizer


class ATPProvider(Provider):

    def __init__(self):

        self.collector = ATPCollector()

        self.normalizer = ATPNormalizer()

    def fetch_events(self):

        html = self.collector.collect()

        return self.normalizer.normalize(html)
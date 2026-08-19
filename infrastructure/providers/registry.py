from domain.interfaces.provider import Provider


class ProviderRegistry:

    def __init__(self):
        self._providers: list[Provider] = []

    def register(self, provider: Provider):
        self._providers.append(provider)

    def providers(self) -> list[Provider]:
        return self._providers

    def fetch_all_events(self):
        events = []

        for provider in self._providers:
            events.extend(provider.fetch_events())

        return events
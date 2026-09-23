"""Router stampa nazionali: ogni paese nella sua lingua, niente basket o vela."""

from services.football.external.sources.news import (
    NewsArticle,
    SixthSenseNewsCollector,
    is_football_article,
    is_international_competition,
    national_team_profile,
)


def test_nations_league_is_international_and_champions_league_is_not():
    assert is_international_competition("UEFA Nations League")
    assert is_international_competition("International Friendlies")
    assert is_international_competition("WC Qualification Europe")
    assert not is_international_competition("Serie A")
    assert not is_international_competition("UEFA Champions League")
    assert not is_international_competition(None)


def test_germany_and_netherlands_use_their_own_press():
    germany = national_team_profile("Germany")
    netherlands = national_team_profile("Olanda")
    assert germany is not None and "kicker.de" in germany["sites"]
    assert germany["language"] == "de"
    assert netherlands is not None and "nos.nl" in netherlands["sites"]
    assert "vi.nl" in netherlands["sites"]
    assert netherlands["language"] == "nl"
    assert national_team_profile("Andorra") is None


def test_serbia_and_greece_sites():
    serbia = national_team_profile("Serbia")
    greece = national_team_profile("Greece")
    assert {"tanjug.rs", "mozzartsport.com", "sportklub.rs"} <= set(serbia["sites"])
    assert {"sport24.gr", "sdna.gr"} <= set(greece["sites"])


def test_basket_and_sailing_are_dropped_and_kicker_is_kept():
    basket = NewsArticle(
        title="Netherlands 3x3: roster for the window",
        url="https://basketnews.com/netherlands",
        source="BasketNews.com",
        snippet="basketball",
    )
    sailing = NewsArticle(
        title="SailGP Netherlands claims the trophy",
        url="https://example.com/sail",
        source="NOS",
        snippet="yacht racing",
    )
    squad = NewsArticle(
        title="Klopp nominiert den Kader für die Nations League",
        url="https://www.kicker.de/klopp",
        source="kicker.de",
        snippet="Verletzung",
    )
    assert not is_football_article(basket)
    assert not is_football_article(sailing)
    assert is_football_article(squad)


class _FakeGoogle:
    def __init__(self):
        self.calls = []

    def search(self, query, language="it", country="IT", max_results=10):
        self.calls.append((query, language, country))
        return [
            NewsArticle(
                title=f"Nations League football {language} {query[:24]}",
                url=f"https://example.com/{len(self.calls)}",
                source="kicker.de",
                snippet="kader",
            )
        ]

    def search_match(self, **kwargs):
        raise AssertionError("la Nations League non deve usare la ricerca club")

    def search_team(self, **kwargs):
        raise AssertionError("la Nations League non deve usare il suffisso italiano")


def test_nations_league_queries_each_country_press():
    collector = SixthSenseNewsCollector()
    collector.newsapi.api_key = None
    collector.google = _FakeGoogle()

    bundle = collector.collect("Netherlands", "Germany", league="UEFA Nations League")

    queries = collector.google.calls
    assert bundle["press_router"] == "national"
    assert "nos.nl" in bundle["league_source"]
    assert "kicker.de" in bundle["league_source"]
    assert "uefa.com" in bundle["league_source"]
    assert any("site:nos.nl" in query and language == "nl" for query, language, _ in queries)
    assert any("site:kicker.de" in query and language == "de" for query, language, _ in queries)
    assert any("site:uefa.com" in query for query, _, _ in queries)
    joined = " ".join(query for query, _, _ in queries)
    assert "infortunio OR formazione OR notizie" not in joined
    assert bundle["total_articles"] > 0

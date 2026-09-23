"""
News collector per il Sesto Senso.

Fonti:
  - Google News RSS (gratuito, nessuna auth)
  - NewsAPI.org (gratuito fino a 100 req/giorno con API key)
  - Fonti specifiche per lega (eredivisie.com, ecc.)

Produce una lista di articoli strutturati pronti per l'analisi LLM.
"""

from __future__ import annotations

import os
import re
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from urllib.parse import quote_plus

import requests


# ------------------------------------------------------------------
# Configurazione fonti specifiche per lega
# ------------------------------------------------------------------

# Mappa: keyword lega → lista di siti da includere nelle ricerche Sesto Senso
# Usati come `site:url` nelle query Google News oppure come URL diretti da fetchare.
LEAGUE_SOURCES: dict[str, dict] = {
    "serie a": {
        "sites": ["gazzetta.it", "corrieredellosport.it", "tuttosport.com", "sport.sky.it", "mondopengwin.it"],
        "language": "it",
        "country": "IT",
        "search_suffix": "probabili formazioni OR infortunio OR conferenza stampa OR turnover OR ballottaggio",
        "note": "Quotidiani sportivi italiani primari (Gazzetta, Corriere, Tuttosport, Sky Sport, MondoPengwin).",
    },
    "serie b": {
        "sites": ["gazzetta.it", "corrieredellosport.it", "pianetaserieb.it", "mondopengwin.it"],
        "language": "it",
        "country": "IT",
        "search_suffix": "formazioni OR infortunio OR convocati",
        "note": "Fonti Serie B italiana.",
    },
    "premier league": {
        "sites": ["theathletic.com", "theguardian.com", "bbc.co.uk", "skysports.com", "mondopengwin.it"],
        "language": "en",
        "country": "GB",
        "search_suffix": "lineup OR injury news OR press conference OR team news OR tactical",
        "note": "Primary UK Football journalism (The Athletic, BBC Sport, The Guardian, Sky Sports, MondoPengwin).",
    },
    "championship": {
        "sites": ["bbc.co.uk", "skysports.com"],
        "language": "en",
        "country": "GB",
        "search_suffix": "team news OR injury OR lineup",
        "note": "English Championship news.",
    },
    "efl cup": {
        "sites": ["theathletic.com", "bbc.co.uk", "skysports.com"],
        "language": "en",
        "country": "GB",
        "search_suffix": "rotation OR team news OR lineup OR injury",
        "note": "Carabao / EFL Cup team news and rotations.",
    },
    "laliga": {
        "sites": ["marca.com", "as.com", "mundodeportivo.com", "sport.es", "mondopengwin.it"],
        "language": "es",
        "country": "ES",
        "search_suffix": "alineacion probable OR lesion OR rueda de prensa OR rotaciones OR convocatoria",
        "note": "Prensa deportiva española (Marca, AS, Mundo Deportivo, Sport, MondoPengwin).",
    },
    "segunda division": {
        "sites": ["marca.com", "as.com"],
        "language": "es",
        "country": "ES",
        "search_suffix": "alineacion OR lesion OR previa",
        "note": "Segunda División Española.",
    },
    "bundesliga": {
        "sites": ["kicker.de", "bild.de", "sport1.de", "mondopengwin.it"],
        "language": "de",
        "country": "DE",
        "search_suffix": "voraussichtliche aufstellung OR verletzung OR pressekonferenz OR kader",
        "note": "Deutsche Sportmedien (Kicker, Bild, Sport1, MondoPengwin).",
    },
    "ligue 1": {
        "sites": ["lequipe.fr", "footmercato.net", "maxifoot.fr", "mondopengwin.it"],
        "language": "fr",
        "country": "FR",
        "search_suffix": "composition probable OR blessure OR conference de presse OR groupe",
        "note": "Médias sportifs français (L'Équipe, FootMercato, MaxiFoot, MondoPengwin).",
    },
    "primeira liga": {
        "sites": ["abola.pt", "record.pt", "ojogo.pt"],
        "language": "pt",
        "country": "PT",
        "search_suffix": "onze provavel OR lesao OR conferencia de imprensa OR convocados",
        "note": "Jornais desportivos portugueses (A Bola, Record, O Jogo).",
    },
    "super lig": {
        "sites": ["fanatik.com.tr", "fotomac.com.tr", "ntvspor.net"],
        "language": "tr",
        "country": "TR",
        "search_suffix": "muhtemel 11 OR sakatlik OR basin toplantisi OR kadro",
        "note": "Türk spor medyası (Fanatik, Fotomaç).",
    },
    "champions league": {
        "sites": ["uefa.com", "gazzetta.it", "marca.com", "theguardian.com", "kicker.de", "lequipe.fr", "mondopengwin.it"],
        "language": "it",
        "country": "IT",
        "search_suffix": "probabili formazioni OR conferenza stampa OR infortuni OR turnover",
        "note": "UEFA Champions League Multi-Journalism Intelligence.",
    },
    "europa league": {
        "sites": ["uefa.com", "gazzetta.it", "marca.com", "theguardian.com", "kicker.de", "lequipe.fr", "mondopengwin.it"],
        "language": "it",
        "country": "IT",
        "search_suffix": "probabili formazioni OR conferenza stampa OR infortuni OR turnover",
        "note": "UEFA Europa League Multi-Journalism Intelligence.",
    },
    "conference league": {
        "sites": ["uefa.com", "gazzetta.it", "marca.com", "theguardian.com", "kicker.de", "mondopengwin.it"],
        "language": "it",
        "country": "IT",
        "search_suffix": "probabili formazioni OR conferenza stampa OR infortuni OR turnover",
        "note": "UEFA Europa Conference League Multi-Journalism Intelligence.",
    },
    "eredivisie": {
        "sites": ["vi.nl", "telegraaf.nl", "eredivisie.com"],
        "language": "nl",
        "country": "NL",
        "search_suffix": "blessure OR opstelling OR persconferentie OR nieuws",
        "base_url": "https://eredivisie.com",
        "club_url_template": "https://eredivisie.com/clubs/{slug}/",
        "note": "Nederlandse voetbalmedia (Voetbal International, De Telegraaf, Eredivisie).",
    },
    "brazil serie a": {
        "sites": ["ge.globo.com", "transfermarkt.com.br", "uol.com.br"],
        "language": "pt",
        "country": "BR",
        "search_suffix": "lesão OR escalação OR coletiva OR notícias",
        "note": "Fonti principali per il Brasileirão (Globo Esporte, UOL).",
    },
}

# Normalizza il nome di una squadra in slug URL (es. "Sparta Rotterdam" → "sparta-rotterdam")
def _team_to_slug(team_name: str) -> str:
    import re
    slug = team_name.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'\s+', '-', slug)
    return slug

def get_league_config(league: str) -> dict | None:
    """Restituisce la config della lega corrispondente (case-insensitive)."""
    league_lower = league.lower()
    for key, cfg in LEAGUE_SOURCES.items():
        if key in league_lower:
            return cfg
    return None


# Competizioni tra nazionali: il sesto senso non usa la stampa di un campionato club.
_INTERNATIONAL_MARKERS = (
    "nations league",
    "world cup",
    "coppa del mondo",
    "qualific",
    "friendl",
    "amichevol",
    "euro championship",
    "european championship",
)

# Stampa della nazionale, non del club. La chiave è il nome inglese usato da FootyStats.
NATIONAL_TEAM_SOURCES: dict[str, dict] = {
    "netherlands": {
        "aliases": ("netherlands", "holland", "olanda", "nederland"),
        "sites": ("nos.nl", "vi.nl", "telegraaf.nl"),
        "language": "nl",
        "country": "NL",
        "search_suffix": "voetbal OR oranje OR blessure OR opstelling OR selectie",
    },
    "germany": {
        "aliases": ("germany", "germania", "deutschland"),
        "sites": ("kicker.de", "sport1.de"),
        "language": "de",
        "country": "DE",
        "search_suffix": "kader OR verletzung OR aufstellung OR nationalmannschaft",
    },
    "serbia": {
        "aliases": ("serbia", "srbija"),
        "sites": ("tanjug.rs", "mozzartsport.com", "sportklub.rs"),
        "language": "sr",
        "country": "RS",
        "search_suffix": "reprezentacija OR spisak OR povreda OR fudbal",
    },
    "greece": {
        "aliases": ("greece", "grecia", "ellada"),
        "sites": ("sport24.gr", "sdna.gr"),
        "language": "el",
        "country": "GR",
        "search_suffix": "εθνική OR τραυματισμός OR αποστολή OR football",
    },
    "portugal": {
        "aliases": ("portugal",),
        "sites": ("abola.pt", "record.pt", "ojogo.pt"),
        "language": "pt",
        "country": "PT",
        "search_suffix": "seleção OR lesão OR convocados OR futebol",
    },
    "wales": {
        "aliases": ("wales", "galles", "cymru"),
        "sites": ("bbc.co.uk",),
        "language": "en",
        "country": "GB",
        "search_suffix": "Wales squad OR injury OR nations league",
    },
    "norway": {
        "aliases": ("norway", "norvegia", "norge"),
        "sites": ("vg.no", "nrk.no"),
        "language": "no",
        "country": "NO",
        "search_suffix": "landslaget OR skade OR tropp OR fotball",
    },
    "denmark": {
        "aliases": ("denmark", "danimarca", "danmark"),
        "sites": ("bold.dk", "dr.dk"),
        "language": "da",
        "country": "DK",
        "search_suffix": "landshold OR skade OR trup OR fodbold",
    },
    "italy": {
        "aliases": ("italy", "italia"),
        "sites": ("gazzetta.it", "corrieredellosport.it"),
        "language": "it",
        "country": "IT",
        "search_suffix": "nazionale OR convocati OR infortunio OR ct",
    },
    "france": {
        "aliases": ("france", "francia"),
        "sites": ("lequipe.fr",),
        "language": "fr",
        "country": "FR",
        "search_suffix": "équipe de france OR bleus OR blessure OR liste",
    },
    "spain": {
        "aliases": ("spain", "spagna", "españa"),
        "sites": ("marca.com", "as.com"),
        "language": "es",
        "country": "ES",
        "search_suffix": "selección OR lesión OR convocatoria OR absoluta",
    },
    "england": {
        "aliases": ("england", "inghilterra"),
        "sites": ("bbc.co.uk", "theguardian.com"),
        "language": "en",
        "country": "GB",
        "search_suffix": "England squad OR injury OR Three Lions",
    },
    "belgium": {
        "aliases": ("belgium", "belgio", "belgique"),
        "sites": ("rtbf.be",),
        "language": "fr",
        "country": "BE",
        "search_suffix": "diables rouges OR sélection OR blessure",
    },
}

_INTERNATIONAL_SITES = ("uefa.com",)
_OFF_TOPIC = re.compile(
    r"\b(basket(?:ball)?|3x3|volley(?:ball)?|pallavolo|sailgp|yacht|nba|euroleague|tennis|formula\s*1|the voice|serie tv)\b",
    re.IGNORECASE,
)
_FOOTBALL_TEXT = re.compile(
    r"football|calcio|voetbal|fussball|fußball|fudbal|fodbold|fotball|soccer|"
    r"nations league|nazionale|oranje|mannschaft|kader|convoc|blessure|infortun|"
    r"les[aã]o|sakat|opstelling|aufstellung|reprezentac|national team|uefa|fifa|"
    r"landslag|landshold|selec",
    re.IGNORECASE,
)
_FOOTBALL_SOURCE = (
    "kicker", "nos.nl", "nos ", "vi.nl", "telegraaf", "uefa", "tanjug",
    "mozzart", "sportklub", "sport24", "sdna", "bbc", "abola", "record.pt",
    "ojogo", "gazzetta", "lequipe", "l'équipe", "marca", "vg.no", "nrk",
    "bold.dk", "sport1",
)


def is_international_competition(league: str | None) -> bool:
    """Nations League, Mondiale, qualificazioni e amichevoli non sono un campionato club."""
    if not league:
        return False
    text = league.lower()
    return any(marker in text for marker in _INTERNATIONAL_MARKERS)


def national_team_profile(team: str) -> dict | None:
    """Profilo stampa della nazionale. None se il paese non è mappato."""
    name = team.strip().lower()
    for profile in NATIONAL_TEAM_SOURCES.values():
        if name in profile["aliases"]:
            return profile
    return None


def is_football_article(article: "NewsArticle") -> bool:
    """Scarta basket, vela e televisione quando il testo non parla di calcio."""
    text = f"{article.title} {article.snippet or ''} {article.source}"
    if _OFF_TOPIC.search(text) and not _FOOTBALL_TEXT.search(text):
        return False
    if _FOOTBALL_TEXT.search(text):
        return True
    identity = f"{article.source} {article.url}".lower()
    return any(token in identity for token in _FOOTBALL_SOURCE)


def _dedupe_articles(articles: list["NewsArticle"]) -> list["NewsArticle"]:
    seen: set[str] = set()
    unique: list[NewsArticle] = []
    for article in articles:
        key = article.title.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(article)
    return unique


# ------------------------------------------------------------------
# Matrice Pesi Dinamici Sesto Senso (Pilastro 5)
# ------------------------------------------------------------------
SOURCE_WEIGHTS_BY_CATEGORY: dict[str, dict[str, float]] = {
    "MULTIGOL_COMBO": {
        "mondopengwin.it": 1.40,
        "footystats.org": 1.35,
        "gazzetta.it": 1.15,
        "marca.com": 1.15,
        "kicker.de": 1.15,
        "bbc.co.uk": 1.15,
        "_default": 1.00
    },
    "CORNER": {
        "footystats.org": 1.50,
        "theathletic.com": 1.25,
        "bbc.co.uk": 1.20,
        "mondopengwin.it": 1.10,
        "_default": 1.00
    },
    "CARTELLINI": {
        "footystats.org": 1.45,
        "marca.com": 1.35,
        "ole.com.ar": 1.35,
        "gazzetta.it": 1.25,
        "mondopengwin.it": 1.20,
        "_default": 1.00
    },
    "LINEUP_INJURY": {
        "gazzetta.it": 1.50,
        "marca.com": 1.50,
        "kicker.de": 1.50,
        "lequipe.fr": 1.50,
        "theathletic.com": 1.40,
        "mondopengwin.it": 1.30,
        "_default": 1.00
    }
}

def calculate_weighted_confidence(sources_cited: list[str], market_category: str) -> float:
    """
    Calcola l'indice di affidabilità ponderata (Weighted Source Index)
    basato sulla matrice di specializzazione delle fonti di Sesto Senso.
    """
    weights = SOURCE_WEIGHTS_BY_CATEGORY.get(market_category.upper(), SOURCE_WEIGHTS_BY_CATEGORY["MULTIGOL_COMBO"])
    if not sources_cited:
        return 1.00

    total_weight = 0.0
    matched = 0
    for src in sources_cited:
        src_clean = src.lower().strip()
        assigned_w = weights.get("_default", 1.0)
        for domain, w in weights.items():
            if domain != "_default" and domain in src_clean:
                assigned_w = w
                break
        total_weight += assigned_w
        matched += 1

    return round(total_weight / max(1, matched), 2)


# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------

@dataclass
class NewsArticle:
    title: str
    url: str
    source: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    language: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "published_at": self.published_at,
            "snippet": self.snippet,
            "language": self.language,
        }


# ------------------------------------------------------------------
# Google News RSS
# ------------------------------------------------------------------

class GoogleNewsSource:
    """
    Cerca notizie via Google News RSS.
    Completamente gratuito, nessuna API key necessaria.
    """

    RSS_URL = "https://news.google.com/rss/search"

    def __init__(self, delay: float = 1.0):
        self._delay = delay
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36"
            )
        })

    def search(
        self,
        query: str,
        language: str = "it",
        country: str = "IT",
        max_results: int = 10,
    ) -> list[NewsArticle]:
        """
        Cerca articoli su Google News RSS.
        language/country: es. 'en'/'GB', 'es'/'ES', 'de'/'DE'
        """
        time.sleep(self._delay)

        params = {
            "q": query,
            "hl": language,
            "gl": country,
            "ceid": f"{country}:{language}",
        }

        r = self._session.get(self.RSS_URL, params=params, timeout=15)
        r.raise_for_status()

        return self._parse_rss(r.text, max_results)

    def _parse_rss(self, xml_text: str, max_results: int) -> list[NewsArticle]:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            return []

        articles = []
        ns = {"media": "http://search.yahoo.com/mrss/"}

        for item in root.findall(".//item")[:max_results]:
            title = item.findtext("title") or ""
            url = item.findtext("link") or ""
            pub_date = item.findtext("pubDate")
            source_el = item.find("source")
            source = source_el.text if source_el is not None else "Google News"
            description = item.findtext("description") or ""

            articles.append(NewsArticle(
                title=title,
                url=url,
                source=source,
                published_at=pub_date,
                snippet=description[:300] if description else None,
            ))

        return articles

    def search_team(
        self,
        team: str,
        language: str = "it",
        country: str = "IT",
        max_results: int = 8,
    ) -> list[NewsArticle]:
        """Cerca notizie recenti su una squadra."""
        return self.search(
            query=f'"{team}" infortunio OR allenatore OR notizie',
            language=language,
            country=country,
            max_results=max_results,
        )

    def search_match(
        self,
        home: str,
        away: str,
        language: str = "it",
        country: str = "IT",
        max_results: int = 10,
    ) -> list[NewsArticle]:
        """Cerca notizie specifiche su una partita."""
        return self.search(
            query=f'"{home}" "{away}"',
            language=language,
            country=country,
            max_results=max_results,
        )


# ------------------------------------------------------------------
# NewsAPI.org
# ------------------------------------------------------------------

class NewsAPISource:
    """
    NewsAPI.org — piano gratuito: 100 req/giorno, articoli ultimi 30gg.
    Richiede API key (gratuita su newsapi.org).
    """

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWSAPI_KEY")
        self._session = requests.Session()

    def _available(self) -> bool:
        return bool(self.api_key)

    def search(
        self,
        query: str,
        language: str = "it",
        max_results: int = 10,
        sort_by: str = "publishedAt",
    ) -> list[NewsArticle]:
        if not self._available():
            return []

        r = self._session.get(
            f"{self.BASE_URL}/everything",
            params={
                "q": query,
                "language": language,
                "sortBy": sort_by,
                "pageSize": min(max_results, 100),
                "apiKey": self.api_key,
            },
            timeout=15,
        )
        r.raise_for_status()
        data = r.json()

        articles = []
        for a in data.get("articles", []):
            articles.append(NewsArticle(
                title=a.get("title") or "",
                url=a.get("url") or "",
                source=a.get("source", {}).get("name") or "NewsAPI",
                published_at=a.get("publishedAt"),
                snippet=a.get("description"),
                language=language,
            ))

        return articles


# ------------------------------------------------------------------
# Orchestratore
# ------------------------------------------------------------------

class SixthSenseNewsCollector:
    """
    Raccoglie notizie per una partita combinando Google News + NewsAPI.
    Se viene fornita una lega, usa anche le fonti specifiche configurate
    in LEAGUE_SOURCES (es. eredivisie.com per partite olandesi).
    Produce un bundle pronto per l'analisi LLM.
    """

    def __init__(
        self,
        newsapi_key: Optional[str] = None,
        language: str = "it",
        country: str = "IT",
    ):
        self.google = GoogleNewsSource()
        self.newsapi = NewsAPISource(api_key=newsapi_key)
        self.language = language
        self.country = country

    def _national_team_articles(
        self,
        team: str,
        profile: dict | None,
        max_results: int,
    ) -> list[NewsArticle]:
        if profile is None:
            return self.google.search(
                query=f'"{team}" (football OR soccer) (squad OR injury OR "nations league")',
                language="en",
                country="US",
                max_results=max_results,
            )
        return self.google.search(
            query=f'"{team}" {profile["search_suffix"]}',
            language=profile["language"],
            country=profile["country"],
            max_results=max_results,
        )

    def _collect_international(
        self,
        home: str,
        away: str,
        match_date: Optional[str],
        collected_at: str,
        max_per_team: int,
        league: Optional[str],
    ) -> dict:
        """Stampa di ciascun paese, nella sua lingua, più UEFA. Niente fallback italiano."""
        home_profile = national_team_profile(home)
        away_profile = national_team_profile(away)
        sites: list[str] = list(_INTERNATIONAL_SITES)
        for profile in (home_profile, away_profile):
            if profile:
                sites.extend(profile["sites"])

        match_articles = self.google.search(
            query=f'"{home}" "{away}" (football OR soccer OR "nations league" OR calcio)',
            language="en",
            country="US",
            max_results=max_per_team,
        )
        for profile in (home_profile, away_profile):
            if not profile:
                continue
            match_articles += self.google.search(
                query=f'"{home}" "{away}" {profile["search_suffix"]}',
                language=profile["language"],
                country=profile["country"],
                max_results=4,
            )

        home_articles = self._national_team_articles(home, home_profile, max_per_team)
        away_articles = self._national_team_articles(away, away_profile, max_per_team)

        for site in sites:
            owner = next(
                (
                    profile
                    for profile in (home_profile, away_profile)
                    if profile and site in profile["sites"]
                ),
                None,
            )
            for team, _profile in ((home, home_profile), (away, away_profile)):
                if owner:
                    language = owner["language"]
                    country = owner["country"]
                    suffix = owner["search_suffix"]
                else:
                    language, country = "en", "US"
                    suffix = 'football OR squad OR injury OR "nations league"'
                extra = self.google.search(
                    query=f'site:{site} "{team}" {suffix}',
                    language=language,
                    country=country,
                    max_results=4,
                )
                if team == home:
                    home_articles += extra
                else:
                    away_articles += extra

        if self.newsapi._available():
            for team, profile in ((home, home_profile), (away, away_profile)):
                language = (profile or {}).get("language", "en")
                if language not in ("en", "it", "de", "fr", "es", "pt", "nl", "no"):
                    language = "en"
                found = self.newsapi.search(
                    query=f'"{team}" football OR soccer OR "nations league"',
                    language=language,
                    max_results=4,
                )
                if team == home:
                    home_articles += found
                else:
                    away_articles += found

        match_articles = _dedupe_articles([a for a in match_articles if is_football_article(a)])
        home_articles = _dedupe_articles([a for a in home_articles if is_football_article(a)])
        away_articles = _dedupe_articles([a for a in away_articles if is_football_article(a)])

        return {
            "home": home,
            "away": away,
            "match_date": match_date,
            "collected_at": collected_at,
            "league": league,
            "league_source": ", ".join(sites),
            "press_router": "national",
            "articles": {
                "match": [a.to_dict() for a in match_articles],
                "home_team": [a.to_dict() for a in home_articles],
                "away_team": [a.to_dict() for a in away_articles],
            },
            "total_articles": len(match_articles) + len(home_articles) + len(away_articles),
        }

    def collect(
        self,
        home: str,
        away: str,
        match_date: Optional[str] = None,
        max_per_team: int = 8,
        league: Optional[str] = None,
    ) -> dict:
        """
        Raccoglie tutte le notizie disponibili per una partita.
        Se `league` è specificata, usa anche le fonti configurate in LEAGUE_SOURCES.

        Ritorna:
        {
            "home": str,
            "away": str,
            "collected_at": str,
            "league": str | None,
            "league_source": str | None,   # es. "eredivisie.com"
            "articles": {
                "match": [...],
                "home_team": [...],
                "away_team": [...]
            },
            "total_articles": int
        }
        """
        collected_at = datetime.utcnow().isoformat()

        if is_international_competition(league):
            return self._collect_international(
                home, away, match_date, collected_at, max_per_team, league
            )

        # Determina lingua/paese: usa config lega se disponibile
        league_cfg = get_league_config(league) if league else None
        lang = league_cfg["language"] if league_cfg else self.language
        country = league_cfg["country"] if league_cfg else self.country
        suffix = league_cfg.get("search_suffix", "infortunio OR formazione OR notizie") if league_cfg else "infortunio OR formazione OR notizie"
        league_sites = league_cfg.get("sites", []) if league_cfg else []

        # Notizie sulla partita (lingua locale)
        match_articles = self.google.search_match(
            home=home,
            away=away,
            language=lang,
            country=country,
            max_results=max_per_team,
        )

        # Notizie singole squadre (lingua locale)
        home_articles = self.google.search_team(
            team=home,
            language=lang,
            country=country,
            max_results=max_per_team,
        )

        away_articles = self.google.search_team(
            team=away,
            language=lang,
            country=country,
            max_results=max_per_team,
        )

        # Ricerche aggiuntive sui siti specifici della lega
        # (es. site:eredivisie.com "Telstar" blessure OR opstelling)
        for site in league_sites:
            for team in [home, away]:
                slug = _team_to_slug(team)
                site_query = f'site:{site} "{team}" {suffix}'
                extra = self.google.search(
                    query=site_query,
                    language=lang,
                    country=country,
                    max_results=5,
                )
                if team == home:
                    home_articles += extra
                else:
                    away_articles += extra

        # Integra con NewsAPI se disponibile
        if self.newsapi._available():
            home_articles += self.newsapi.search(
                query=home,
                language=lang,
                max_results=5,
            )
            away_articles += self.newsapi.search(
                query=away,
                language=lang,
                max_results=5,
            )

        all_articles = (
            [a.to_dict() for a in match_articles],
            [a.to_dict() for a in home_articles],
            [a.to_dict() for a in away_articles],
        )

        total = sum(len(a) for a in all_articles)

        return {
            "home": home,
            "away": away,
            "match_date": match_date,
            "collected_at": collected_at,
            "league": league,
            "league_source": league_sites[0] if league_sites else None,
            "articles": {
                "match": all_articles[0],
                "home_team": all_articles[1],
                "away_team": all_articles[2],
            },
            "total_articles": total,
        }

    def format_for_llm(self, bundle: dict) -> str:
        """
        Formatta il bundle di notizie come testo strutturato
        pronto da passare a un LLM per l'analisi del Sesto Senso.
        """
        home = bundle["home"]
        away = bundle["away"]
        date = bundle.get("match_date", "N/A")

        league_label = bundle.get("league", "")
        league_src = bundle.get("league_source", "")
        header_extra = ""
        if league_label:
            header_extra = f" | Lega: {league_label}"
        if league_src:
            header_extra += f" | Fonte extra: {league_src}"

        lines = [
            f"=== ANALISI SESTO SENSO: {home} vs {away} ({date}){header_extra} ===",
            "",
        ]

        sections = [
            ("NOTIZIE SULLA PARTITA", bundle["articles"]["match"]),
            (f"NOTIZIE {home.upper()}", bundle["articles"]["home_team"]),
            (f"NOTIZIE {away.upper()}", bundle["articles"]["away_team"]),
        ]

        for title, articles in sections:
            if not articles:
                continue
            lines.append(f"--- {title} ---")
            for i, a in enumerate(articles, 1):
                lines.append(f"{i}. {a['title']}")
                if a.get("snippet"):
                    lines.append(f"   {a['snippet'][:200]}")
                lines.append(f"   Fonte: {a['source']} | {a.get('published_at', '')}")
                lines.append("")

        lines += [
            "=== ISTRUZIONI PER L'ANALISI ===",
            "Analizza le notizie sopra e identifica:",
            "1. Infortuni o assenze di giocatori chiave (con stima dell'impatto)",
            "2. Cambi di allenatore recenti o tensioni nello staff",
            "3. Fattori extra-campo (scandali, motivazione, eventi speciali)",
            "4. Condizione generale della squadra (morale, stanchezza, pressione)",
            "",
            "Per ogni fattore identificato, fornisci:",
            "- team: quale squadra riguarda",
            "- event_type: categoria (injury/coach_change/morale/fatigue/other)",
            "- impact: stima impatto (-3 molto negativo ... +3 molto positivo)",
            "- confidence: quanto sei sicuro (0.0-1.0)",
            "- notes: breve spiegazione",
        ]

        return "\n".join(lines)

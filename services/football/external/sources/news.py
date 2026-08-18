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
    "eredivisie": {
        "sites": ["eredivisie.com"],
        "language": "nl",
        "country": "NL",
        "search_suffix": "blessure OR opstelling OR nieuws OR schorsing",
        "base_url": "https://eredivisie.com",
        # Slug normalizzazione: team_name → slug per URL club page
        # es. "Sparta Rotterdam" → "sparta-rotterdam"
        "club_url_template": "https://eredivisie.com/clubs/{slug}/",
        "note": (
            "Fonte ufficiale Eredivisie. Contiene notizie su blessures (infortuni), "
            "opstellingen (formazioni), scouting e trasferimenti. "
            "Il sito è JavaScript-rendered: usare ricerca Google con site:eredivisie.com."
        ),
    },
    "brazil serie a": {
        "sites": ["ge.globo.com", "transfermarkt.com.br"],
        "language": "pt",
        "country": "BR",
        "search_suffix": "lesão OR escalação OR notícias",
        "note": "Fonti principali per il Brasileirão.",
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

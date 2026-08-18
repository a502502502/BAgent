"""
MultiSourceCollector — orchestratore delle fonti gratuite.

Sostituisce FootballExternalCollector (API-Football) con:
  - SofaScore     → fixture live, lineups, odds, form (qualsiasi campionato)
  - ClubElo       → rating ELO per campionati europei
  - FootballDataUK → dati storici CSV per modello base
  - SixthSenseNewsCollector → notizie per il Sesto Senso
  - OddsAPICollector → quote reali corner, btts, qualificazione

Utilizzo base:
    collector = MultiSourceCollector()
    result = collector.collect("Juventus", "Inter", date(2025, 3, 15))
    sixth = collector.collect_sixth_sense("Juventus", "Inter", date(2025, 3, 15))
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional

from services.football.external.sources.sofascore import SofaScoreSource
from services.football.external.sources.club_elo import ClubEloSource
from services.football.external.sources.football_data_uk import FootballDataUKSource
from services.football.external.sources.news import SixthSenseNewsCollector
from services.football.external.sources.totalcorner import TotalCornerSource
from services.football.external.collector import FootballExternalCollector
from services.football.external.sources.odds_api import OddsAPICollector, SPORT_KEYS


# Mapping league_id API-Football → sport key The Odds API
# NOTA: Conference League (848) ed Europa League (3) NON sono coperte da The Odds API
LEAGUE_TO_SPORT_KEY: dict[int, str] = {
    2:   SPORT_KEYS["champions_league_qual"],  # CL Qualification
    39:  SPORT_KEYS["premier_league"],
    135: SPORT_KEYS["serie_a"],
    136: SPORT_KEYS["serie_b"],
    140: SPORT_KEYS["la_liga"],
    78:  SPORT_KEYS["bundesliga"],
    61:  SPORT_KEYS["ligue_1"],
    88:  SPORT_KEYS["eredivisie"],
    106: SPORT_KEYS["ekstraklasa"],
    113: SPORT_KEYS["allsvenskan"],
    119: SPORT_KEYS["superliga_dk"],
}


class MultiSourceCollector:
    """
    Raccoglie dati da tutte le fonti disponibili per qualsiasi partita.

    Gerarchia fonti:
      1. API-Football (primaria) — infortuni reali, formazioni, quote ufficiali
      2. ClubElo                 — probabilità ELO quando non c'è storico
      3. SofaScore               — fallback se API-Football non trova la partita
      4. Google News + NewsAPI   — notizie per il Sesto Senso

    Parametri:
        api_football_key: chiave API-Football (default da env API_FOOTBALL_KEY)
        league_id:        ID campionato API-Football (opzionale, velocizza ricerca)
        season:           anno stagione (es. 2024)
        cache_dir:        cartella per caching CSV football-data.co.uk
        newsapi_key:      API key NewsAPI.org (opzionale)
        language:         lingua per la ricerca notizie (default 'it')
        country:          paese per Google News (default 'IT')
        sofascore_delay:  secondi tra richieste SofaScore (default 0.5)
    """

    def __init__(
        self,
        api_football_key: Optional[str] = None,
        odds_api_key: Optional[str] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        cache_dir: Optional[Path] = None,
        newsapi_key: Optional[str] = None,
        language: str = "it",
        country: str = "IT",
        sofascore_delay: float = 0.5,
    ):
        self.league_id = league_id
        self.season = season

        # API-Football (primaria)
        try:
            self.api_football = FootballExternalCollector(
                api_key=api_football_key or os.getenv("API_FOOTBALL_KEY")
            )
        except RuntimeError:
            self.api_football = None

        # The Odds API (corner, btts, qualificazione)
        try:
            self.odds_api = OddsAPICollector(
                api_key=odds_api_key or os.getenv("ODDS_API_KEY")
            )
        except RuntimeError:
            self.odds_api = None

        # Fonti secondarie
        self.sofascore = SofaScoreSource(delay=sofascore_delay)
        self.totalcorner = TotalCornerSource(delay=1.0)
        self.club_elo = ClubEloSource()
        self.football_data = FootballDataUKSource(
            cache_dir=cache_dir or Path("data/football/cache")
        )
        self.news = SixthSenseNewsCollector(
            newsapi_key=newsapi_key or os.getenv("NEWSAPI_KEY"),
            language=language,
            country=country,
        )

    # ------------------------------------------------------------------
    # Collect base
    # ------------------------------------------------------------------

    def collect(
        self,
        home: str,
        away: str,
        match_date: date,
    ) -> dict:
        """
        Raccoglie tutti i dati statistici per una partita.

        Ritorna un dict con:
          - sofascore: fixture, lineups, odds, form delle squadre
          - elo: rating e probabilità stimate da ClubElo
          - collected_at: timestamp UTC
        """
        collected_at = datetime.now(timezone.utc).isoformat()

        # 1. API-Football (primaria)
        api_football_data = None
        if self.api_football:
            try:
                api_football_data = self.api_football.collect_sixth_sense(
                    home=home,
                    away=away,
                    match_date=match_date,
                    league_id=self.league_id,
                    season=self.season,
                )
            except Exception as e:
                api_football_data = {"status": "ERROR", "error": str(e)}

        # 2. SofaScore (fallback se API-Football non trova la partita)
        sofascore_data = None
        if not api_football_data or api_football_data.get("status") != "OK":
            try:
                sofascore_data = self.sofascore.collect(home, away, match_date)
            except Exception as e:
                sofascore_data = {"error": str(e), "status": "unavailable"}

        # 3. ClubElo (probabilità ELO)
        try:
            elo_data = self.club_elo.win_probability(home, away, match_date)
        except Exception:
            elo_data = None

        return {
            "home": home,
            "away": away,
            "match_date": match_date.isoformat(),
            "collected_at": collected_at,
            "api_football": api_football_data,
            "sofascore": sofascore_data,
            "elo": elo_data,
        }

    # ------------------------------------------------------------------
    # Collect Sixth Sense
    # ------------------------------------------------------------------

    def collect_sixth_sense(
        self,
        home: str,
        away: str,
        match_date: date,
        include_news: bool = True,
    ) -> dict:
        """
        Raccoglie dati statistici + notizie per l'analisi del Sesto Senso.

        Ritorna un dict con:
          - tutti i campi di collect()
          - news: bundle notizie Google News + NewsAPI
          - news_prompt: testo formattato pronto per l'analisi LLM
          - sixth_sense: struttura per ricevere il risultato dell'analisi
        """
        base = self.collect(home, away, match_date)

        news_bundle = {}
        news_prompt = ""

        if include_news:
            try:
                news_bundle = self.news.collect(
                    home=home,
                    away=away,
                    match_date=match_date.isoformat(),
                )
                news_prompt = self.news.format_for_llm(news_bundle)
            except Exception as e:
                print(f"[News] Notizie non disponibili ({type(e).__name__}) — procedo senza")
                news_bundle = {}
                news_prompt = ""

        # TotalCorner — statistiche storiche Over/Under, gol, corner, forma
        totalcorner_data: dict = {}
        totalcorner_prompt = ""
        try:
            totalcorner_data = self.totalcorner.collect(home, away, match_date)
            if totalcorner_data.get("found"):
                totalcorner_prompt = self.totalcorner.format_for_prompt(totalcorner_data)
        except Exception as e:
            print(f"[TotalCorner] Dati non disponibili ({type(e).__name__}) — procedo senza")

        # Aggiunge infortuni e formazioni da API-Football al prompt LLM
        api_data = base.get("api_football") or {}
        structured_context = self._build_structured_context(api_data, home, away)
        if structured_context:
            news_prompt = structured_context + "\n\n" + news_prompt
        if totalcorner_prompt:
            news_prompt = totalcorner_prompt + "\n\n" + news_prompt

        # Quote reali: prima API-Football, poi SofaScore come fallback
        market_odds_from_api = api_data.get("market_odds", {})
        if not market_odds_from_api and base.get("sofascore", {}).get("found"):
            ss_data = base["sofascore"]
            raw_odds = ss_data.get("odds", {})
            market_odds_from_api = self.sofascore.parse_odds(raw_odds)

        # Statistiche corner da API-Football (per CornerModel)
        home_corner_stats = api_data.get("home_corner_stats", {})
        away_corner_stats = api_data.get("away_corner_stats", {})
        if home_corner_stats or away_corner_stats:
            if api_data:
                api_data["home_corner_stats"] = home_corner_stats
                api_data["away_corner_stats"] = away_corner_stats

        # The Odds API — corner, btts, qualificazione
        odds_api_data: dict = {}
        if self.odds_api and self.league_id:
            sport_key = LEAGUE_TO_SPORT_KEY.get(self.league_id)
            if sport_key:
                try:
                    odds_api_data = self.odds_api.collect(
                        sport_key=sport_key,
                        home=home,
                        away=away,
                        match_date=match_date.isoformat(),
                        include_corners=True,
                        include_qualify=True,
                    )
                    if odds_api_data.get("status") == "OK":
                        # Merge quote principali (se non già presenti)
                        for k, v in odds_api_data.get("market_odds", {}).items():
                            if k not in market_odds_from_api:
                                market_odds_from_api[k] = v
                        # Corner odds (over_9_5, ecc.) → aggiunge alle market_odds
                        market_odds_from_api.update(odds_api_data.get("corner_odds", {}))
                        # Qualify odds
                        market_odds_from_api.update(odds_api_data.get("qualify_odds", {}))
                    else:
                        print(f"[OddsAPI] Evento non trovato: {home} vs {away}")
                except Exception as e:
                    print(f"[OddsAPI] Errore raccolta dati: {e}")

        return {
            **base,
            "news": news_bundle,
            "news_prompt": news_prompt,
            "market_odds_from_api": market_odds_from_api,
            "odds_api": odds_api_data,
            "totalcorner": totalcorner_data,
            "sixth_sense": {
                "events": [],
                "home_impact": 0.0,
                "draw_impact": 0.0,
                "away_impact": 0.0,
                "confidence": 0.0,
                "status": "COLLECTED_ONLY",
                "analyzed_at": None,
            },
        }

    def _build_structured_context(self, api_data: dict, home: str, away: str) -> str:
        """
        Costruisce il contesto strutturato (infortuni + formazioni)
        da aggiungere al prompt del Sesto Senso.
        """
        if not api_data or api_data.get("status") != "OK":
            return ""

        sections = []

        injuries_text = api_data.get("injuries_text", "")
        if injuries_text and injuries_text != "Nessun infortunio registrato.":
            sections.append(
                "=== INFORTUNI E INDISPONIBILI (fonte: API-Football) ===\n"
                + injuries_text
            )

        lineups_text = api_data.get("lineups_text", "")
        if lineups_text and lineups_text != "Formazioni non ancora disponibili.":
            sections.append(
                "=== FORMAZIONI UFFICIALI (fonte: API-Football) ===\n"
                + lineups_text
            )

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # Historical data helpers
    # ------------------------------------------------------------------

    def load_historical(
        self,
        league: str,
        season: int,
    ):
        """
        Carica dati storici da football-data.co.uk.
        league: es. 'serie_b', 'premier_league'
        season: anno inizio stagione (es. 2024)
        """
        return self.football_data.load(league, season)

    def team_form_stats(
        self,
        df,
        team: str,
        before_date,
        n: int = 10,
    ) -> dict:
        """Statistiche di forma per una squadra su dati storici."""
        return self.football_data.form_stats(df, team, before_date, n)

"""
SixthSenseEngine — pipeline completa BAgent.

Flusso:
  1. Raccoglie dati statistici (SofaScore + ClubElo)
  2. Raccoglie notizie (Google News + NewsAPI)
  3. Analizza notizie con LLM (Claude)
  4. Aggiusta le probabilità base con gli eventi trovati
  5. Identifica value bets rispetto alle quote di mercato

Utilizzo:
    engine = SixthSenseEngine()
    result = engine.analyze(
        home="Juventus",
        away="Inter",
        match_date=date(2025, 9, 20),
        market_odds={"home_win": 2.10, "draw": 3.40, "away_win": 3.60}
    )
    print(result.report())
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional

from services.football.external.multi_collector import MultiSourceCollector
from services.football.sixth_sense.analyzer import (
    SixthSenseAnalyzer,
    SixthSenseAnalysis,
)
from services.football.sixth_sense.adjuster import (
    ProbabilityAdjuster,
    AdjustedProbabilities,
)
from services.football.base_model.goal_model import GoalModel
from services.football.base_model.corner_model import CornerModel
from services.football.base_model.aggregate_model import AggregateModel
from services.football.sixth_sense.repository import SixthSenseRepository


# ------------------------------------------------------------------
# Result container
# ------------------------------------------------------------------

@dataclass
class MatchAnalysisResult:
    home: str
    away: str
    match_date: str
    analyzed_at: str

    # Probabilità
    base_probs: dict              # da ClubElo o V3
    adjusted_probs: AdjustedProbabilities

    # Sesto Senso
    sixth_sense: SixthSenseAnalysis

    # Value bets
    value_signals: list[dict] = field(default_factory=list)
    market_odds: dict = field(default_factory=dict)

    # Mercati gol (Over/Under, BTTS)
    goal_markets: dict = field(default_factory=dict)

    # Mercati corner
    corner_markets: dict = field(default_factory=dict)

    # Probabilità qualificazione (solo partite di coppa con andata/ritorno)
    qualification_probs: dict = field(default_factory=dict)

    # Dati grezzi per debug/log
    raw_data: dict = field(default_factory=dict)

    def report(self) -> str:
        """
        Genera un report testuale completo della partita.
        """
        lines = [
            "=" * 60,
            f"  {self.home.upper()} vs {self.away.upper()}",
            f"  {self.match_date}",
            "=" * 60,
            "",
            "── PROBABILITÀ BASE (modello statistico) ──────────────",
            f"  Home Win : {self.base_probs.get('home_win', 0):.1%}",
            f"  Draw     : {self.base_probs.get('draw', 0):.1%}",
            f"  Away Win : {self.base_probs.get('away_win', 0):.1%}",
            "",
        ]

        # Sesto Senso
        ss = self.sixth_sense
        adj = self.adjusted_probs

        if ss.status == "NO_NEWS":
            lines.append("── SESTO SENSO ─────────────────────────────────────────")
            lines.append("  Nessuna notizia disponibile.")
        elif ss.status == "NO_EVENTS":
            lines.append("── SESTO SENSO ─────────────────────────────────────────")
            lines.append("  Notizie analizzate, nessun evento rilevante trovato.")
        elif ss.status == "ERROR":
            lines.append("── SESTO SENSO ─────────────────────────────────────────")
            lines.append(f"  Errore: {ss.summary}")
        else:
            lines += [
                "── SESTO SENSO ─────────────────────────────────────────",
                f"  Confidenza: {ss.overall_confidence:.0%}",
                f"  Sintesi: {ss.summary}",
                "",
                "  Eventi identificati:",
            ]

            for ev in ss.events:
                impact_str = f"{ev.impact:+.1f}"
                conf_str = f"{ev.confidence:.0%}"
                lines.append(
                    f"    [{ev.team.upper():4}] {ev.event_type:15} "
                    f"impatto {impact_str:5} conf {conf_str:5} "
                    f"— {ev.description}"
                )

            lines += [
                "",
                "── PROBABILITÀ CORRETTE (base + sesto senso) ──────────",
                f"  Home Win : {adj.home_win:.1%}  ({adj.home_delta:+.1%})",
                f"  Draw     : {adj.draw:.1%}  ({adj.draw_delta:+.1%})",
                f"  Away Win : {adj.away_win:.1%}  ({adj.away_delta:+.1%})",
                f"  Segnale  : {adj.signal}",
            ]

        # Probabilità qualificazione (partite di ritorno)
        if self.qualification_probs:
            qp = self.qualification_probs
            lines += [
                "",
                "── PROBABILITÀ QUALIFICAZIONE (aggregato) ──────────────",
                f"  {self.home:<22}: {qp.get('home_qualifies', 0):.1%}",
                f"  {self.away:<22}: {qp.get('away_qualifies', 0):.1%}",
            ]
            if qp.get("goes_to_et", 0) > 0.01:
                lines.append(f"  Supplementari             : {qp.get('goes_to_et', 0):.1%}")

        # Mercati gol
        if self.goal_markets:
            gm = self.goal_markets
            lines += [
                "",
                "── MERCATI GOL (Poisson) ───────────────────────────────",
                f"  Gol attesi: {gm.get('expected_total', '?')} "
                f"(casa {gm.get('lambda_home', '?')} + ospite {gm.get('lambda_away', '?')})",
                f"  Over 1.5 : {gm.get('over_1_5', 0):.1%}  |  Under 1.5 : {gm.get('under_1_5', 0):.1%}",
                f"  Over 2.5 : {gm.get('over_2_5', 0):.1%}  |  Under 2.5 : {gm.get('under_2_5', 0):.1%}",
                f"  Over 3.5 : {gm.get('over_3_5', 0):.1%}  |  Under 3.5 : {gm.get('under_3_5', 0):.1%}",
                f"  BTTS Sì  : {gm.get('btts_yes', 0):.1%}  |  BTTS No   : {gm.get('btts_no', 0):.1%}",
            ]

        # Mercati corner
        if self.corner_markets:
            cm = self.corner_markets
            lines += [
                "",
                "── MERCATI CORNER (Poisson) ────────────────────────────",
                f"  Corner attesi: {cm.get('expected_total', '?')} "
                f"(casa {cm.get('lambda_home', '?')} + ospite {cm.get('lambda_away', '?')})",
                f"  Over  8.5 : {cm.get('over_8_5', 0):.1%}  |  Under  8.5 : {cm.get('under_8_5', 0):.1%}",
                f"  Over  9.5 : {cm.get('over_9_5', 0):.1%}  |  Under  9.5 : {cm.get('under_9_5', 0):.1%}",
                f"  Over 10.5 : {cm.get('over_10_5', 0):.1%}  |  Under 10.5 : {cm.get('under_10_5', 0):.1%}",
                f"  Over 11.5 : {cm.get('over_11_5', 0):.1%}  |  Under 11.5 : {cm.get('under_11_5', 0):.1%}",
                f"  Casa >4.5 : {cm.get('home_over_4_5', 0):.1%}  |  Casa >5.5  : {cm.get('home_over_5_5', 0):.1%}",
            ]

        # Quote di mercato e value bets
        if self.market_odds:
            lines += [
                "",
                "── QUOTE DI MERCATO ────────────────────────────────────",
                f"  Home Win : {self.market_odds.get('home_win', 'N/A')}",
                f"  Draw     : {self.market_odds.get('draw', 'N/A')}",
                f"  Away Win : {self.market_odds.get('away_win', 'N/A')}",
            ]

        if self.value_signals:
            lines += ["", "── VALUE BETS ──────────────────────────────────────────"]
            for vs in self.value_signals:
                rec = "⭐ VALUE BET" if vs["recommendation"] == "VALUE BET" else "👀 WATCH"
                lines.append(
                    f"  {rec}  {vs['market']:10}  "
                    f"nostra {vs['our_probability']:.1%} vs "
                    f"mercato {vs['market_probability']:.1%}  "
                    f"edge {vs['edge']:+.1%}  "
                    f"quota mercato: {vs['market_odd']}"
                )
        elif self.market_odds:
            lines.append("")
            lines.append("── VALUE BETS: nessun valore trovato ───────────────────")

        lines += ["", "=" * 60]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "home": self.home,
            "away": self.away,
            "match_date": self.match_date,
            "analyzed_at": self.analyzed_at,
            "base_probs": self.base_probs,
            "adjusted_probs": self.adjusted_probs.to_dict(),
            "sixth_sense": self.sixth_sense.to_dict(),
            "goal_markets": self.goal_markets,
            "value_signals": self.value_signals,
            "market_odds": self.market_odds,
        }


# ------------------------------------------------------------------
# Engine
# ------------------------------------------------------------------

class SixthSenseEngine:
    """
    Pipeline completa BAgent.

    Parametri:
        language:       lingua per la ricerca notizie (default 'it')
        country:        paese per Google News (default 'IT')
        llm_model:      modello Claude da usare per il Sesto Senso
        newsapi_key:    API key NewsAPI (opzionale)
        anthropic_key:  API key Anthropic (default da env ANTHROPIC_API_KEY)
        min_edge:       edge minimo per segnalare un value bet (default 5%)
    """

    def __init__(
        self,
        language: str = "it",
        country: str = "IT",
        llm_model: str = "claude-haiku-4-5-20251001",
        newsapi_key: Optional[str] = None,
        anthropic_key: Optional[str] = None,
        api_football_key: Optional[str] = None,
        league_id: Optional[int] = None,
        season: Optional[int] = None,
        min_edge: float = 0.05,
    ):
        self.collector = MultiSourceCollector(
            api_football_key=api_football_key or os.getenv("API_FOOTBALL_KEY"),
            league_id=league_id,
            season=season,
            newsapi_key=newsapi_key or os.getenv("NEWSAPI_KEY"),
            language=language,
            country=country,
        )

        self.analyzer = SixthSenseAnalyzer(
            api_key=anthropic_key or os.getenv("ANTHROPIC_API_KEY"),
            model=llm_model,
        )

        self.adjuster = ProbabilityAdjuster()
        self.min_edge = min_edge
        self.repo = SixthSenseRepository()

    def analyze(
        self,
        home: str,
        away: str,
        match_date: date,
        market_odds: Optional[dict] = None,
        base_probs: Optional[dict] = None,
        include_news: bool = True,
        extra_context: str = "",
        first_leg: Optional[dict] = None,
        verbose: bool = False,
    ) -> MatchAnalysisResult:
        """
        Analisi completa di una partita.

        home, away:    nomi delle squadre
        match_date:    data della partita
        market_odds:   quote del bookmaker {home_win, draw, away_win} (opzionale)
        base_probs:    probabilità base custom — se non fornite usa ClubElo
        include_news:  se False salta la raccolta notizie (più veloce)
        verbose:       stampa progress

        Ritorna MatchAnalysisResult con report() e to_dict()
        """
        analyzed_at = datetime.now(timezone.utc).isoformat()

        if verbose:
            print(f"[BAgent] Raccolta dati: {home} vs {away} ({match_date})")

        # 1. Raccolta dati
        bundle = self.collector.collect_sixth_sense(
            home=home,
            away=away,
            match_date=match_date,
            include_news=include_news,
        )

        # 2. Modello aggregato (se partita di ritorno)
        agg_model: Optional[AggregateModel] = None
        if first_leg is not None:
            agg_model = AggregateModel(
                first_leg_home_goals=first_leg.get("home_goals", 0),
                first_leg_away_goals=first_leg.get("away_goals", 0),
            )
            if verbose:
                print(f"[BAgent] Aggregato: {home} {agg_model.fl_home} - {agg_model.fl_away} {away}")

        # 3. Probabilità base: fornite → AggregateModel → ClubElo → flat
        if base_probs is None:
            if agg_model is not None:
                base_probs = agg_model.base_return_probs()
                if verbose:
                    print(f"[BAgent] Probabilità base da aggregato: {base_probs}")
            else:
                base_probs = bundle.get("elo") or {
                    "home_win": 0.40,
                    "draw": 0.28,
                    "away_win": 0.32,
                }

        # Quote reali da API-Football (se non fornite manualmente)
        if market_odds is None:
            market_odds = bundle.get("market_odds_from_api") or {}
            if market_odds and verbose:
                print(f"[BAgent] Quote da API-Football: {market_odds}")

        if verbose:
            print(f"[BAgent] Probabilità base: {base_probs}")
            print(f"[BAgent] Notizie raccolte: {bundle.get('news', {}).get('total_articles', 0)}")

        # 4. Analisi LLM
        news_prompt = bundle.get("news_prompt", "")
        # Inietta contesto aggregato nel prompt LLM (prima di extra_context)
        if agg_model is not None:
            agg_ctx = agg_model.context_description(home, away)
            news_prompt = f"=== CONTESTO AGGREGATO ===\n{agg_ctx}\n\n{news_prompt}"
        if extra_context:
            news_prompt = f"=== CONTESTO SPECIALE ===\n{extra_context}\n\n{news_prompt}"
        sixth_sense = self.analyzer.analyze(
            news_prompt=news_prompt,
            home=home,
            away=away,
            base_probs=base_probs,
        )

        if verbose:
            print(f"[BAgent] Sesto Senso: {len(sixth_sense.events)} eventi trovati")

        # 4b. Persistenza Sesto Senso nel DB
        match_date_str = match_date.isoformat() if isinstance(match_date, date) else str(match_date)
        try:
            news_bundle = bundle.get("news") or {}
            if news_bundle:
                n_art = self.repo.save_news(news_bundle, home, away, match_date_str)
                if verbose:
                    print(f"[BAgent] Salvati {n_art} articoli nel DB")
            n_ev = self.repo.save_events(sixth_sense, home, away, match_date_str)
            if verbose:
                print(f"[BAgent] Salvati {n_ev} eventi nel DB")
        except Exception as e:
            if verbose:
                print(f"[BAgent] ⚠️  Errore salvataggio DB Sesto Senso: {e}")

        # 5. Aggiustamento probabilità
        adjusted = self.adjuster.adjust(base_probs, sixth_sense)

        # 6. Modello gol (Poisson)
        goal_model = self._build_goal_model(bundle, adjusted)
        goal_markets = goal_model.markets()

        if verbose:
            print(f"[BAgent] Goal model: {goal_model}")

        # 6b. Modello corner (Poisson)
        corner_model = self._build_corner_model(bundle, adjusted)
        corner_markets = corner_model.markets()

        if verbose:
            print(f"[BAgent] Corner model: {corner_model}")

        # 7. Probabilità qualificazione (solo partite di ritorno)
        qualification_probs = {}
        if agg_model is not None:
            qualification_probs = agg_model.qualification_probs(goal_model)
            if verbose:
                print(f"[BAgent] Qualificazione: {home} {qualification_probs['home_qualifies']:.1%} | "
                      f"{away} {qualification_probs['away_qualifies']:.1%}")

        # 8. Value bets 1X2 + gol + corner
        value_signals = []
        if market_odds:
            value_signals = self.adjuster.value_signals(
                adjusted, market_odds, min_edge=self.min_edge
            )
            goal_signals = goal_model.value_signals(
                market_odds, min_edge=self.min_edge
            )
            corner_signals = corner_model.value_signals(
                market_odds, min_edge=self.min_edge
            )
            value_signals = sorted(
                value_signals + goal_signals + corner_signals,
                key=lambda x: x["edge"],
                reverse=True,
            )

        return MatchAnalysisResult(
            home=home,
            away=away,
            match_date=match_date.isoformat(),
            analyzed_at=analyzed_at,
            base_probs=base_probs,
            adjusted_probs=adjusted,
            sixth_sense=sixth_sense,
            goal_markets=goal_markets,
            corner_markets=corner_markets,
            qualification_probs=qualification_probs,
            value_signals=value_signals,
            market_odds=market_odds or {},
            raw_data=bundle,
        )

    def _build_corner_model(self, bundle: dict, adjusted: "AdjustedProbabilities") -> CornerModel:
        """
        Costruisce il CornerModel dalla fonte migliore disponibile.

        Priorità:
          1. Statistiche corner da API-Football (teams/statistics)
          2. Fallback: win probability (stima da adjusted.home_win)
        """
        api_data = bundle.get("api_football") or {}

        home_corner_stats = api_data.get("home_corner_stats", {})
        away_corner_stats = api_data.get("away_corner_stats", {})

        if home_corner_stats and away_corner_stats:
            model = CornerModel.from_api_stats(home_corner_stats, away_corner_stats)
            # Se from_api_stats ha avuto dati sufficienti, usalo
            if model.lh != CornerModel.LEAGUE_AVG_HOME or model.la != CornerModel.LEAGUE_AVG_AWAY:
                return model

        return CornerModel.from_win_prob(home_win=adjusted.home_win)

    def _build_goal_model(self, bundle: dict, adjusted: "AdjustedProbabilities") -> GoalModel:
        """
        Costruisce il GoalModel dalle fonti disponibili.
        Priorità: form stats > win probability da ClubElo/adjusted.
        """
        # Prova a usare le form stats di SofaScore se disponibili
        ss = bundle.get("sofascore") or {}
        home_form = ss.get("home_form") or {}
        away_form = ss.get("away_form") or {}

        if home_form.get("matches", 0) >= 3 and away_form.get("matches", 0) >= 3:
            return GoalModel.from_form_stats(home_form, away_form)

        # Fallback: calibra dai da probabilità di vittoria casa
        return GoalModel.from_win_prob(home_win=adjusted.home_win)

"""
TennisEngine — pipeline BAgent per il tennis (singolare e doppio).

Flusso:
  1. Calcola P(vittoria) con Bradley-Terry + superficie + H2H
  2. Calcola mercati set (over/under 2.5 / 3.5 / 4.5)
  3. Sesto Senso: cerca notizie su infortuni, ritiri, forma
  4. Applica fattori Sesto Senso alle probabilità
  5. Identifica value bets rispetto alle quote di mercato

Utilizzo singolare:
    engine = TennisEngine()
    result = engine.analyze(
        player1="Carlos Alcaraz",    player1_rank=2,
        player2="Jannik Sinner",     player2_rank=1,
        surface="clay",
        best_of=3,
        tournament="Roland Garros",
        market_odds={"player1": 1.90, "player2": 1.90},
        include_sixth_sense=True,
        verbose=True,
    )
    print(result.report())

Utilizzo doppio:
    result = engine.analyze_doubles(
        team1=("M. Arevalo", "M. Pavić"),  team1_avg_rank=15,
        team2=("O. Luz", "R. Matos"),      team2_avg_rank=40,
        surface="hard",
        best_of=3,
        market_odds={"team1": 1.60, "team2": 2.30},
    )
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, Tuple

from services.tennis.base_model.win_model import TennisWinModel
from services.tennis.base_model.set_model import TennisSetModel
from services.tennis.sixth_sense.engine import TennisSixthSense, TennisSixthSenseResult


# ------------------------------------------------------------------
# Result container
# ------------------------------------------------------------------

@dataclass
class TennisAnalysisResult:
    player1: str
    player2: str
    surface: str
    best_of: int
    tournament: str
    analyzed_at: str
    match_type: str = "singles"     # singles | doubles

    # Probabilità
    win_probs: dict = field(default_factory=dict)
    set_markets: dict = field(default_factory=dict)

    # Sesto Senso
    sixth_sense: Optional[TennisSixthSenseResult] = None

    # Value bets
    value_signals: list[dict] = field(default_factory=list)
    market_odds: dict = field(default_factory=dict)

    # Metadati modello
    player1_rank: int = 0
    player2_rank: int = 0
    h2h: Optional[Tuple[int, int]] = None

    def report(self) -> str:
        p1 = self.player1
        p2 = self.player2

        lines = [
            "=" * 62,
            f"  {p1.upper()} vs {p2.upper()}",
        ]
        if self.tournament:
            lines.append(f"  {self.tournament}  |  {self.surface.upper()}  |  Best of {self.best_of}")
        else:
            lines.append(f"  {self.surface.upper()}  |  Best of {self.best_of}")
        if self.player1_rank and self.player2_rank:
            lines.append(f"  Ranking: #{self.player1_rank} vs #{self.player2_rank}")
        lines += ["=" * 62, ""]

        # Probabilità
        lines += [
            "── PROBABILITÀ VITTORIA ────────────────────────────────",
            f"  {p1:<28}: {self.win_probs.get('player1', 0):.1%}",
            f"  {p2:<28}: {self.win_probs.get('player2', 0):.1%}",
        ]
        if self.h2h:
            lines.append(f"  H2H: {p1} {self.h2h[0]} - {self.h2h[1]} {p2}")
        lines.append("")

        # Sesto Senso
        ss = self.sixth_sense
        if ss and ss.status == "OK" and ss.events:
            lines += [
                "── SESTO SENSO ─────────────────────────────────────────",
                f"  Confidenza: {ss.overall_confidence:.0%}",
                f"  {ss.summary}",
                f"  Fattore {p1}: {ss.p1_factor:+.0%}",
                f"  Fattore {p2}: {ss.p2_factor:+.0%}",
                "",
            ]
            for ev in ss.events:
                sign = "+" if ev.impact > 0 else ""
                lines.append(f"    [{ev.player}] {ev.event_type} {sign}{ev.impact:.0f} ({ev.confidence:.0%}) — {ev.description}")
            lines.append("")
        elif ss and ss.status == "NO_NEWS":
            lines += ["── SESTO SENSO: nessuna notizia trovata ───────────────", ""]

        # Mercati set
        sm = self.set_markets
        if self.best_of == 3:
            lines += [
                "── MERCATI SET (Best of 3) ─────────────────────────────",
                f"  {p1} 2-0 : {sm.get('p1_2_0', 0):.1%}  |  {p2} 2-0 : {sm.get('p2_2_0', 0):.1%}",
                f"  {p1} 2-1 : {sm.get('p1_2_1', 0):.1%}  |  {p2} 2-1 : {sm.get('p2_2_1', 0):.1%}",
                f"  Over 2.5 set  : {sm.get('over_2_5_sets', 0):.1%}  |  Under 2.5 : {sm.get('under_2_5_sets', 0):.1%}",
                f"  Set attesi    : {sm.get('expected_sets', 0):.2f}",
                "",
            ]
        else:
            lines += [
                "── MERCATI SET (Best of 5) ─────────────────────────────",
                f"  {p1} 3-0 : {sm.get('p1_3_0', 0):.1%}  |  {p2} 3-0 : {sm.get('p2_3_0', 0):.1%}",
                f"  {p1} 3-1 : {sm.get('p1_3_1', 0):.1%}  |  {p2} 3-1 : {sm.get('p2_3_1', 0):.1%}",
                f"  {p1} 3-2 : {sm.get('p1_3_2', 0):.1%}  |  {p2} 3-2 : {sm.get('p2_3_2', 0):.1%}",
                f"  Over 3.5 set  : {sm.get('over_3_5_sets', 0):.1%}  |  Under 3.5 : {sm.get('under_3_5_sets', 0):.1%}",
                f"  Over 4.5 set  : {sm.get('over_4_5_sets', 0):.1%}  |  Under 4.5 : {sm.get('under_4_5_sets', 0):.1%}",
                f"  Set attesi    : {sm.get('expected_sets', 0):.2f}",
                "",
            ]

        # Quote di mercato
        if self.market_odds:
            lines += [
                "── QUOTE DI MERCATO ────────────────────────────────────",
                f"  {p1:<28}: {self.market_odds.get('player1', 'N/A')}",
                f"  {p2:<28}: {self.market_odds.get('player2', 'N/A')}",
            ]
            for key in ["over_2_5_sets", "under_2_5_sets",
                        "over_3_5_sets", "under_3_5_sets",
                        "over_4_5_sets", "under_4_5_sets"]:
                if key in self.market_odds:
                    lines.append(f"  {key:<28}: {self.market_odds[key]}")
            lines.append("")

        # Value bets
        if self.value_signals:
            lines += ["── VALUE BETS ──────────────────────────────────────────"]
            for vs in self.value_signals:
                rec = "⭐ VALUE BET" if vs["recommendation"] == "VALUE BET" else "👀 WATCH"
                edge_pct = f"{vs['edge']:+.1%}"
                lines.append(
                    f"  {rec}  {vs['market']:<22}  "
                    f"nostra {vs['our_probability']:.1%} vs "
                    f"mercato {vs['market_probability']:.1%}  "
                    f"edge {edge_pct}  quota: {vs['market_odd']}"
                )
        elif self.market_odds:
            lines.append("── VALUE BETS: nessun valore trovato ───────────────────")

        lines += ["", "=" * 62]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "player1":      self.player1,
            "player2":      self.player2,
            "surface":      self.surface,
            "best_of":      self.best_of,
            "tournament":   self.tournament,
            "match_type":   self.match_type,
            "player1_rank": self.player1_rank,
            "player2_rank": self.player2_rank,
            "analyzed_at":  self.analyzed_at,
            "win_probs":    self.win_probs,
            "set_markets":  self.set_markets,
            "value_signals":self.value_signals,
            "market_odds":  self.market_odds,
            "sixth_sense":  self.sixth_sense.to_dict() if self.sixth_sense else None,
        }


# ------------------------------------------------------------------
# Engine
# ------------------------------------------------------------------

class TennisEngine:
    """
    Pipeline BAgent per il tennis (singolare e doppio).
    """

    def __init__(
        self,
        min_edge: float = 0.05,
        anthropic_key: Optional[str] = None,
        newsapi_key: Optional[str] = None,
        llm_model: str = "claude-haiku-4-5-20251001",
    ):
        self.min_edge = min_edge
        self._ss = TennisSixthSense(
            anthropic_key=anthropic_key or os.getenv("ANTHROPIC_API_KEY"),
            newsapi_key=newsapi_key or os.getenv("NEWSAPI_KEY"),
            llm_model=llm_model,
        )

    def analyze(
        self,
        player1: str,
        player1_rank: int,
        player2: str,
        player2_rank: int,
        surface: str = "hard",
        best_of: int = 3,
        tournament: str = "",
        match_date: Optional[str] = None,
        h2h: Optional[Tuple[int, int]] = None,
        p1_surface_factor: float = 1.0,
        p2_surface_factor: float = 1.0,
        market_odds: Optional[dict] = None,
        include_sixth_sense: bool = True,
        verbose: bool = False,
    ) -> TennisAnalysisResult:
        """
        Analisi completa singolare.

        h2h: (vittorie p1, vittorie p2) — opzionale
        p1_surface_factor: moltiplicatore superficie (1.0 = neutro)
        """
        analyzed_at = datetime.now(timezone.utc).isoformat()

        if verbose:
            print(f"[TennisEngine] {player1} (#{player1_rank}) vs {player2} (#{player2_rank})")
            print(f"[TennisEngine] {surface.upper()}  Bo{best_of}  {tournament}")

        # Sesto Senso (prima, perché può modificare i fattori superficie)
        ss_result: Optional[TennisSixthSenseResult] = None
        if include_sixth_sense:
            ss_result = self._ss.analyze(
                player1=player1,
                player2=player2,
                surface=surface,
                tournament=tournament,
                match_date=match_date,
                verbose=verbose,
            )
            # Applica fattori Sesto Senso ai surface factors
            if ss_result and ss_result.status == "OK":
                p1_surface_factor *= ss_result.p1_factor
                p2_surface_factor *= ss_result.p2_factor

        # Modello vittoria
        win_model = TennisWinModel(
            player1_rank=player1_rank,
            player2_rank=player2_rank,
            surface=surface,
            h2h=h2h,
            p1_surface_factor=p1_surface_factor,
            p2_surface_factor=p2_surface_factor,
        )
        win_probs = win_model.win_probs()

        if verbose:
            print(f"[TennisEngine] P1={win_probs['player1']:.1%}  P2={win_probs['player2']:.1%}")

        # Modello set
        set_model = TennisSetModel(p1_win_prob=win_probs["player1"], best_of=best_of)
        set_markets = set_model.markets()

        # Value bets
        value_signals: list[dict] = []
        if market_odds:
            win_signals = win_model.value_signals(market_odds, min_edge=self.min_edge)
            set_signals = set_model.value_signals(market_odds, min_edge=self.min_edge)
            value_signals = sorted(
                win_signals + set_signals,
                key=lambda x: x["edge"], reverse=True,
            )

        return TennisAnalysisResult(
            player1=player1,
            player2=player2,
            surface=surface,
            best_of=best_of,
            tournament=tournament,
            analyzed_at=analyzed_at,
            match_type="singles",
            win_probs=win_probs,
            set_markets=set_markets,
            sixth_sense=ss_result,
            value_signals=value_signals,
            market_odds=market_odds or {},
            player1_rank=player1_rank,
            player2_rank=player2_rank,
            h2h=h2h,
        )

    def analyze_doubles(
        self,
        team1: Tuple[str, str],
        team2: Tuple[str, str],
        team1_avg_rank: int,
        team2_avg_rank: int,
        surface: str = "hard",
        best_of: int = 3,
        tournament: str = "",
        match_date: Optional[str] = None,
        h2h: Optional[Tuple[int, int]] = None,
        market_odds: Optional[dict] = None,
        include_sixth_sense: bool = True,
        verbose: bool = False,
    ) -> TennisAnalysisResult:
        """
        Analisi doppio.
        team1/team2: tuple (nome_giocatore1, nome_giocatore2)
        team1_avg_rank / team2_avg_rank: ranking medio del coppia

        Il modello tratta la coppia come un singolo "giocatore" con rank medio.
        Il Sesto Senso cerca notizie su entrambi i giocatori di ogni coppia.
        """
        # Nome coppia = "Cognome1 / Cognome2"
        p1_name = f"{team1[0]} / {team1[1]}"
        p2_name = f"{team2[0]} / {team2[1]}"

        if verbose:
            print(f"[TennisEngine] DOPPIO: {p1_name} vs {p2_name}")

        # Per il Sesto Senso cerchiamo i singoli giocatori
        ss_result: Optional[TennisSixthSenseResult] = None
        if include_sixth_sense:
            # Cerca notizie su giocatore 1 di team1 vs giocatore 1 di team2
            # (approssimazione: ci interessano infortuni dei giocatori chiave)
            ss_result = self._ss.analyze(
                player1=team1[0],
                player2=team2[0],
                surface=surface,
                tournament=tournament,
                match_date=match_date,
                verbose=verbose,
            )

        p1_sf = ss_result.p1_factor if (ss_result and ss_result.status == "OK") else 1.0
        p2_sf = ss_result.p2_factor if (ss_result and ss_result.status == "OK") else 1.0

        win_model = TennisWinModel(
            player1_rank=team1_avg_rank,
            player2_rank=team2_avg_rank,
            surface=surface,
            h2h=h2h,
            p1_surface_factor=p1_sf,
            p2_surface_factor=p2_sf,
        )
        win_probs = win_model.win_probs()

        set_model = TennisSetModel(p1_win_prob=win_probs["player1"], best_of=best_of)
        set_markets = set_model.markets()

        value_signals: list[dict] = []
        if market_odds:
            win_signals = win_model.value_signals(market_odds, min_edge=self.min_edge)
            set_signals = set_model.value_signals(market_odds, min_edge=self.min_edge)
            value_signals = sorted(win_signals + set_signals, key=lambda x: x["edge"], reverse=True)

        analyzed_at = datetime.now(timezone.utc).isoformat()

        return TennisAnalysisResult(
            player1=p1_name,
            player2=p2_name,
            surface=surface,
            best_of=best_of,
            tournament=tournament,
            analyzed_at=analyzed_at,
            match_type="doubles",
            win_probs=win_probs,
            set_markets=set_markets,
            sixth_sense=ss_result,
            value_signals=value_signals,
            market_odds=market_odds or {},
            player1_rank=team1_avg_rank,
            player2_rank=team2_avg_rank,
            h2h=h2h,
        )

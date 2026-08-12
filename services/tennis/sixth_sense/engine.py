"""
TennisEngine — pipeline BAgent per il tennis.

Flusso:
  1. Calcola P(vittoria) con Bradley-Terry + superficie + H2H
  2. Calcola mercati set (2.5 / 3.5 / 4.5)
  3. Raccoglie notizie opzionalmente (stesso SixthSenseAnalyzer del calcio)
  4. Identifica value bets rispetto alle quote di mercato

Utilizzo:
    engine = TennisEngine()
    result = engine.analyze(
        player1="Carlos Alcaraz",    player1_rank=2,
        player2="Jannik Sinner",     player2_rank=1,
        surface="clay",
        best_of=3,
        market_odds={"player1": 1.90, "player2": 1.90}
    )
    print(result.report())
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional, Tuple

from services.tennis.base_model.win_model import TennisWinModel
from services.tennis.base_model.set_model import TennisSetModel


# ------------------------------------------------------------------
# Result container
# ------------------------------------------------------------------

@dataclass
class TennisAnalysisResult:
    player1: str
    player2: str
    surface: str
    best_of: int
    analyzed_at: str

    # Probabilità
    win_probs: dict           # {"player1": float, "player2": float}
    set_markets: dict         # da TennisSetModel.markets()

    # Value bets
    value_signals: list[dict] = field(default_factory=list)
    market_odds: dict         = field(default_factory=dict)

    # Metadati modello
    player1_rank: int = 0
    player2_rank: int = 0
    h2h: Optional[Tuple[int, int]] = None

    def report(self) -> str:
        lines = [
            "=" * 60,
            f"  {self.player1.upper()} vs {self.player2.upper()}",
            f"  Superficie: {self.surface.upper()}  |  Best of {self.best_of}",
            f"  Ranking: #{self.player1_rank} vs #{self.player2_rank}",
            "=" * 60,
            "",
            "── PROBABILITÀ VITTORIA (Bradley-Terry) ───────────────",
            f"  {self.player1:<25}: {self.win_probs['player1']:.1%}",
            f"  {self.player2:<25}: {self.win_probs['player2']:.1%}",
        ]

        if self.h2h:
            p1w, p2w = self.h2h
            lines.append(f"  H2H: {self.player1} {p1w} - {p2w} {self.player2}")

        lines.append("")

        # Mercati set
        sm = self.set_markets
        if self.best_of == 3:
            lines += [
                "── MERCATI SET (Best of 3) ─────────────────────────────",
                f"  {self.player1} 2-0 : {sm.get('p1_2_0', 0):.1%}  |  {self.player2} 2-0 : {sm.get('p2_2_0', 0):.1%}",
                f"  {self.player1} 2-1 : {sm.get('p1_2_1', 0):.1%}  |  {self.player2} 2-1 : {sm.get('p2_2_1', 0):.1%}",
                f"  Over 2.5 set  : {sm.get('over_2_5_sets', 0):.1%}  (3 set)  |  Under 2.5 : {sm.get('under_2_5_sets', 0):.1%}  (2 set)",
                f"  Set attesi    : {sm.get('expected_sets', 0):.2f}",
            ]
        else:
            lines += [
                "── MERCATI SET (Best of 5) ─────────────────────────────",
                f"  {self.player1} 3-0 : {sm.get('p1_3_0', 0):.1%}  |  {self.player2} 3-0 : {sm.get('p2_3_0', 0):.1%}",
                f"  {self.player1} 3-1 : {sm.get('p1_3_1', 0):.1%}  |  {self.player2} 3-1 : {sm.get('p2_3_1', 0):.1%}",
                f"  {self.player1} 3-2 : {sm.get('p1_3_2', 0):.1%}  |  {self.player2} 3-2 : {sm.get('p2_3_2', 0):.1%}",
                f"  Over 3.5 set  : {sm.get('over_3_5_sets', 0):.1%}  |  Under 3.5 : {sm.get('under_3_5_sets', 0):.1%}",
                f"  Over 4.5 set  : {sm.get('over_4_5_sets', 0):.1%}  |  Under 4.5 : {sm.get('under_4_5_sets', 0):.1%}",
                f"  Set attesi    : {sm.get('expected_sets', 0):.2f}",
            ]

        # Quote di mercato
        if self.market_odds:
            lines += [
                "",
                "── QUOTE DI MERCATO ────────────────────────────────────",
                f"  {self.player1:<25}: {self.market_odds.get('player1', 'N/A')}",
                f"  {self.player2:<25}: {self.market_odds.get('player2', 'N/A')}",
            ]
            for key in ["over_2_5_sets", "under_2_5_sets",
                        "over_3_5_sets", "under_3_5_sets",
                        "over_4_5_sets", "under_4_5_sets"]:
                if key in self.market_odds:
                    lines.append(f"  {key:<25}: {self.market_odds[key]}")

        # Value bets
        if self.value_signals:
            lines += ["", "── VALUE BETS ──────────────────────────────────────────"]
            for vs in self.value_signals:
                rec = "⭐ VALUE BET" if vs["recommendation"] == "VALUE BET" else "👀 WATCH"
                lines.append(
                    f"  {rec}  {vs['market']:<20}  "
                    f"nostra {vs['our_probability']:.1%} vs "
                    f"mercato {vs['market_probability']:.1%}  "
                    f"edge {vs['edge']:+.1%}  "
                    f"quota: {vs['market_odd']}"
                )
        elif self.market_odds:
            lines += ["", "── VALUE BETS: nessun valore trovato ───────────────────"]

        lines += ["", "=" * 60]
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "player1":        self.player1,
            "player2":        self.player2,
            "surface":        self.surface,
            "best_of":        self.best_of,
            "player1_rank":   self.player1_rank,
            "player2_rank":   self.player2_rank,
            "analyzed_at":    self.analyzed_at,
            "win_probs":      self.win_probs,
            "set_markets":    self.set_markets,
            "value_signals":  self.value_signals,
            "market_odds":    self.market_odds,
        }


# ------------------------------------------------------------------
# Engine
# ------------------------------------------------------------------

class TennisEngine:
    """
    Pipeline BAgent per il tennis.

    Parametri:
        min_edge: edge minimo per segnalare value bet (default 5%)
    """

    def __init__(self, min_edge: float = 0.05):
        self.min_edge = min_edge

    def analyze(
        self,
        player1: str,
        player1_rank: int,
        player2: str,
        player2_rank: int,
        surface: str = "hard",
        best_of: int = 3,
        h2h: Optional[Tuple[int, int]] = None,
        p1_surface_factor: float = 1.0,
        p2_surface_factor: float = 1.0,
        market_odds: Optional[dict] = None,
        verbose: bool = False,
    ) -> TennisAnalysisResult:
        """
        Analisi completa di un match tennis.

        player1/player2:        nomi dei giocatori
        player1_rank/player2_rank: ranking ATP/WTA
        surface:                'clay' | 'grass' | 'hard' | 'indoor'
        best_of:                3 o 5
        h2h:                    (vittorie p1, vittorie p2) — opzionale
        p1_surface_factor:      moltiplicatore forza P1 su questa superficie (1.0 = neutro)
        p2_surface_factor:      idem per P2
        market_odds:            quote bookmaker {player1, player2, over_2_5_sets, ...}
        verbose:                stampa progress
        """
        analyzed_at = datetime.now(timezone.utc).isoformat()

        if verbose:
            print(f"[TennisEngine] Analisi: {player1} (#{player1_rank}) vs {player2} (#{player2_rank})")
            print(f"[TennisEngine] Superficie: {surface}  |  Best of {best_of}")

        # 1. Modello vittoria
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
            print(f"[TennisEngine] P(vittoria): {player1} {win_probs['player1']:.1%}  |  {player2} {win_probs['player2']:.1%}")

        # 2. Modello set
        set_model = TennisSetModel(p1_win_prob=win_probs["player1"], best_of=best_of)
        set_markets = set_model.markets()

        if verbose:
            print(f"[TennisEngine] Set attesi: {set_markets.get('expected_sets')}")

        # 3. Value bets
        value_signals: list[dict] = []
        if market_odds:
            # Value bets sul vincitore
            win_signals = win_model.value_signals(market_odds, min_edge=self.min_edge)
            # Value bets sui set
            set_signals = set_model.value_signals(market_odds, min_edge=self.min_edge)
            value_signals = sorted(
                win_signals + set_signals,
                key=lambda x: x["edge"],
                reverse=True,
            )

        if verbose and value_signals:
            print(f"[TennisEngine] {len(value_signals)} value bet trovate")

        return TennisAnalysisResult(
            player1=player1,
            player2=player2,
            surface=surface,
            best_of=best_of,
            analyzed_at=analyzed_at,
            win_probs=win_probs,
            set_markets=set_markets,
            value_signals=value_signals,
            market_odds=market_odds or {},
            player1_rank=player1_rank,
            player2_rank=player2_rank,
            h2h=h2h,
        )

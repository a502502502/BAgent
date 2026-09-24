"""
services/live/live_momentum_sniper.py — In-Play Real-Time Momentum Engine & Sniper (Regola #65).

Analizza in tempo reale minute-by-minute il flusso tattico delle partite in corso:
- Intercetta i 5 trigger di picco probabilistico (Late Pressure, Assedio, Sblocco Intervallo, Fast Breakout, Tensione Sanzioni);
- Calcola la probabilità stocastica residua sui minuti rimanenti;
- Emette un 'LiveSnipeSignal' con il mercato specifico da prendere all'istante su Netwin.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional

from services.football.sixth_sense.lambda_context import MatchContext
from services.live.live_in_play_engine import (
    LiveSweetSpot,
    PricedLiveMarket,
    ResidualState,
    project_residual,
    scan_live_book,
)

@dataclass
class LiveMatchSnapshot:
    fixture_id: str
    match_name: str
    minute: int
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_corners: int = 0
    away_corners: int = 0
    home_yellow_cards: int = 0
    away_yellow_cards: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0
    pre_match_favorite: str = "EQUAL"  # 'HOME', 'AWAY', 'EQUAL'
    pre_match_odd_favorite: float = 1.60
    xg_home: Optional[float] = None
    xg_away: Optional[float] = None
    stoppage: int = 4
    odds_suspended: bool = False
    ht_home_goals: Optional[int] = None
    ht_away_goals: Optional[int] = None
    corner_avg_home: Optional[float] = None
    corner_avg_away: Optional[float] = None
    recent_shots_home: Optional[int] = None
    recent_shots_away: Optional[int] = None

@dataclass
class LiveSnipeSignal:
    fixture_id: str
    match_name: str
    trigger_type: str
    minute: int
    current_score: str
    market_to_bet_now: str
    urgency_level: str               # "🚨 ENTRA ORA (SUBITO)", "⚡ FINESTRA 3 MIN", "👀 MONITORARE"
    real_probability_pct: float
    target_odds_range: str
    tactical_rationale: str
    netwin_category_path: str
    recommended_stake_pct: float = 0.03 # 3% del bankroll per sniping in-play
    exact_selection: str = ""        # Stringa già parsabile da parse_netwin_selection
    ticket_context: str = ""         # Contesto ticket utente
    book_odd: float = 0.0
    fair_odd: float = 0.0
    edge: float = 0.0

class LiveMomentumSniper:
    """
    Sentinel di Sniping In-Play per BAgent.
    Emette un segnale solo se la quota live è nello sweet spot e la matrice residua lo paga.
    """

    MIN_SNIPE_PROBABILITY = 0.72

    def __init__(self, spot: LiveSweetSpot | None = None):
        self.spot = spot or LiveSweetSpot()

    def evaluate_live_match(
        self,
        snapshot: LiveMatchSnapshot,
        ticket_info: str = "",
        book_odds: Optional[Dict[str, float]] = None,
        context: MatchContext | None = None,
        suspended_markets: Optional[set[str]] = None,
    ) -> Optional[LiveSnipeSignal]:
        """Il migliore mercato live che passa il filtro. Senza quota non inventa un segnale."""
        found = self.scan(snapshot, book_odds, ticket_info, context, suspended_markets)
        return found[0] if found else None

    def scan(
        self,
        snapshot: LiveMatchSnapshot,
        book_odds: Optional[Dict[str, float]] = None,
        ticket_info: str = "",
        context: MatchContext | None = None,
        suspended_markets: Optional[set[str]] = None,
    ) -> List[LiveSnipeSignal]:
        state = _state_from_snapshot(snapshot, context)
        priced, _rejected = scan_live_book(
            state,
            book_odds,
            home_goals=snapshot.home_goals,
            away_goals=snapshot.away_goals,
            home_corners=snapshot.home_corners,
            away_corners=snapshot.away_corners,
            second_half_goals=_second_half_goals(snapshot),
            suspended=snapshot.odds_suspended,
            suspended_markets=suspended_markets,
            spot=self.spot,
        )
        return [_signal(snapshot, item, ticket_info) for item in priced]


def _state_from_snapshot(snapshot: LiveMatchSnapshot, context: MatchContext | None) -> ResidualState:
    return project_residual(
        snapshot.xg_home if snapshot.xg_home is not None else 1.3,
        snapshot.xg_away if snapshot.xg_away is not None else 1.1,
        snapshot.minute,
        stoppage=snapshot.stoppage,
        home_goals=snapshot.home_goals,
        away_goals=snapshot.away_goals,
        home_reds=snapshot.home_red_cards,
        away_reds=snapshot.away_red_cards,
        home_shots=snapshot.home_shots,
        away_shots=snapshot.away_shots,
        home_shots_on_target=snapshot.home_shots_on_target,
        away_shots_on_target=snapshot.away_shots_on_target,
        recent_shots_home=snapshot.recent_shots_home,
        recent_shots_away=snapshot.recent_shots_away,
        home_corners=snapshot.home_corners,
        away_corners=snapshot.away_corners,
        corner_avg_home=snapshot.corner_avg_home,
        corner_avg_away=snapshot.corner_avg_away,
        favorite=snapshot.pre_match_favorite,
        context=context,
    )


def _second_half_goals(snapshot: LiveMatchSnapshot) -> Optional[int]:
    if snapshot.ht_home_goals is not None and snapshot.ht_away_goals is not None:
        return (snapshot.home_goals - snapshot.ht_home_goals) + (snapshot.away_goals - snapshot.ht_away_goals)
    if snapshot.home_goals + snapshot.away_goals == 0 and snapshot.minute >= 46:
        return 0
    return None


def _signal(snapshot: LiveMatchSnapshot, item: PricedLiveMarket, ticket_info: str) -> LiveSnipeSignal:
    score = f"{snapshot.home_goals}-{snapshot.away_goals}"
    urgency = "🚨 ENTRA ORA (SUBITO)" if snapshot.minute >= 70 else "⚡ FINESTRA 3 MIN"
    return LiveSnipeSignal(
        fixture_id=snapshot.fixture_id,
        match_name=snapshot.match_name,
        trigger_type=item.family or "LIVE",
        minute=snapshot.minute,
        current_score=score,
        market_to_bet_now=item.market,
        exact_selection=item.market,
        ticket_context=ticket_info,
        urgency_level=urgency,
        real_probability_pct=item.probability * 100.0,
        target_odds_range=f"@ {item.book_odd:.2f}",
        tactical_rationale="; ".join(item.notes),
        netwin_category_path=_netwin_path(item.family),
        recommended_stake_pct=item.stake_pct,
        book_odd=item.book_odd,
        fair_odd=item.fair_odd,
        edge=item.edge,
    )


def _netwin_path(family: str) -> str:
    return {
        "CORNER": "Live > Angoli",
        "MULTIGOL": "Live > MultiGol",
        "COMBO": "Live > Combo",
        "NEXT_GOAL": "Live > Prossimo Gol",
        "OU": "Live > Totale Gol",
        "BTTS": "Live > Gol/NoGol",
    }.get(family, "Live")

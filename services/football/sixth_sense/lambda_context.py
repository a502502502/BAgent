"""Il sesto senso entra nella matrice dei gol, non solo nell'1X2.

Un infortunio o un corto muso cambiano quali punteggi restano vivi.
Spostare solo la probabilità di vittoria lascia le combo sullo stesso Poisson di prima.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.football.sixth_sense.analyzer import SixthSenseEvent


ROTATION_FACTOR = 0.92
LOW_MOTIVATION_FACTOR = 0.90
CORTO_MUSO_FACTOR = 0.85
DOMINANT_ATTACK = 2.20
MIN_LAMBDA = 0.15


@dataclass(frozen=True)
class MatchContext:
    slow_start: bool = False
    rotation_risk: bool = False
    low_motivation_home: bool = False
    low_motivation_away: bool = False
    corto_muso_home: bool = False
    corto_muso_away: bool = False


@dataclass(frozen=True)
class AttackProjection:
    xg_home: float
    xg_away: float
    notes: tuple[str, ...]
    veto_home_one_nil: bool
    veto_away_one_nil: bool
    veto_home_ceiling: bool
    veto_away_ceiling: bool
    veto_first_half: bool


def context_from_events(events: list[SixthSenseEvent]) -> MatchContext:
    """Traduce gli eventi già strutturati in bandiere che la matrice sa leggere."""
    slow_start = False
    rotation_risk = False
    low_home = False
    low_away = False
    corto_home = False
    corto_away = False
    for event in events:
        kind = event.event_type.strip().lower()
        if kind in {"fatigue", "rotation"}:
            rotation_risk = True
        elif kind in {"slow_start", "diesel"}:
            slow_start = True
        elif kind in {"corto_muso", "pragmatic"}:
            if event.team == "home":
                corto_home = True
            elif event.team == "away":
                corto_away = True
        elif kind == "motivation" and event.impact < 0 and event.confidence >= 0.5:
            if event.team == "home":
                low_home = True
            elif event.team == "away":
                low_away = True
    return MatchContext(
        slow_start=slow_start,
        rotation_risk=rotation_risk,
        low_motivation_home=low_home,
        low_motivation_away=low_away,
        corto_muso_home=corto_home,
        corto_muso_away=corto_away,
    )


def project_attack(xg_home: float, xg_away: float, context: MatchContext) -> AttackProjection:
    home = max(MIN_LAMBDA, xg_home)
    away = max(MIN_LAMBDA, xg_away)
    notes: list[str] = []
    if context.rotation_risk:
        home *= ROTATION_FACTOR
        away *= ROTATION_FACTOR
        notes.append("turnover: entrambi gli attacchi -8%, vietati i mercati sul primo tempo")
    if context.low_motivation_home:
        home *= LOW_MOTIVATION_FACTOR
        notes.append("motivazione bassa in casa: attacco casa -10%")
    if context.low_motivation_away:
        away *= LOW_MOTIVATION_FACTOR
        notes.append("motivazione bassa in trasferta: attacco ospite -10%")
    if context.corto_muso_home:
        home *= CORTO_MUSO_FACTOR
        notes.append("corto muso casa: attacco casa -15%, fuori le combo che muoiono sull'1-0")
    if context.corto_muso_away:
        away *= CORTO_MUSO_FACTOR
        notes.append("corto muso ospite: attacco ospite -15%, fuori le combo che muoiono sullo 0-1")
    if context.slow_start:
        notes.append("avvio lento: fuori i mercati che possono morire al 45'")
    home = max(MIN_LAMBDA, home)
    away = max(MIN_LAMBDA, away)
    return AttackProjection(
        xg_home=home,
        xg_away=away,
        notes=tuple(notes),
        veto_home_one_nil=context.corto_muso_home,
        veto_away_one_nil=context.corto_muso_away,
        veto_home_ceiling=home >= DOMINANT_ATTACK,
        veto_away_ceiling=away >= DOMINANT_ATTACK,
        veto_first_half=context.slow_start or context.rotation_risk,
    )

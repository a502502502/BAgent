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
# Priors conservativi, non un fit sulla stagione: 8% di lambda per punto di impatto a confidenza 1.
INJURY_RATE = 0.08
INJURY_CAP = 0.25
INJURY_FLOOR = 0.75
SEVERE_CARDS_PER_GAME = 5.2
REFEREE_ATTACK_BOOST = 1.03
AGGREGATE_MARGIN = 2
AGGREGATE_MANAGE = 0.90
AGGREGATE_CHASE = 1.10
AGGREGATE_LEAK = 1.15
CORNER_DOMINANT_BOOST = 1.12
CORNER_PARKED_FACTOR = 0.85

_DEFENSIVE = (
    "portiere",
    "difensor",
    "centrale",
    "terzino",
    "stopper",
    "keeper",
    "goalkeeper",
    "defender",
)


@dataclass(frozen=True)
class FactorSet:
    """Moltiplicatori usati sui gol attesi. I default sono i prior, non un fit."""

    rotation: float = ROTATION_FACTOR
    low_motivation: float = LOW_MOTIVATION_FACTOR
    corto_muso: float = CORTO_MUSO_FACTOR
    injury_scale: float = 1.0


def scale_attack_factor(factor: float, injury_scale: float) -> float:
    """Scala il taglio già calcolato sull'infortunio. 1.0 lascia il prior."""
    if factor >= 1.0:
        return 1.0
    return min(1.0, max(INJURY_FLOOR, factor * injury_scale))


@dataclass(frozen=True)
class MatchContext:
    slow_start: bool = False
    rotation_risk: bool = False
    low_motivation_home: bool = False
    low_motivation_away: bool = False
    corto_muso_home: bool = False
    corto_muso_away: bool = False
    attack_factor_home: float = 1.0
    attack_factor_away: float = 1.0
    leak_to_home: float = 1.0
    leak_to_away: float = 1.0
    unscoped_injury: bool = False
    referee_cards_per_game: float | None = None
    referee_style: str | None = None
    first_leg_home: int | None = None
    first_leg_away: int | None = None


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
    base_home: float = 0.0
    base_away: float = 0.0
    veto_sanction: bool = False
    veto_chase_home: bool = False
    veto_chase_away: bool = False


@dataclass(frozen=True)
class CornerProjection:
    corners_home: float
    corners_away: float
    notes: tuple[str, ...]
    base_home: float
    base_away: float


def events_from_mappings(rows: list[dict] | None) -> list[SixthSenseEvent]:
    """Accetta gli eventi già salvati sul candidato, senza richiamare il modello."""
    events: list[SixthSenseEvent] = []
    for row in rows or []:
        events.append(
            SixthSenseEvent(
                team=str(row.get("team", "")),
                event_type=str(row.get("event_type", "other")),
                description=str(row.get("description", "")),
                impact=float(row.get("impact", 0.0)),
                confidence=float(row.get("confidence", 0.0)),
                source_hint=str(row.get("source_hint", "")),
            )
        )
    return events


def _sides(team: str) -> tuple[str, ...]:
    if team == "both":
        return ("home", "away")
    if team in {"home", "away"}:
        return (team,)
    return ()


def _injury_cut(impact: float, confidence: float) -> float:
    if impact >= 0 or confidence < 0.5:
        return 0.0
    return min(INJURY_CAP, abs(impact) * confidence * INJURY_RATE)


def context_from_events(events: list[SixthSenseEvent]) -> MatchContext:
    """Traduce gli eventi già strutturati in bandiere che la matrice sa leggere."""
    slow_start = False
    rotation_risk = False
    low_home = False
    low_away = False
    corto_home = False
    corto_away = False
    attack_home = 1.0
    attack_away = 1.0
    leak_home = 1.0
    leak_away = 1.0
    for event in events:
        kind = event.event_type.strip().lower()
        sides = _sides(event.team)
        if kind in {"fatigue", "rotation"}:
            rotation_risk = True
        elif kind in {"slow_start", "diesel"}:
            slow_start = True
        elif kind in {"corto_muso", "pragmatic"}:
            corto_home = corto_home or "home" in sides
            corto_away = corto_away or "away" in sides
        elif kind == "motivation" and event.impact < 0 and event.confidence >= 0.5:
            low_home = low_home or "home" in sides
            low_away = low_away or "away" in sides
        elif kind in {"injury", "suspension"}:
            cut = _injury_cut(event.impact, event.confidence)
            if cut <= 0:
                continue
            defensive = any(token in event.description.lower() for token in _DEFENSIVE)
            for side in sides:
                if defensive and side == "home":
                    leak_away *= 1.0 + cut
                elif defensive and side == "away":
                    leak_home *= 1.0 + cut
                elif side == "home":
                    attack_home *= 1.0 - cut
                elif side == "away":
                    attack_away *= 1.0 - cut
    return MatchContext(
        slow_start=slow_start,
        rotation_risk=rotation_risk,
        low_motivation_home=low_home,
        low_motivation_away=low_away,
        corto_muso_home=corto_home,
        corto_muso_away=corto_away,
        attack_factor_home=max(INJURY_FLOOR, attack_home),
        attack_factor_away=max(INJURY_FLOOR, attack_away),
        leak_to_home=min(1.0 + INJURY_CAP, leak_home),
        leak_to_away=min(1.0 + INJURY_CAP, leak_away),
    )


def context_from_signals(
    flags: list[str] | None,
    events: list[SixthSenseEvent] | None,
    xg_home: float,
    xg_away: float,
) -> MatchContext:
    """Unisce gli eventi strutturati alle bandiere già usate dalla pipeline."""
    base = context_from_events(events or [])
    names = {flag.strip().upper() for flag in (flags or [])}
    low_home = base.low_motivation_home
    low_away = base.low_motivation_away
    unscoped_injury = False
    if "LOW_MOTIVATION" in names or "DEAD_RUBBER" in names:
        if xg_home > xg_away:
            low_home = True
        elif xg_away > xg_home:
            low_away = True
    if "INJURY_ALARM" in names and base.attack_factor_home == 1.0 and base.attack_factor_away == 1.0 and base.leak_to_home == 1.0 and base.leak_to_away == 1.0:
        unscoped_injury = True
    return MatchContext(
        slow_start=base.slow_start or "SLOW_START" in names or "DIESEL_TEMPO" in names,
        rotation_risk=base.rotation_risk or "ROTATION_RISK" in names or "MIDWEEK_CUP" in names,
        low_motivation_home=low_home,
        low_motivation_away=low_away,
        corto_muso_home=base.corto_muso_home,
        corto_muso_away=base.corto_muso_away,
        attack_factor_home=base.attack_factor_home,
        attack_factor_away=base.attack_factor_away,
        leak_to_home=base.leak_to_home,
        leak_to_away=base.leak_to_away,
        unscoped_injury=unscoped_injury,
        referee_cards_per_game=base.referee_cards_per_game,
        referee_style=base.referee_style,
        first_leg_home=base.first_leg_home,
        first_leg_away=base.first_leg_away,
    )


def referee_band(context: MatchContext) -> str:
    """severe, permissive o unknown. Senza profilo non si inventa un arbitro."""
    style = (context.referee_style or "").strip().lower()
    if style in {"severe", "severo"}:
        return "severe"
    if style in {"permissive", "permissivo"}:
        return "permissive"
    cards = context.referee_cards_per_game
    if cards is None:
        return "unknown"
    if cards > SEVERE_CARDS_PER_GAME:
        return "severe"
    return "permissive"


def aggregate_margin(context: MatchContext) -> int | None:
    """Gol dell'andata dal punto di vista di questa gara. Manca un numero: niente margine."""
    if context.first_leg_home is None or context.first_leg_away is None:
        return None
    return context.first_leg_home - context.first_leg_away


def _dominant_side(context: MatchContext, xg_home: float | None, xg_away: float | None) -> str | None:
    if context.corto_muso_home and not context.corto_muso_away:
        return "home"
    if context.corto_muso_away and not context.corto_muso_home:
        return "away"
    if xg_home is None or xg_away is None:
        return None
    if xg_home >= DOMINANT_ATTACK and xg_home > xg_away:
        return "home"
    if xg_away >= DOMINANT_ATTACK and xg_away > xg_home:
        return "away"
    return None


def project_corners(
    corners_home: float | None,
    corners_away: float | None,
    context: MatchContext,
    xg_home: float | None = None,
    xg_away: float | None = None,
) -> CornerProjection:
    """La squadra che schiaccia produce più corner. Senza medie si resta al base."""
    if corners_home is None or corners_away is None:
        base_home = float(corners_home or 0.0)
        base_away = float(corners_away or 0.0)
        return CornerProjection(base_home, base_away, ("corner non forniti: proiezione base",), base_home, base_away)
    home = float(corners_home)
    away = float(corners_away)
    notes: list[str] = []
    side = _dominant_side(context, xg_home, xg_away)
    if side == "home":
        home *= CORNER_DOMINANT_BOOST
        away *= CORNER_PARKED_FACTOR
        notes.append("attacco dominante casa: corner casa +12%, ospite arroccato -15%")
    elif side == "away":
        away *= CORNER_DOMINANT_BOOST
        home *= CORNER_PARKED_FACTOR
        notes.append("attacco dominante ospite: corner ospite +12%, casa arroccata -15%")
    return CornerProjection(home, away, tuple(notes), float(corners_home), float(corners_away))


def market_context_veto(market: str, projection: AttackProjection) -> str | None:
    """Veti che non dipendono dalla matrice dei punteggi. Senza bandiera non scattano."""
    name = market.lower()
    if projection.veto_sanction and "under" in name and ("cartellin" in name or "card" in name):
        return "arbitro severo: under cartellini"
    if projection.veto_sanction and "under" in name:
        return "arbitro severo: combo conservativa esposta all'uomo in meno"
    if projection.veto_chase_home and ("1x" in name or "under" in name):
        return "ritorno: la casa deve ribaltare il margine, fuori la non-sconfitta e il catenaccio"
    if projection.veto_chase_away and ("x2" in name or "under" in name):
        return "ritorno: l'ospite deve ribaltare il margine, fuori la non-sconfitta e il catenaccio"
    return None


def project_attack(
    xg_home: float,
    xg_away: float,
    context: MatchContext,
    factors: FactorSet | None = None,
) -> AttackProjection:
    factors = factors or FactorSet()
    home = max(MIN_LAMBDA, xg_home)
    away = max(MIN_LAMBDA, xg_away)
    notes: list[str] = []
    if context.rotation_risk:
        home *= factors.rotation
        away *= factors.rotation
        notes.append(
            f"turnover: entrambi gli attacchi -{1.0 - factors.rotation:.0%}, vietati i mercati sul primo tempo"
        )
    if context.low_motivation_home:
        home *= factors.low_motivation
        notes.append(f"motivazione bassa in casa: attacco casa -{1.0 - factors.low_motivation:.0%}")
    if context.low_motivation_away:
        away *= factors.low_motivation
        notes.append(f"motivazione bassa in trasferta: attacco ospite -{1.0 - factors.low_motivation:.0%}")
    if context.corto_muso_home:
        home *= factors.corto_muso
        notes.append("corto muso casa: attacco casa ridotto, fuori le combo che muoiono sull'1-0")
    if context.corto_muso_away:
        away *= factors.corto_muso
        notes.append("corto muso ospite: attacco ospite ridotto, fuori le combo che muoiono sullo 0-1")
    attack_home = scale_attack_factor(context.attack_factor_home, factors.injury_scale)
    attack_away = scale_attack_factor(context.attack_factor_away, factors.injury_scale)
    if attack_home < 1.0:
        home *= attack_home
        notes.append(f"assenza offensiva casa: attacco casa {(1.0 - attack_home):.0%} in meno")
    if attack_away < 1.0:
        away *= attack_away
        notes.append(f"assenza offensiva ospite: attacco ospite {(1.0 - attack_away):.0%} in meno")
    if context.leak_to_away > 1.0:
        away *= context.leak_to_away
        notes.append(f"difesa casa incompleta: attacco ospite +{(context.leak_to_away - 1.0):.0%}")
    if context.leak_to_home > 1.0:
        home *= context.leak_to_home
        notes.append(f"difesa ospite incompleta: attacco casa +{(context.leak_to_home - 1.0):.0%}")
    if context.unscoped_injury:
        notes.append("allarme infortuni senza squadra: i gol attesi restano quelli di partenza")
    if context.slow_start:
        notes.append("avvio lento: fuori i mercati che possono morire al 45'")
    veto_sanction = False
    band = referee_band(context)
    if band == "severe":
        home *= REFEREE_ATTACK_BOOST
        away *= REFEREE_ATTACK_BOOST
        veto_sanction = True
        notes.append("arbitro severo: entrambi gli attacchi +3%, fuori under e catenaccio")
    margin = aggregate_margin(context)
    veto_chase_home = False
    veto_chase_away = False
    if margin is not None and margin >= AGGREGATE_MARGIN:
        home *= AGGREGATE_MANAGE * AGGREGATE_LEAK
        away *= AGGREGATE_CHASE
        veto_chase_away = True
        notes.append("andata: casa avanti di 2+, gestisce; ospite deve inseguire")
    elif margin is not None and margin <= -AGGREGATE_MARGIN:
        away *= AGGREGATE_MANAGE * AGGREGATE_LEAK
        home *= AGGREGATE_CHASE
        veto_chase_home = True
        notes.append("andata: ospite avanti di 2+, gestisce; casa deve inseguire")
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
        base_home=xg_home,
        base_away=xg_away,
        veto_sanction=veto_sanction,
        veto_chase_home=veto_chase_home,
        veto_chase_away=veto_chase_away,
    )

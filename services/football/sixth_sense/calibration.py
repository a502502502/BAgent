"""Due storici. Quello esterno apre la finestra, quello interno sposta i fattori.

Le partite scaricate dicono quando una squadra ha già chiuso 3 gare.
L'archivio interno, partita dopo partita, pesa sul sesto senso: 1% a gara
chiusa e confrontabile, con tetto al 30%. Il resto resta il prior.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path

from services.database.schema import DB_PATH
from services.football.sixth_sense.analyzer import SixthSenseEvent
from services.football.sixth_sense.lambda_context import (
    CORTO_MUSO_FACTOR,
    LOW_MOTIVATION_FACTOR,
    ROTATION_FACTOR,
    FactorSet,
    MatchContext,
)

MIN_GROUP = 8
MIN_PLAYED_BEFORE = 3
# Ogni partita interna chiusa sposta il fattore dell'1%, mai oltre il 30%.
INTERNAL_WEIGHT_PER_MATCH = 0.01
INTERNAL_WEIGHT_CAP = 0.30
DECAY_FULL_DAYS = 45
DECAY_HALF_DAYS = 90

_DDL = """
CREATE TABLE IF NOT EXISTS sixth_sense_samples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season TEXT NOT NULL,
    match_date TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    fixture_id INTEGER,
    base_xg_home REAL NOT NULL,
    base_xg_away REAL NOT NULL,
    projected_xg_home REAL NOT NULL,
    projected_xg_away REAL NOT NULL,
    rotation_risk INTEGER NOT NULL DEFAULT 0,
    slow_start INTEGER NOT NULL DEFAULT 0,
    low_motivation_home INTEGER NOT NULL DEFAULT 0,
    low_motivation_away INTEGER NOT NULL DEFAULT 0,
    corto_muso_home INTEGER NOT NULL DEFAULT 0,
    corto_muso_away INTEGER NOT NULL DEFAULT 0,
    attack_factor_home REAL NOT NULL DEFAULT 1,
    attack_factor_away REAL NOT NULL DEFAULT 1,
    leak_to_home REAL NOT NULL DEFAULT 1,
    leak_to_away REAL NOT NULL DEFAULT 1,
    actual_home_goals INTEGER,
    actual_away_goals INTEGER,
    settled_at TEXT,
    UNIQUE(season, match_date, home_team, away_team)
);
CREATE TABLE IF NOT EXISTS sixth_sense_factor_fits (
    season TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    prior REAL NOT NULL,
    fitted REAL NOT NULL,
    n_treated INTEGER NOT NULL,
    n_control INTEGER NOT NULL,
    fitted_at TEXT NOT NULL,
    used INTEGER NOT NULL,
    PRIMARY KEY(season, factor_name)
);
"""


@dataclass(frozen=True)
class LambdaSample:
    season: str
    match_date: str
    home_team: str
    away_team: str
    base_xg_home: float
    base_xg_away: float
    projected_xg_home: float
    projected_xg_away: float
    rotation_risk: bool = False
    slow_start: bool = False
    low_motivation_home: bool = False
    low_motivation_away: bool = False
    corto_muso_home: bool = False
    corto_muso_away: bool = False
    attack_factor_home: float = 1.0
    attack_factor_away: float = 1.0
    leak_to_home: float = 1.0
    leak_to_away: float = 1.0
    actual_home_goals: int | None = None
    actual_away_goals: int | None = None
    fixture_id: int | None = None

    @property
    def settled(self) -> bool:
        return self.actual_home_goals is not None and self.actual_away_goals is not None


@dataclass(frozen=True)
class FactorFit:
    name: str
    prior: float
    fitted: float
    n_treated: int
    n_control: int
    used: bool
    internal_weight: float = 0.0


@dataclass(frozen=True)
class SeasonMatch:
    """Partita finita caricata da una fonte esterna, non scritta da noi."""

    season: str
    match_date: str
    home_team: str
    away_team: str
    home_goals: int
    away_goals: int
    league: str = ""


@dataclass(frozen=True)
class CalibrationRun:
    fits: list[FactorFit]
    loaded: int
    eligible: int


@dataclass(frozen=True)
class MatchResult:
    home_team: str
    away_team: str
    match_date: str
    home_goals: int
    away_goals: int


def season_key(match_date: date) -> str:
    """Stagione europea: luglio apre l'annata nuova."""
    year = match_date.year
    if match_date.month >= 7:
        return f"{year}-{(year + 1) % 100:02d}"
    return f"{year - 1}-{year % 100:02d}"


def events_from_api_injuries(
    injuries: list[dict],
    home: str,
    away: str,
) -> list[SixthSenseEvent]:
    """Traduce /injuries in eventi. Un dubbio non muove i gol attesi."""
    events: list[SixthSenseEvent] = []
    for item in injuries:
        team_name = str(item.get("team", ""))
        if home.casefold() in team_name.casefold():
            side = "home"
        elif away.casefold() in team_name.casefold():
            side = "away"
        else:
            continue
        kind = str(item.get("type", "")).casefold()
        reason = " ".join(
            part
            for part in (item.get("player", ""), item.get("type", ""), item.get("reason", ""))
            if part
        )
        if "question" in kind or "doubt" in kind:
            impact, confidence = -1.0, 0.4
        else:
            impact, confidence = -1.5, 0.8
        event_type = "suspension" if "suspend" in kind or "squalif" in reason.casefold() else "injury"
        events.append(
            SixthSenseEvent(
                team=side,
                event_type=event_type,
                description=reason,
                impact=impact,
                confidence=confidence,
                source_hint=str(item.get("player", "")),
            )
        )
    return events


def connect(db_path: Path | str | None = None) -> sqlite3.Connection:
    path = Path(db_path) if db_path else DB_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(_DDL)
    return conn


def record_projection(
    season: str,
    match_date: str,
    home_team: str,
    away_team: str,
    base_xg_home: float,
    base_xg_away: float,
    projected_xg_home: float,
    projected_xg_away: float,
    context: MatchContext,
    fixture_id: int | None = None,
    db_path: Path | str | None = None,
) -> None:
    """Salva la fotografia pre-partita. Un nuovo passaggio non cancella il punteggio già chiuso."""
    sample = LambdaSample(
        season=season,
        match_date=match_date,
        home_team=home_team.strip(),
        away_team=away_team.strip(),
        fixture_id=fixture_id,
        base_xg_home=base_xg_home,
        base_xg_away=base_xg_away,
        projected_xg_home=projected_xg_home,
        projected_xg_away=projected_xg_away,
        rotation_risk=context.rotation_risk,
        slow_start=context.slow_start,
        low_motivation_home=context.low_motivation_home,
        low_motivation_away=context.low_motivation_away,
        corto_muso_home=context.corto_muso_home,
        corto_muso_away=context.corto_muso_away,
        attack_factor_home=context.attack_factor_home,
        attack_factor_away=context.attack_factor_away,
        leak_to_home=context.leak_to_home,
        leak_to_away=context.leak_to_away,
    )
    _upsert(sample, db_path)


def list_samples(season: str | None = None, db_path: Path | str | None = None) -> list[LambdaSample]:
    conn = connect(db_path)
    try:
        if season is None:
            rows = conn.execute("SELECT * FROM sixth_sense_samples").fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM sixth_sense_samples WHERE season = ?",
                (season,),
            ).fetchall()
        return [_sample_from_row(row) for row in rows]
    finally:
        conn.close()


def settle_results(results: list[MatchResult], db_path: Path | str | None = None) -> int:
    """Scrive i gol finali sulle fotografie già salvate, a parità di squadre e data."""
    conn = connect(db_path)
    updated = 0
    settled_at = datetime.now(timezone.utc).isoformat()
    try:
        rows = conn.execute("SELECT id, home_team, away_team, match_date FROM sixth_sense_samples").fetchall()
        by_key: dict[tuple[str, str, str], list[int]] = {}
        for row in rows:
            key = (row["home_team"].casefold(), row["away_team"].casefold(), row["match_date"])
            by_key.setdefault(key, []).append(row["id"])
        for result in results:
            key = (result.home_team.casefold(), result.away_team.casefold(), result.match_date)
            for sample_id in by_key.get(key, []):
                conn.execute(
                    """
                    UPDATE sixth_sense_samples
                    SET actual_home_goals = ?, actual_away_goals = ?, settled_at = ?
                    WHERE id = ?
                    """,
                    (result.home_goals, result.away_goals, settled_at, sample_id),
                )
                updated += 1
        conn.commit()
    finally:
        conn.close()
    return updated


def settle_from_matches(db_path: Path | str | None = None) -> int:
    """Chiude le fotografie con i gol già presenti nella tabella matches."""
    conn = connect(db_path)
    try:
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        if "matches" not in tables:
            return 0
        rows = conn.execute(
            """
            SELECT home_team, away_team, date_gmt, home_goals, away_goals
            FROM matches
            WHERE home_goals IS NOT NULL AND away_goals IS NOT NULL AND date_gmt IS NOT NULL
            """
        ).fetchall()
    finally:
        conn.close()
    results = [
        MatchResult(
            home_team=row["home_team"],
            away_team=row["away_team"],
            match_date=str(row["date_gmt"])[:10],
            home_goals=int(row["home_goals"]),
            away_goals=int(row["away_goals"]),
        )
        for row in rows
    ]
    return settle_results(results, db_path)


def sample_decay(match_date: str, as_of: date) -> float:
    """1.0 entro 45 giorni, 0.5 fino a 90, 0.25 dopo. Una data futura vale zero."""
    try:
        played = date.fromisoformat(match_date[:10])
    except ValueError:
        return 0.0
    if played > as_of:
        return 0.0
    age = (as_of - played).days
    if age <= DECAY_FULL_DAYS:
        return 1.0
    if age <= DECAY_HALF_DAYS:
        return 0.5
    return 0.25


def _as_of(samples: list[LambdaSample], as_of: date | None) -> date:
    if as_of is not None:
        return as_of
    dates: list[date] = []
    for sample in samples:
        try:
            dates.append(date.fromisoformat(sample.match_date[:10]))
        except ValueError:
            continue
    return max(dates) if dates else date.today()


def fit_factors(samples: list[LambdaSample], as_of: date | None = None) -> list[FactorFit]:
    """Stima i fattori sulle partite chiuse, pesate per età. Nessuna gara dopo as_of."""
    settled = [sample for sample in samples if sample.settled]
    anchor = _as_of(settled, as_of)
    visible = [sample for sample in settled if sample_decay(sample.match_date, anchor) > 0]
    return [
        _fit_rotation(visible, anchor),
        _fit_side_flag(visible, "low_motivation", LOW_MOTIVATION_FACTOR, "low_motivation", anchor),
        _fit_side_flag(visible, "corto_muso", CORTO_MUSO_FACTOR, "corto_muso", anchor),
        _fit_injury_scale(visible, anchor),
    ]


def save_fits(season: str, fits: list[FactorFit], db_path: Path | str | None = None) -> None:
    fitted_at = datetime.now(timezone.utc).isoformat()
    conn = connect(db_path)
    try:
        for fit in fits:
            conn.execute(
                """
                INSERT INTO sixth_sense_factor_fits
                    (season, factor_name, prior, fitted, n_treated, n_control, fitted_at, used)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(season, factor_name) DO UPDATE SET
                    prior = excluded.prior,
                    fitted = excluded.fitted,
                    n_treated = excluded.n_treated,
                    n_control = excluded.n_control,
                    fitted_at = excluded.fitted_at,
                    used = excluded.used
                """,
                (
                    season,
                    fit.name,
                    fit.prior,
                    fit.fitted,
                    fit.n_treated,
                    fit.n_control,
                    fitted_at,
                    int(fit.used),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def load_factors(season: str, db_path: Path | str | None = None) -> FactorSet:
    """Prior se il fit non ha ancora abbastanza partite."""
    try:
        conn = connect(db_path)
    except Exception:
        return FactorSet()
    try:
        rows = conn.execute(
            """
            SELECT factor_name, fitted
            FROM sixth_sense_factor_fits
            WHERE season = ? AND used = 1
            """,
            (season,),
        ).fetchall()
    except Exception:
        return FactorSet()
    finally:
        conn.close()
    values = {row["factor_name"]: row["fitted"] for row in rows}
    return FactorSet(
        rotation=values.get("rotation", ROTATION_FACTOR),
        low_motivation=values.get("low_motivation", LOW_MOTIVATION_FACTOR),
        corto_muso=values.get("corto_muso", CORTO_MUSO_FACTOR),
        injury_scale=values.get("injury_scale", 1.0),
    )


def same_season(stored: str, wanted: str) -> bool:
    """2026, 2026/2027 e 2026-27 sono la stessa annata."""
    left = stored.strip()
    right = wanted.strip()
    if left == right:
        return True
    start = right[:4]
    return start.isdigit() and start in left.replace("/", "-")


def after_third(matches: list[SeasonMatch]) -> list[SeasonMatch]:
    """Tiene le gare in cui entrambe le squadre hanno già chiuso 3 partite di quel campionato."""
    ordered = sorted(matches, key=lambda match: (match.match_date, match.home_team, match.away_team))
    played: dict[tuple[str, str], int] = {}
    kept: list[SeasonMatch] = []
    for match in ordered:
        key_home = (match.league.casefold(), match.home_team.casefold())
        key_away = (match.league.casefold(), match.away_team.casefold())
        if played.get(key_home, 0) >= MIN_PLAYED_BEFORE and played.get(key_away, 0) >= MIN_PLAYED_BEFORE:
            kept.append(match)
        played[key_home] = played.get(key_home, 0) + 1
        played[key_away] = played.get(key_away, 0) + 1
    return kept


def played_before(
    matches: list[SeasonMatch],
    team: str,
    match_date: str,
    league: str = "",
) -> int | None:
    """Partite già chiuse da quella squadra prima di questa data. None se la squadra non è nella fonte."""
    name = team.casefold()
    league_name = league.casefold()
    seen = [
        match
        for match in matches
        if (not league_name or match.league.casefold() == league_name)
        and name in {match.home_team.casefold(), match.away_team.casefold()}
    ]
    if not seen:
        return None
    return sum(1 for match in seen if match.match_date < match_date)


def load_finished_matches(season: str, db_path: Path | str | None = None) -> list[SeasonMatch]:
    """Legge i risultati già scaricati in matches. Non crea uno storico nostro."""
    path = Path(db_path) if db_path else DB_PATH
    if not path.exists():
        return []
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        if "matches" not in tables:
            return []
        rows = conn.execute(
            """
            SELECT league, season, date_gmt, home_team, away_team, home_goals, away_goals
            FROM matches
            WHERE home_goals IS NOT NULL AND away_goals IS NOT NULL AND date_gmt IS NOT NULL
            """
        ).fetchall()
    finally:
        conn.close()
    return [
        SeasonMatch(
            season=str(row["season"]),
            match_date=str(row["date_gmt"])[:10],
            home_team=row["home_team"],
            away_team=row["away_team"],
            home_goals=int(row["home_goals"]),
            away_goals=int(row["away_goals"]),
            league=row["league"] or "",
        )
        for row in rows
        if same_season(str(row["season"]), season)
    ]


def calibrate_season(season: str, db_path: Path | str | None = None) -> CalibrationRun:
    """Carica i risultati esterni, scarta le prime 3 gare per squadra e fitta solo il resto."""
    loaded = load_finished_matches(season, db_path)
    eligible = after_third(loaded)
    settle_from_matches(db_path)
    allowed = {
        (match.home_team.casefold(), match.away_team.casefold(), match.match_date)
        for match in eligible
    }
    usable = [
        sample
        for sample in list_samples(season, db_path)
        if (sample.home_team.casefold(), sample.away_team.casefold(), sample.match_date) in allowed
    ]
    fits = fit_factors(usable)
    save_fits(season, fits, db_path)
    return CalibrationRun(fits=fits, loaded=len(loaded), eligible=len(eligible))


def _upsert(sample: LambdaSample, db_path: Path | str | None) -> None:
    conn = connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO sixth_sense_samples (
                season, match_date, home_team, away_team, fixture_id,
                base_xg_home, base_xg_away, projected_xg_home, projected_xg_away,
                rotation_risk, slow_start, low_motivation_home, low_motivation_away,
                corto_muso_home, corto_muso_away, attack_factor_home, attack_factor_away,
                leak_to_home, leak_to_away
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(season, match_date, home_team, away_team) DO UPDATE SET
                fixture_id = excluded.fixture_id,
                base_xg_home = excluded.base_xg_home,
                base_xg_away = excluded.base_xg_away,
                projected_xg_home = excluded.projected_xg_home,
                projected_xg_away = excluded.projected_xg_away,
                rotation_risk = excluded.rotation_risk,
                slow_start = excluded.slow_start,
                low_motivation_home = excluded.low_motivation_home,
                low_motivation_away = excluded.low_motivation_away,
                corto_muso_home = excluded.corto_muso_home,
                corto_muso_away = excluded.corto_muso_away,
                attack_factor_home = excluded.attack_factor_home,
                attack_factor_away = excluded.attack_factor_away,
                leak_to_home = excluded.leak_to_home,
                leak_to_away = excluded.leak_to_away
            """,
            (
                sample.season,
                sample.match_date,
                sample.home_team,
                sample.away_team,
                sample.fixture_id,
                sample.base_xg_home,
                sample.base_xg_away,
                sample.projected_xg_home,
                sample.projected_xg_away,
                int(sample.rotation_risk),
                int(sample.slow_start),
                int(sample.low_motivation_home),
                int(sample.low_motivation_away),
                int(sample.corto_muso_home),
                int(sample.corto_muso_away),
                sample.attack_factor_home,
                sample.attack_factor_away,
                sample.leak_to_home,
                sample.leak_to_away,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _sample_from_row(row: sqlite3.Row) -> LambdaSample:
    return LambdaSample(
        season=row["season"],
        match_date=row["match_date"],
        home_team=row["home_team"],
        away_team=row["away_team"],
        fixture_id=row["fixture_id"],
        base_xg_home=row["base_xg_home"],
        base_xg_away=row["base_xg_away"],
        projected_xg_home=row["projected_xg_home"],
        projected_xg_away=row["projected_xg_away"],
        rotation_risk=bool(row["rotation_risk"]),
        slow_start=bool(row["slow_start"]),
        low_motivation_home=bool(row["low_motivation_home"]),
        low_motivation_away=bool(row["low_motivation_away"]),
        corto_muso_home=bool(row["corto_muso_home"]),
        corto_muso_away=bool(row["corto_muso_away"]),
        attack_factor_home=row["attack_factor_home"],
        attack_factor_away=row["attack_factor_away"],
        leak_to_home=row["leak_to_home"],
        leak_to_away=row["leak_to_away"],
        actual_home_goals=row["actual_home_goals"],
        actual_away_goals=row["actual_away_goals"],
    )


def internal_weight(n_treated: float) -> float:
    """0% sotto le 8 partite effettive, poi 1% a partita, fermo al 30%."""
    if n_treated < MIN_GROUP:
        return 0.0
    return min(INTERNAL_WEIGHT_CAP, float(n_treated) * INTERNAL_WEIGHT_PER_MATCH)


def _apply_internal(prior: float, raw: float, n_treated: float, low: float, high: float) -> tuple[float, float]:
    weight = min(INTERNAL_WEIGHT_CAP, internal_weight(n_treated))
    clipped = min(high, max(low, raw))
    return prior + weight * (clipped - prior), weight


def _ready(n_treated: float, n_control: float) -> bool:
    return n_treated >= MIN_GROUP and n_control >= MIN_GROUP


def _clean_match(sample: LambdaSample) -> bool:
    return not any(
        (
            sample.rotation_risk,
            sample.low_motivation_home,
            sample.low_motivation_away,
            sample.corto_muso_home,
            sample.corto_muso_away,
            sample.attack_factor_home < 1.0,
            sample.attack_factor_away < 1.0,
            sample.leak_to_home > 1.0,
            sample.leak_to_away > 1.0,
        )
    )


def _side_is_clean(sample: LambdaSample, side: str) -> bool:
    if sample.rotation_risk:
        return False
    if side == "home":
        return (
            not sample.low_motivation_home
            and not sample.corto_muso_home
            and sample.attack_factor_home >= 1.0
            and sample.leak_to_home <= 1.0
        )
    return (
        not sample.low_motivation_away
        and not sample.corto_muso_away
        and sample.attack_factor_away >= 1.0
        and sample.leak_to_away <= 1.0
    )


def _fit_rotation(samples: list[LambdaSample], as_of: date) -> FactorFit:
    treated = [sample for sample in samples if sample.rotation_risk and _only_rotation(sample)]
    control = [sample for sample in samples if _clean_match(sample)]
    return _fit_total("rotation", ROTATION_FACTOR, treated, control, as_of)


def _only_rotation(sample: LambdaSample) -> bool:
    return not any(
        (
            sample.low_motivation_home,
            sample.low_motivation_away,
            sample.corto_muso_home,
            sample.corto_muso_away,
            sample.attack_factor_home < 1.0,
            sample.attack_factor_away < 1.0,
            sample.leak_to_home > 1.0,
            sample.leak_to_away > 1.0,
        )
    )


def _fit_total(
    name: str,
    prior: float,
    treated: list[LambdaSample],
    control: list[LambdaSample],
    as_of: date,
) -> FactorFit:
    treated_rate, treated_mass = _goal_rate(treated, as_of)
    control_rate, control_mass = _goal_rate(control, as_of)
    if (
        treated_rate is None
        or control_rate is None
        or control_rate <= 0
        or not _ready(treated_mass, control_mass)
    ):
        return FactorFit(name, prior, prior, int(treated_mass), int(control_mass), False)
    raw = treated_rate / control_rate
    fitted, weight = _apply_internal(prior, raw, treated_mass, 0.50, 1.20)
    return FactorFit(name, prior, fitted, int(treated_mass), int(control_mass), True, weight)


def _goal_rate(samples: list[LambdaSample], as_of: date) -> tuple[float | None, float]:
    base = 0.0
    actual = 0.0
    mass = 0.0
    for sample in samples:
        weight = sample_decay(sample.match_date, as_of)
        if weight <= 0:
            continue
        base += weight * (sample.base_xg_home + sample.base_xg_away)
        actual += weight * ((sample.actual_home_goals or 0) + (sample.actual_away_goals or 0))
        mass += weight
    if base <= 0 or mass <= 0:
        return None, mass
    return actual / base, mass


def _fit_side_flag(
    samples: list[LambdaSample],
    flag: str,
    prior: float,
    name: str,
    as_of: date,
) -> FactorFit:
    treated_actual = 0.0
    treated_base = 0.0
    n_treated = 0.0
    control_actual = 0.0
    control_base = 0.0
    n_control = 0.0
    for sample in samples:
        weight = sample_decay(sample.match_date, as_of)
        if weight <= 0:
            continue
        for side in ("home", "away"):
            actual = sample.actual_home_goals if side == "home" else sample.actual_away_goals
            base = sample.base_xg_home if side == "home" else sample.base_xg_away
            flagged = getattr(sample, f"{flag}_{side}")
            if flagged and _side_only_flag(sample, side, flag):
                treated_actual += weight * (actual or 0)
                treated_base += weight * base
                n_treated += weight
            elif _side_is_clean(sample, side):
                control_actual += weight * (actual or 0)
                control_base += weight * base
                n_control += weight
    if treated_base <= 0 or control_base <= 0 or not _ready(n_treated, n_control):
        return FactorFit(name, prior, prior, int(n_treated), int(n_control), False)
    raw = (treated_actual / treated_base) / (control_actual / control_base)
    fitted, weight = _apply_internal(prior, raw, n_treated, 0.50, 1.20)
    return FactorFit(name, prior, fitted, int(n_treated), int(n_control), True, weight)


def _side_only_flag(sample: LambdaSample, side: str, flag: str) -> bool:
    if sample.rotation_risk:
        return False
    if side == "home":
        other_corto = sample.corto_muso_home if flag != "corto_muso" else False
        other_motivation = sample.low_motivation_home if flag != "low_motivation" else False
        return (
            not other_corto
            and not other_motivation
            and sample.attack_factor_home >= 1.0
            and sample.leak_to_home <= 1.0
        )
    other_corto = sample.corto_muso_away if flag != "corto_muso" else False
    other_motivation = sample.low_motivation_away if flag != "low_motivation" else False
    return (
        not other_corto
        and not other_motivation
        and sample.attack_factor_away >= 1.0
        and sample.leak_to_away <= 1.0
    )


def _fit_injury_scale(samples: list[LambdaSample], as_of: date) -> FactorFit:
    numerator = 0.0
    denominator = 0.0
    n_treated = 0.0
    for sample in samples:
        weight = sample_decay(sample.match_date, as_of)
        if weight <= 0 or sample.rotation_risk:
            continue
        if (
            sample.attack_factor_home < 1.0
            and not sample.low_motivation_home
            and not sample.corto_muso_home
            and sample.leak_to_home <= 1.0
        ):
            numerator += weight * (sample.actual_home_goals or 0)
            denominator += weight * sample.base_xg_home * sample.attack_factor_home
            n_treated += weight
        if (
            sample.attack_factor_away < 1.0
            and not sample.low_motivation_away
            and not sample.corto_muso_away
            and sample.leak_to_away <= 1.0
        ):
            numerator += weight * (sample.actual_away_goals or 0)
            denominator += weight * sample.base_xg_away * sample.attack_factor_away
            n_treated += weight
    if denominator <= 0 or n_treated < MIN_GROUP:
        return FactorFit("injury_scale", 1.0, 1.0, int(n_treated), 0, False)
    raw = numerator / denominator
    fitted, weight = _apply_internal(1.0, raw, n_treated, 0.50, 1.50)
    return FactorFit("injury_scale", 1.0, fitted, int(n_treated), 0, True, weight)

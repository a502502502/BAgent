"""Lettura della cache Netwin, senza browser e senza abbonamenti.

Il file `data/netwin_live_odds.json` è già il palinsesto decodificato da
`NetwinOddsDownloader`. Qui diventa una lista di partite con le quote
piatte, nel formato che `find_hidden_gems` confronta con la matrice dei gol.
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from services.analysis.combo_book_search import HiddenMarketFilter, find_hidden_gems
from services.analysis.league_dna_market_matcher import LeagueDNAMarketMatcher
from services.database.schema import DB_PATH
from services.football.sixth_sense.lambda_context import MatchContext

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CACHE = ROOT / "data" / "netwin_live_odds.json"
MIN_TEAM_GAMES = 5
CACHE_MAX_AGE_HOURS = 12.0

_MATCHER = LeagueDNAMarketMatcher()


@dataclass(frozen=True)
class CachedMatch:
    match_name: str
    home_team: str
    away_team: str
    tournament: str
    kickoff: str
    odds_dict: dict[str, float]


@dataclass(frozen=True)
class NetwinGem:
    tournament: str
    match_name: str
    market: str
    book_odd: float
    fair_odd: float
    probability: float
    edge: float
    notes: str


def cache_is_stale(path: Path | None = None, max_age_hours: float = CACHE_MAX_AGE_HOURS) -> bool:
    """Vera se il file manca, è vuoto, o è più vecchio della finestra."""
    target = path or DEFAULT_CACHE
    if not target.exists():
        return True
    try:
        if target.stat().st_size <= 0:
            return True
        age_hours = (time.time() - target.stat().st_mtime) / 3600.0
    except OSError:
        return True
    return age_hours > max_age_hours


def flatten_netwin_markets(match_data: dict | None) -> dict[str, float]:
    """Appiattisce i mercati annidati di Netwin nel dizionario universale delle combo."""
    if not isinstance(match_data, dict):
        return {}
    markets = match_data.get("markets")
    if not isinstance(markets, dict):
        markets = match_data
    flat: dict[str, float] = {}
    _copy_outcome_map(markets.get("1X2"), flat, lambda key: str(key))
    _copy_outcome_map(markets.get("DOPPIA_CHANCE"), flat, lambda key: str(key))
    _copy_goal_lines(markets.get("UNDER_OVER"), flat, corner=False)
    goal = markets.get("GOL_NOGOL")
    if isinstance(goal, dict):
        for key, value in goal.items():
            odd = _as_odd(value)
            if odd is not None:
                flat[str(key)] = odd
    _copy_multigol(markets.get("MULTIGOL") or markets.get("MultiGol"), flat)
    _copy_goal_lines(markets.get("CORNER") or markets.get("CORNERS"), flat, corner=True)
    return flat


def load_cached_matches(
    tournament: str | None = None,
    path: Path | None = None,
) -> list[CachedMatch]:
    """Carica il palinsesto. JSON assente o illeggibile: lista vuota, niente eccezione."""
    target = path or DEFAULT_CACHE
    payload = _read_payload(target)
    rows = payload.get("matches") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        return []
    wanted = (tournament or "").casefold().strip()
    loaded: list[CachedMatch] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        match = _cached_match(row)
        if match is None:
            continue
        if wanted and wanted not in match.tournament.casefold():
            continue
        loaded.append(match)
    return loaded


LEAGUE_BASELINES: dict[str, tuple[float, float]] = {
    "primera division arg": (1.20, 0.931),  # Totale 2.131 (Under 2.5: 62.5%, Under 3.5: 84.2%)
    "liga profesional": (1.20, 0.931),
    "argentina": (1.20, 0.931),
    "brazil serie a": (1.52, 1.148),        # Totale 2.668 (Under 2.5: 48.4%, Under 3.5: 74.4%)
    "serie a brasiliana": (1.52, 1.148),
    "brasile": (1.52, 1.148),
    "serie a": (1.60, 1.30),                # Totale 2.90
    "premier league": (1.53, 1.29),         # Totale 2.82
    "la liga": (1.65, 1.39),                # Totale 3.04
    "laliga": (1.65, 1.39),
    "bundesliga": (2.05, 1.76),             # Totale 3.81
    "europa league": (1.48, 1.24),          # Totale 2.72
}


def tournament_baseline(tournament: str) -> tuple[float, float]:
    """Spezza la media gol certificata del torneo in casa e trasferta."""
    key = (tournament or "").casefold().strip()
    for league_name, baseline in LEAGUE_BASELINES.items():
        if league_name in key or key in league_name:
            return baseline
    _cluster, data = _MATCHER.identify_league_cluster(tournament or "")
    total = float((data.get("stats") or {}).get("avg_goals") or 2.50)
    home = max(0.2, total * 0.55)
    return home, max(0.2, total - home)


def historical_xg(
    home: str,
    away: str,
    tournament: str = "",
    db_path: Path | None = None,
) -> tuple[float, float] | None:
    """Media gol certificata nel database con regressione bayesiana (shrinkage) verso la media di lega."""
    target = db_path or DB_PATH
    if not home or not away or not target.exists():
        return None
    try:
        conn = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        home_rows = _team_games(conn, home, home_side=True)
        away_rows = _team_games(conn, away, home_side=False)
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    if len(home_rows) < MIN_TEAM_GAMES and len(away_rows) < MIN_TEAM_GAMES:
        return None

    l_home, l_away = tournament_baseline(tournament)

    # Bayesian shrinkage (m = 5.0 partite a priori sulla media di lega)
    m = 5.0
    n_h = len(home_rows)
    n_a = len(away_rows)

    h_att = (sum(row[0] for row in home_rows) + m * l_home) / (n_h + m) if n_h else l_home
    h_def = (sum(row[1] for row in home_rows) + m * l_away) / (n_h + m) if n_h else l_away

    a_att = (sum(row[0] for row in away_rows) + m * l_away) / (n_a + m) if n_a else l_away
    a_def = (sum(row[1] for row in away_rows) + m * l_home) / (n_a + m) if n_a else l_home

    xg_home = min(3.5, max(0.2, (h_att / l_home) * (a_def / l_home) * l_home))
    xg_away = min(3.5, max(0.2, (a_att / l_away) * (h_def / l_away) * l_away))
    return round(xg_home, 2), round(xg_away, 2)


def estimate_xg(match: CachedMatch, db_path: Path | None = None) -> tuple[float, float]:
    """Prima lo storico shrunken delle due squadre, poi la baseline certificata del torneo."""
    stored = historical_xg(match.home_team, match.away_team, match.tournament, db_path)
    if stored is not None:
        return stored
    return tournament_baseline(match.tournament)


def context_for_match(match: CachedMatch) -> MatchContext:
    """Il sesto senso entra solo dalle bandiere già note: corto muso delle squadre pragmatiche."""
    home = match.home_team.casefold()
    away = match.away_team.casefold()
    clubs = _MATCHER.PRAGMATIC_LOW_PACE_CLUBS
    return MatchContext(
        corto_muso_home=any(club in home for club in clubs),
        corto_muso_away=any(club in away for club in clubs),
    )


def scan_netwin_matches(
    matches: list[CachedMatch],
    *,
    min_edge: float = 0.045,
    min_probability: float = 0.70,
    xg_for: Callable[[CachedMatch], tuple[float, float]] | None = None,
    context_for: Callable[[CachedMatch], MatchContext] | None = None,
) -> list[NetwinGem]:
    """Confronta ogni quota piatta con la matrice. Tiene solo le Hidden Gems sopra soglia."""
    resolve_xg = xg_for or estimate_xg
    resolve_context = context_for or context_for_match
    sweet = HiddenMarketFilter(min_probability=min_probability, min_edge=min_edge)
    gems: list[NetwinGem] = []
    for match in matches:
        try:
            xg_home, xg_away = resolve_xg(match)
        except (TypeError, ValueError):
            continue
        if xg_home <= 0 or xg_away <= 0:
            continue
        found = find_hidden_gems(
            xg_home,
            xg_away,
            match.odds_dict,
            resolve_context(match),
            sweet,
        )
        note = "; ".join(found.notes)
        for combo in found.ranked:
            gems.append(
                NetwinGem(
                    tournament=match.tournament,
                    match_name=match.match_name,
                    market=combo.market,
                    book_odd=combo.book_odd,
                    fair_odd=combo.fair_odd,
                    probability=combo.probability,
                    edge=combo.edge,
                    notes=note,
                )
            )
    gems.sort(key=lambda gem: gem.edge, reverse=True)
    return gems


def _read_payload(path: Path) -> dict | list:
    try:
        raw = path.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError):
        return {}
    if isinstance(payload, (dict, list)):
        return payload
    return {}


def _cached_match(row: dict) -> CachedMatch | None:
    match_name = str(row.get("match_name") or "").strip()
    raw_name = str(row.get("raw_name") or "").strip()
    home, away = split_teams(match_name, raw_name)
    if not home or not away:
        return None
    label = match_name or f"{home} vs {away}"
    odds = flatten_netwin_markets(row)
    return CachedMatch(
        match_name=label,
        home_team=home,
        away_team=away,
        tournament=str(row.get("tournament") or "").strip(),
        kickoff=str(row.get("kickoff") or "").strip(),
        odds_dict=odds,
    )


def split_teams(match_name: str, raw_name: str = "") -> tuple[str, str]:
    for text in (match_name, raw_name):
        if " vs " in text:
            home, away = text.split(" vs ", 1)
            return home.strip(), away.strip()
    for text in (raw_name, match_name):
        if " - " in text:
            home, away = text.split(" - ", 1)
            return home.strip(), away.strip()
    return "", ""


def _as_odd(value: object) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        odd = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    if odd <= 1.0:
        return None
    return odd


def _copy_outcome_map(source: object, flat: dict[str, float], rename: Callable[[object], str]) -> None:
    if not isinstance(source, dict):
        return
    for key, value in source.items():
        odd = _as_odd(value)
        if odd is not None:
            flat[rename(key)] = odd


def _copy_goal_lines(source: object, flat: dict[str, float], *, corner: bool) -> None:
    if not isinstance(source, dict):
        return
    suffix = " Corner" if corner else ""
    for line, sides in source.items():
        label = str(line).strip()
        if isinstance(sides, dict):
            over = _as_odd(sides.get("Over"))
            under = _as_odd(sides.get("Under"))
            if "corner" in label.casefold():
                if over is not None:
                    flat[label if label.casefold().startswith("over") else f"Over {label}"] = over
                if under is not None:
                    flat[label if label.casefold().startswith("under") else f"Under {label}"] = under
                continue
            if over is not None:
                flat[f"Over {label}{suffix}"] = over
            if under is not None:
                flat[f"Under {label}{suffix}"] = under
            continue
        odd = _as_odd(sides)
        if odd is None:
            continue
        if corner and "corner" not in label.casefold():
            flat[f"{label}{suffix}"] = odd
        else:
            flat[label] = odd


def _copy_multigol(source: object, flat: dict[str, float]) -> None:
    if not isinstance(source, dict):
        return
    for key, value in source.items():
        odd = _as_odd(value)
        if odd is None:
            continue
        label = str(key).strip()
        if not label.casefold().startswith("multigol"):
            label = f"MultiGol {label}"
        flat[label] = odd


def _normalize_team_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    s = s.lower()
    s = re.sub(r"\b(fc|sp|rj|mg|ba|pr|sc|sde|cr|ec|fr|y esgrima)\b", "", s)
    s = re.sub(r"[^a-z0-9]", " ", s)
    return " ".join(s.split())


def _find_matching_team(conn: sqlite3.Connection, raw_name: str, *, home_side: bool) -> str:
    if not raw_name:
        return raw_name
    norm = _normalize_team_name(raw_name)
    col = "home_team" if home_side else "away_team"
    try:
        cursor = conn.execute(f"SELECT DISTINCT {col} FROM matches WHERE status='FT'")
        all_teams = [row[0] for row in cursor if row[0]]
    except Exception:
        return raw_name
    for t in all_teams:
        if _normalize_team_name(t) == norm:
            return t
    for t in all_teams:
        t_norm = _normalize_team_name(t)
        if norm and (norm in t_norm or t_norm in norm):
            return t
    return raw_name


def _team_games(conn: sqlite3.Connection, team: str, *, home_side: bool) -> list[tuple[float, float]]:
    db_team = _find_matching_team(conn, team, home_side=home_side)
    if home_side:
        query = """
            SELECT home_goals, away_goals FROM matches
            WHERE status='FT' AND home_team=? AND home_goals IS NOT NULL AND away_goals IS NOT NULL
        """
    else:
        query = """
            SELECT away_goals, home_goals FROM matches
            WHERE status='FT' AND away_team=? AND home_goals IS NOT NULL AND away_goals IS NOT NULL
        """
    return [(float(scored), float(conceded)) for scored, conceded in conn.execute(query, (db_team,))]


def _mean(values) -> float:
    rows = list(values)
    if not rows:
        return 0.0
    return sum(rows) / len(rows)

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

from services.analysis.combo_book_search import (
    COMBO_CATALOG,
    market_verdict,
    rank_quoted_markets,
)
from services.analysis.league_dna_market_matcher import LeagueDNAMarketMatcher
from services.database.schema import DB_PATH
from services.football.sixth_sense.lambda_context import MatchContext

ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CACHE = ROOT / "data" / "netwin_live_odds.json"
MIN_TEAM_GAMES = 1
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
    verdict: str = ""


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
    _copy_outcome_map(markets.get("COMBO") or markets.get("combo"), flat, lambda key: str(key))
    _copy_outcome_map(markets.get("PRIMO_TEMPO") or markets.get("primo_tempo"), flat, lambda key: str(key))
    _copy_outcome_map(markets.get("CHANCE_MIX") or markets.get("chance_mix"), flat, lambda key: str(key))
    _copy_outcome_map(markets.get("DRAW_NO_BET") or markets.get("draw_no_bet"), flat, lambda key: str(key))
    _copy_outcome_map(markets.get("MULTIGOL_SQUADRA") or markets.get("multigol_squadra"), flat, lambda key: str(key))
    _copy_goal_lines(markets.get("CORNER") or markets.get("CORNERS"), flat, corner=True)
    _sanitize_double_chance(flat)
    return flat


def _sanitize_double_chance(flat: dict[str, float]) -> None:
    """Rimuove quote di Doppia Chance palesemente corrotte o scambiate rispetto all'1X2."""
    o1, ox, o2 = flat.get("1"), flat.get("X"), flat.get("2")
    if not (o1 and ox and o2):
        return

    fair_1x = 1.0 / (1.0 / o1 + 1.0 / ox)
    fair_x2 = 1.0 / (1.0 / ox + 1.0 / o2)
    fair_12 = 1.0 / (1.0 / o1 + 1.0 / o2)

    # Hard bounds matematici: una doppia chance include due esiti, quindi la sua quota
    # non può mai essere superiore (o quasi uguale) al segno secco, né discostarsi vistosamente
    # dal valore equo teorico calcolato sui prezzi 1X2 del banco.
    if "X2" in flat:
        if flat["X2"] >= o2 or abs(flat["X2"] - fair_x2) > 0.35:
            del flat["X2"]

    if "1X" in flat:
        if flat["1X"] >= o1 or abs(flat["1X"] - fair_1x) > 0.35:
            del flat["1X"]

    if "12" in flat:
        if flat["12"] >= min(o1, o2) or abs(flat["12"] - fair_12) > 0.35:
            del flat["12"]


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
    stored = _stored_league_baseline(key)
    if stored is not None:
        return stored
    hardcoded = _hardcoded_baseline(key)
    if hardcoded is not None:
        return hardcoded
    _cluster, data = _MATCHER.identify_league_cluster(tournament or "")
    total = float((data.get("stats") or {}).get("avg_goals") or 2.50)
    home = max(0.2, total * 0.55)
    return home, max(0.2, total - home)


_LEAGUE_AVERAGE_CACHE: dict[str, tuple[float, float, int]] | None = None

# Token del torneo -> frammento del nome lega salvato in matches.league
_STORED_LEAGUE_TOKENS = (
    ("nations league", "uefa nations league"),
    ("libertadores", "copa libertadores"),
    ("sudamericana", "copa sudamericana"),
    ("ekstraklasa", "ekstraklasa"),
    ("liga mx", "liga mx"),
    ("j1 league", "j1 league"),
    ("prva hnl", "prva hnl"),
    ("hnl", "prva hnl"),
    ("superliga serbia", "serbia superliga"),
    ("serbia", "serbia superliga"),
    ("primera a", "colombia primera a"),
    ("colombia", "colombia primera a"),
    ("chile", "chile primera"),
    ("czech", "czech first league"),
    ("cechia", "czech first league"),
    ("peru", "peru primera"),
    ("uruguay", "uruguay primera"),
    ("ecuador", "ecuador serie a"),
    ("paraguay", "paraguay division profesional"),
    ("nb i", "hungary nb i"),
    ("hungary", "hungary nb i"),
    ("ungheria", "hungary nb i"),
    ("liga i", "romania liga i"),
    ("romania", "romania liga i"),
    ("ukrain", "ukrainian premier league"),
    ("ucraina", "ukrainian premier league"),
    ("austria", "austria bundesliga"),
    ("mls", "mls"),
)


def _hardcoded_baseline(key: str) -> tuple[float, float] | None:
    hits: list[tuple[int, tuple[float, float]]] = []
    for league_name, baseline in LEAGUE_BASELINES.items():
        if league_name == "bundesliga" and "austria" in key:
            continue
        if league_name in key:
            hits.append((len(league_name), baseline))
    if not hits:
        return None
    return max(hits)[1]


def _stored_league_baseline(tournament: str) -> tuple[float, float] | None:
    """Media gol casa/trasferta dello storico importato, quando la lega non ha una baseline fissa."""
    if not tournament or not DB_PATH.exists():
        return None
    token = next((fragment for needle, fragment in _STORED_LEAGUE_TOKENS if needle in tournament), "")
    if not token:
        return None
    averages = _league_averages()
    best: tuple[int, float, float] | None = None
    for name, (home, away, count) in averages.items():
        if token not in name or count < 20:
            continue
        if best is None or count > best[0]:
            best = (count, home, away)
    if best is None:
        return None
    return round(best[1], 3), round(best[2], 3)


def _league_averages() -> dict[str, tuple[float, float, int]]:
    global _LEAGUE_AVERAGE_CACHE
    if _LEAGUE_AVERAGE_CACHE is not None:
        return _LEAGUE_AVERAGE_CACHE
    found: dict[str, tuple[float, float, int]] = {}
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    except sqlite3.Error:
        _LEAGUE_AVERAGE_CACHE = found
        return found
    try:
        rows = conn.execute(
            """
            SELECT league, AVG(home_goals), AVG(away_goals), COUNT(*)
            FROM matches
            WHERE status='FT' AND home_goals IS NOT NULL AND away_goals IS NOT NULL
            GROUP BY league
            """
        )
        for league, home, away, count in rows:
            if league and home is not None and away is not None:
                found[str(league).casefold()] = (float(home), float(away), int(count))
    except sqlite3.Error:
        found = {}
    finally:
        conn.close()
    _LEAGUE_AVERAGE_CACHE = found
    return found


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
        home_rows = _team_games(conn, home, home_side=True, league=tournament)
        away_rows = _team_games(conn, away, home_side=False, league=tournament)
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    # Anche un campione corto entra: lo shrinkage (m=5) lo tira verso la media di lega.
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


def estimate_xg(match: CachedMatch, db_path: Path | None = None) -> tuple[float, float] | None:
    """Solo lo storico delle due squadre. Senza un nome agganciato non si inventa la media di lega."""
    return historical_xg(match.home_team, match.away_team, match.tournament, db_path)


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
    xg_for: Callable[[CachedMatch], tuple[float, float] | None] | None = None,
    context_for: Callable[[CachedMatch], MatchContext] | None = None,
) -> list[NetwinGem]:
    """Ogni mercato quotato da 1.20, con verdetto. Le soglie non scartano più la partita."""
    resolve_xg = xg_for or estimate_xg
    resolve_context = context_for or context_for_match
    gems: list[NetwinGem] = []
    for match in matches:
        try:
            resolved = resolve_xg(match)
        except (TypeError, ValueError):
            continue
        if not resolved:
            continue
        xg_home, xg_away = resolved
        if xg_home <= 0 or xg_away <= 0:
            continue
        catalog = tuple(dict.fromkeys(COMBO_CATALOG + tuple(match.odds_dict.keys())))
        found = rank_quoted_markets(
            xg_home,
            xg_away,
            match.odds_dict,
            resolve_context(match),
            catalog=catalog,
        )
        note = "; ".join(found.notes)
        for combo in found.ranked:
            verdict = market_verdict(combo.edge)
            extra = ""
            if combo.edge < min_edge or combo.probability < min_probability:
                extra = " Fuori dalla banda 70% / +4.5%: il mercato resta in elenco."
            gems.append(
                NetwinGem(
                    tournament=match.tournament,
                    match_name=match.match_name,
                    market=combo.market,
                    book_odd=combo.book_odd,
                    fair_odd=combo.fair_odd,
                    probability=combo.probability,
                    edge=combo.edge,
                    notes=(note + extra).strip(),
                    verdict=verdict,
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


_EDGE_NOISE = frozenset({
    "fc", "cf", "ac", "afc", "cfc", "club", "clube", "ec", "cr", "cd", "sde",
    "rj", "mg", "ba", "pr", "sc", "sp", "rs", "pe", "ce", "go", "es",
    "de", "del", "da", "do", "dos", "das",
})

# Ago del torneo -> frammento del nome salvato in matches.league. Il più lungo vince.
_LEAGUE_HINTS = _STORED_LEAGUE_TOKENS + (
    ("brazil serie a", "brazil serie a"),
    ("brasileirao", "brazil serie a"),
    ("brasile", "brazil serie a"),
    ("serie a brasiliana", "brazil serie a"),
    ("brasiliana", "brazil serie a"),
    ("primera division arg", "primera division arg"),
    ("liga profesional", "primera division arg"),
    ("argentina", "primera division arg"),
    ("premier league", "premier league"),
    ("inghilterra", "premier league"),
    ("la liga", "la liga"),
    ("laliga", "la liga"),
    ("spagna", "la liga"),
    ("bundesliga", "bundesliga"),
    ("germania", "bundesliga"),
    ("ligue 1", "ligue 1"),
    ("francia", "ligue 1"),
    ("primeira liga", "primeira liga"),
    ("portogallo", "primeira liga"),
    ("eredivisie", "eredivisie"),
    ("olanda", "eredivisie"),
    ("scottish premiership", "scottish premiership"),
    ("scozia", "scottish premiership"),
    ("jupiler", "jupiler pro league"),
    ("belgio", "jupiler pro league"),
    ("pro league", "jupiler pro league"),
    ("superliga den", "superliga den"),
    ("danimarca", "superliga den"),
    ("eliteserien", "eliteserien"),
    ("norvegia", "eliteserien"),
    ("allsvenskan", "allsvenskan"),
    ("svezia", "allsvenskan"),
    ("super league greece", "super league greece"),
    ("grecia", "super league greece"),
    ("super lig", "super lig"),
    ("turchia", "super lig"),
    ("swiss super", "swiss super league"),
    ("svizzera", "swiss super league"),
    ("champions league", "champions league"),
    ("europa league", "europa league"),
    ("conference league", "conference league"),
    ("serie a", "serie a"),
    ("italia", "serie a"),
)


_KNOWN_TEAM_ALIASES: dict[str, str] = {
    # Argentina (Netwin -> DB / FootyStats canonical)
    "instituto cordoba": "instituto",
    "talleres de cordoba": "talleres cordoba",
    "talleres cordoba": "talleres cordoba",
    "gimnasia y esgrima mendoza": "gimnasia mendoza",
    "gimnasia esgrima mendoza": "gimnasia mendoza",
    "sarmiento junin": "sarmiento",
    "newells old boys": "newells old boys",
    "central cordoba": "central cordoba sde",
    "racing": "racing club",
    "racing club": "racing club",
    # Brasile
    "atletico mineiro": "atletico mineiro",
    "atletico mg": "atletico mineiro",
    "atletico paranaense": "athletico paranaense",
    "atletico pr": "athletico paranaense",
    "athletico pr": "athletico paranaense",
    "bragantino": "red bull bragantino",
    "rb bragantino": "red bull bragantino",
}


def _normalize_team_name(name: str) -> str:
    s = unicodedata.normalize("NFKD", name).encode("ASCII", "ignore").decode("utf-8")
    s = s.lower()
    s = re.sub(r"['’]", "", s)
    s = re.sub(r"[^a-z0-9]", " ", s)
    return " ".join(s.split())


def _core_tokens(name: str) -> tuple[str, ...]:
    """Toglie solo le sigle ai bordi (FC, PR, RJ). Il corpo del nome resta intero."""
    tokens = _normalize_team_name(name).split()
    changed = True
    while changed and tokens:
        changed = False
        if tokens[0] in _EDGE_NOISE:
            tokens = tokens[1:]
            changed = True
        if tokens and tokens[-1] in _EDGE_NOISE:
            tokens = tokens[:-1]
            changed = True
    return tuple(tokens)


def team_names_match(left: str, right: str) -> bool:
    """Stesso club. «Atlético PR» non è «Atlético Madrid» e «Cerro» non è «Cerro Porteño»."""
    if not left or not right:
        return False
    norm_l = _normalize_team_name(left)
    norm_r = _normalize_team_name(right)
    if norm_l == norm_r:
        return True
    alias_l = _KNOWN_TEAM_ALIASES.get(norm_l, norm_l)
    alias_r = _KNOWN_TEAM_ALIASES.get(norm_r, norm_r)
    if alias_l == norm_r or norm_l == alias_r or alias_l == alias_r:
        return True
    core_l = _core_tokens(left)
    core_r = _core_tokens(right)
    return bool(core_l) and (core_l == core_r or core_l == _core_tokens(alias_r) or _core_tokens(alias_l) == core_r)


def _league_names_for(conn: sqlite3.Connection, tournament: str) -> list[str]:
    key = (tournament or "").casefold().strip()
    if not key:
        return []
    try:
        available = [row[0] for row in conn.execute("SELECT DISTINCT league FROM matches") if row[0]]
    except sqlite3.Error:
        return []
    exact = [name for name in available if name.casefold() == key]
    if exact:
        return exact
    hits = [(len(needle), fragment) for needle, fragment in _LEAGUE_HINTS if needle in key]
    if not hits:
        contained = [name for name in available if name.casefold() in key]
        if not contained:
            return []
        return [max(contained, key=len)]
    fragment = max(hits)[1]
    if fragment == "bundesliga" and "austria" in key:
        fragment = "austria bundesliga"
    exact = [name for name in available if name.casefold() == fragment]
    if exact:
        return exact
    return [name for name in available if fragment in name.casefold()]


def _team_pool(conn: sqlite3.Connection, leagues: list[str]) -> list[str]:
    if leagues:
        marks = ",".join("?" for _ in leagues)
        query = f"""
            SELECT DISTINCT team FROM (
                SELECT home_team AS team FROM matches WHERE league IN ({marks})
                UNION
                SELECT away_team AS team FROM matches WHERE league IN ({marks})
            )
        """
        rows = conn.execute(query, (*leagues, *leagues))
    else:
        rows = conn.execute(
            """
            SELECT DISTINCT team FROM (
                SELECT home_team AS team FROM matches
                UNION
                SELECT away_team AS team FROM matches
            )
            """
        )
    return [row[0] for row in rows if row[0]]


def _unique_team(raw_name: str, pool: list[str], *, loose: bool) -> str:
    if not raw_name or not pool:
        return ""
    norm = _normalize_team_name(raw_name)
    alias = _KNOWN_TEAM_ALIASES.get(norm, norm)
    exact = [team for team in pool if _normalize_team_name(team) in (norm, alias)]
    if len(set(exact)) == 1:
        return exact[0]
    if len(set(exact)) > 1:
        for t in exact:
            if _normalize_team_name(t) == alias:
                return t
        return exact[0]
    if not loose:
        return ""
    core = _core_tokens(raw_name)
    core_alias = _core_tokens(alias)
    if not core:
        return ""
    loose_hits = [team for team in pool if _core_tokens(team) in (core, core_alias)]
    if len(set(loose_hits)) == 1:
        return loose_hits[0]
    if len(set(loose_hits)) > 1:
        for t in loose_hits:
            if _normalize_team_name(t) == alias:
                return t
    return ""


def _find_matching_team(
    conn: sqlite3.Connection,
    raw_name: str,
    *,
    home_side: bool,
    league: str = "",
) -> str:
    """Il nome si risolve nel campionato della partita. Fuori da lì solo se il nome è unico."""
    del home_side
    if not raw_name:
        return ""
    try:
        leagues = _league_names_for(conn, league)
        if leagues:
            chosen = _unique_team(raw_name, _team_pool(conn, leagues), loose=True)
            if chosen:
                return chosen
        return _unique_team(raw_name, _team_pool(conn, []), loose=False)
    except sqlite3.Error:
        return ""


def _team_games(
    conn: sqlite3.Connection,
    team: str,
    *,
    home_side: bool,
    league: str = "",
) -> list[tuple[float, float]]:
    db_team = _find_matching_team(conn, team, home_side=home_side, league=league)
    if not db_team:
        return []
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

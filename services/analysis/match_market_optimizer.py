"""Scansiona i mercati Netwin di una partita: gol, corner e cartellini.

Le quote arrivano da data/netwin_live_odds.json. I gol arrivano da DixonColesMLE
sul database, oppure dallo shrinkage se la squadra non è nel fit. I corner usano
la binomiale negativa, i cartellini il Poisson, entrambi sulle medie storiche
della lega. Le linee standard entrano anche quando Netwin non le quota.
Nessuna chiamata di rete.
"""

from __future__ import annotations

import logging
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.stats import poisson

from services.analysis.dixon_coles_mle import DixonColesMLE
from services.analysis.xg_poisson_engine import QuantitativeEngine, _goal_market_mask
from services.betting.netwin_cache_reader import (
    DEFAULT_CACHE,
    CachedMatch,
    historical_xg,
    load_cached_matches,
    split_teams,
    team_names_match,
    tournament_baseline,
    _league_names_for,
)
from services.database.schema import DB_PATH

logger = logging.getLogger(__name__)

# Due o tre partite non identificano un attacco. Sotto questa soglia il MLE si scarta.
MIN_DIXON_COLES_SAMPLE = 8
# Oltre questo scarto sull'1 il modello piccolo non viene pubblicato così com'è.
MAX_1X2_GAP = 0.38

_FIRST_HALF = re.compile(
    r"\b(?:1\s*°?\s*tempo|1\s*°?\s*t|primo\s+tempo|1h)\b",
    re.IGNORECASE,
)
_HALF_SHARE = 0.45
_CORNER_BASE = (5.4, 4.6)
_CARD_BASE = (2.3, 2.1)
_COUNT_LINE = re.compile(r"\b(over|under)\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE)
_COUNT_SIGN = re.compile(r"^\s*(1x|x2|12|1|x|2)\b", re.IGNORECASE)
_CORNER_WORD = re.compile(r"corner|angol|calci d'angolo", re.IGNORECASE)
_CARD_WORD = re.compile(r"cartellin|sanzion|ammoniz|\bcards?\b", re.IGNORECASE)

_CORNER_LINES = (6.5, 7.5, 8.5, 9.5, 10.5)
_CORNER_TEAM_LINES = (3.5, 4.5, 5.5)
_CARD_LINES = (2.5, 3.5, 4.5, 5.5)
_CARD_TEAM_LINES = (1.5, 2.5)

ALTERNATIVES: dict[str, tuple[str, ...]] = {
    "1": (
        "1X + MultiGol 2-5",
        "1X + Over 1.5",
        "Chance Mix: 1X o Gol",
        "1X + MultiGol 1-4",
    ),
    "2": (
        "X2 + MultiGol 1-5",
        "X2 + Over 1.5",
        "Chance Mix: X2 o Gol",
    ),
    "Under 2.5": (
        "Under 3.5",
        "MultiGol 1-3",
        "1X + Under 3.5",
    ),
    "Over 2.5": (
        "Over 1.5",
        "MultiGol 2-4",
        "1X + Over 1.5",
    ),
}

SCENARIOS: dict[tuple[str, str], str] = {
    ("1", "1X + MultiGol 2-5"): "Protegge il pareggio 1-1 e 2-2, che fanno perdere l'1 fisso.",
    ("1", "1X + Over 1.5"): "Protegge l'1-1. Perde ancora sull'1-0.",
    ("1", "Chance Mix: 1X o Gol"): "Perde solo sullo 0-1: il pareggio resta dentro.",
    ("1", "1X + MultiGol 1-4"): "Protegge il pareggio fino a 4 gol. L'1-0 resta dentro il MultiGol.",
    ("2", "X2 + MultiGol 1-5"): "Protegge il pareggio, che fa perdere il 2 fisso.",
    ("2", "X2 + Over 1.5"): "Protegge l'1-1. Perde ancora sullo 0-1.",
    ("2", "Chance Mix: X2 o Gol"): "Perde solo sull'1-0.",
    ("Under 2.5", "Under 3.5"): "Allarga il tetto: il 3-0 e il 2-1 non rompono più l'Under 2.5.",
    ("Under 2.5", "MultiGol 1-3"): "Chiede almeno un gol e tiene il tetto a 3.",
    ("Under 2.5", "1X + Under 3.5"): "Aggiunge il segno casa-pareggio al tetto dei 3 gol.",
    ("Over 2.5", "Over 1.5"): "Basta un secondo gol: non serve arrivare a 3.",
    ("Over 2.5", "MultiGol 2-4"): "Tiene la banda 2-4 gol, senza escludere il 2-0.",
    ("Over 2.5", "1X + Over 1.5"): "Unisce il segno casa-pareggio a almeno due gol.",
}


@dataclass(frozen=True)
class PricedMarket:
    market: str
    odd: float | None
    probability: float
    fair_odd: float
    edge: float | None
    resilience: str


@dataclass(frozen=True)
class ComboAlternative:
    single: str
    single_odd: float | None
    single_probability: float
    alternative: str
    alternative_odd: float | None
    alternative_probability: float
    delta_p: float
    scenario: str


@dataclass(frozen=True)
class MatchScan:
    match_name: str
    home_team: str
    away_team: str
    tournament: str
    kickoff: str
    lambda_home: float
    lambda_away: float
    rho: float
    source: str
    sample_home: int | None
    sample_away: int | None
    corner_home: float
    corner_away: float
    card_home: float
    card_away: float
    count_source: str
    markets: tuple[PricedMarket, ...]


class MatchMarketOptimizer:
    """Prezza ogni mercato quotato di una partita e propone le combo che alzano P."""

    def __init__(
        self,
        odds_path: Path | None = None,
        db_path: Path | None = None,
        xg_home: float | None = None,
        xg_away: float | None = None,
        rho: float | None = None,
        corner_home: float | None = None,
        corner_away: float | None = None,
        card_home: float | None = None,
        card_away: float | None = None,
    ):
        self.odds_path = odds_path or DEFAULT_CACHE
        self.db_path = db_path or DB_PATH
        self._xg_override = (xg_home, xg_away) if xg_home is not None and xg_away is not None else None
        self._rho_override = rho
        self._corner_override = (
            (corner_home, corner_away) if corner_home is not None and corner_away is not None else None
        )
        self._card_override = (
            (card_home, card_away) if card_home is not None and card_away is not None else None
        )
        self._fits: dict[str, DixonColesMLE | None] = {}
        self.scan_result: MatchScan | None = None

    def scan(self, match: str = "", home: str = "", away: str = "") -> MatchScan:
        found = self.find_match(match, home, away)
        lam_home, lam_away, rho, source, sample_home, sample_away = self.lambdas_for(found)
        corner_home, corner_away, card_home, card_away, count_source = self.counts_for(found)
        markets = tuple(
            sorted(
                self._price_book(
                    found.odds_dict,
                    lam_home,
                    lam_away,
                    rho,
                    corner_home,
                    corner_away,
                    card_home,
                    card_away,
                ),
                key=lambda row: row.probability,
                reverse=True,
            )
        )
        result = MatchScan(
            match_name=found.match_name,
            home_team=found.home_team,
            away_team=found.away_team,
            tournament=found.tournament,
            kickoff=found.kickoff,
            lambda_home=lam_home,
            lambda_away=lam_away,
            rho=rho,
            source=source,
            sample_home=sample_home,
            sample_away=sample_away,
            corner_home=corner_home,
            corner_away=corner_away,
            card_home=card_home,
            card_away=card_away,
            count_source=count_source,
            markets=markets,
        )
        self.scan_result = result
        return result

    def find_match(self, match: str = "", home: str = "", away: str = "") -> CachedMatch:
        rows = load_cached_matches(path=self.odds_path)
        home_query, away_query = home.strip(), away.strip()
        if not home_query or not away_query:
            left, right = split_teams(match, match.replace(" - ", " vs "))
            home_query = home_query or left
            away_query = away_query or right
        if home_query and away_query:
            hits = [
                row for row in rows
                if team_names_match(row.home_team, home_query) and team_names_match(row.away_team, away_query)
            ]
        else:
            needle = home_query or match.strip()
            hits = [
                row for row in rows
                if team_names_match(row.home_team, needle) or team_names_match(row.away_team, needle)
                or needle.casefold() in row.match_name.casefold()
            ]
        if not hits:
            raise LookupError(f"Nessuna partita in cache per {match or home or away!r}")
        if len(hits) > 1 and not (home_query and away_query):
            names = ", ".join(row.match_name for row in hits[:8])
            raise LookupError(f"Più partite per {match!r}: {names}")
        return hits[0]

    def lambdas_for(self, match: CachedMatch) -> tuple[float, float, float, str, int | None, int | None]:
        if self._xg_override is not None:
            rho = -0.05 if self._rho_override is None else self._rho_override
            return self._xg_override[0], self._xg_override[1], rho, "override", None, None
        self._rejected_sample = None
        fitted = self._dixon_coles(match)
        if fitted is not None:
            chosen = fitted
        else:
            home_n, away_n = self._rejected_sample or self._count_samples(match)
            historic = historical_xg(match.home_team, match.away_team, match.tournament, self.db_path)
            if historic is not None:
                chosen = (historic[0], historic[1], -0.05, "poisson-shrinkage", home_n, away_n)
            else:
                base_home, base_away = tournament_baseline(match.tournament)
                chosen = (base_home, base_away, -0.05, "baseline", home_n, away_n)
        return self._guard_market_divergence(match, chosen)

    def counts_for(self, match: CachedMatch) -> tuple[float, float, float, float, str]:
        if self._corner_override is not None:
            corner_home, corner_away, corner_source = (*self._corner_override, "override")
        else:
            corner_home, corner_away, corner_source = _event_rates(
                self.db_path, match, "corners", _CORNER_BASE
            )
        if self._card_override is not None:
            card_home, card_away, card_source = (*self._card_override, "override")
        else:
            card_home, card_away, card_source = _event_rates(
                self.db_path, match, "cards", _CARD_BASE
            )
        source = corner_source if corner_source == card_source else "storico"
        return corner_home, corner_away, card_home, card_away, source

    def get_highest_probability_markets(self, min_odd: float = 1.15, limit: int = 20) -> tuple[PricedMarket, ...]:
        rows = self._require().markets
        picked = [row for row in rows if row.odd is not None and row.odd >= min_odd]
        return tuple(picked[:limit])

    def sweet_spot(self, min_probability: float = 0.70) -> tuple[PricedMarket, ...]:
        return tuple(
            row for row in self._require().markets
            if row.odd is not None
            and row.edge is not None
            and row.probability >= min_probability
            and 1.25 <= row.odd <= 1.80
            and row.edge > 0
        )

    def find_alternative_combos(self, target_single_family: str = "1X2") -> tuple[ComboAlternative, ...]:
        priced = {row.market: row for row in self._require().markets}
        singles = _singles_for(target_single_family, priced)
        found: list[ComboAlternative] = []
        for single_name in singles:
            base = priced.get(single_name)
            if base is None:
                continue
            for alternative_name in ALTERNATIVES.get(single_name, ()):
                alternative = priced.get(alternative_name)
                if alternative is None:
                    continue
                found.append(
                    ComboAlternative(
                        single=single_name,
                        single_odd=base.odd,
                        single_probability=base.probability,
                        alternative=alternative_name,
                        alternative_odd=alternative.odd,
                        alternative_probability=alternative.probability,
                        delta_p=alternative.probability - base.probability,
                        scenario=SCENARIOS.get(
                            (single_name, alternative_name),
                            "Copre esiti che il singolo lascia fuori.",
                        ),
                    )
                )
        return tuple(found)

    def probability_of(self, market: str) -> float | None:
        for row in self._require().markets:
            if row.market == market:
                return row.probability
        lam_home = self.scan_result.lambda_home if self.scan_result else None
        if lam_home is None:
            return None
        return _probability(market, *_matrices(lam_home, self.scan_result.lambda_away, self.scan_result.rho))

    def _price_book(
        self,
        odds: dict[str, float],
        lam_home: float,
        lam_away: float,
        rho: float,
        corner_home: float,
        corner_away: float,
        card_home: float,
        card_away: float,
    ) -> list[PricedMarket]:
        full, half = _matrices(lam_home, lam_away, rho)
        corners = _count_axes(corner_home, corner_away, kind="corner")
        cards = _count_axes(card_home, card_away, kind="cards")
        book = dict(odds)
        for name in _count_catalog():
            book.setdefault(name, None)
        priced: list[PricedMarket] = []
        for market, odd in book.items():
            if odd is not None and odd <= 1.0:
                continue
            probability = _any_probability(market, full, half, corners, cards)
            if probability is None or probability <= 0.0:
                continue
            quoted = float(odd) if odd is not None else None
            priced.append(
                PricedMarket(
                    market=market,
                    odd=quoted,
                    probability=probability,
                    fair_odd=1.0 / probability,
                    edge=None if quoted is None else (probability * quoted) - 1.0,
                    resilience=_resilience(market),
                )
            )
        return priced

    def _dixon_coles(self, match: CachedMatch) -> tuple[float, float, float, str, int | None, int | None] | None:
        if not self.db_path.exists():
            return None
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        except sqlite3.Error:
            return None
        try:
            leagues = _league_names_for(conn, match.tournament)
        finally:
            conn.close()
        for league in leagues:
            engine = self._fit_league(league)
            if engine is None or engine.result is None:
                continue
            home = _resolve_team(match.home_team, engine.result.attack_params)
            away = _resolve_team(match.away_team, engine.result.attack_params)
            if home is None or away is None:
                continue
            try:
                lam_home, lam_away = engine.predict_lambdas(home, away)
            except KeyError:
                continue
            sizes = engine.result.sample_sizes
            home_n = int(sizes.get(home) or 0)
            away_n = int(sizes.get(away) or 0)
            if min(home_n, away_n) < MIN_DIXON_COLES_SAMPLE:
                logger.warning(
                    "Dixon-Coles scartato per %s: campione %s/%s sotto %s",
                    match.match_name,
                    home_n,
                    away_n,
                    MIN_DIXON_COLES_SAMPLE,
                )
                self._rejected_sample = (home_n, away_n)
                return None
            return (
                lam_home,
                lam_away,
                engine.result.rho,
                "dixon-coles",
                home_n,
                away_n,
            )
        return None

    def _guard_market_divergence(self, match: CachedMatch, chosen: tuple) -> tuple:
        lam_home, lam_away, rho, source, home_n, away_n = chosen
        small = home_n is not None and away_n is not None and min(home_n, away_n) < MIN_DIXON_COLES_SAMPLE
        implied = _implied_1x2(match.odds_dict)
        if implied is None:
            if not small:
                return chosen
            base_home, base_away = tournament_baseline(match.tournament)
            tilted_home, tilted_away = _temper_total(base_home, base_away, match.odds_dict)
            logger.warning(
                "Campione %s/%s sotto %s su %s e 1X2 assente: uso la media di lega",
                home_n,
                away_n,
                MIN_DIXON_COLES_SAMPLE,
                match.match_name,
            )
            return tilted_home, tilted_away, -0.05, "baseline-sanity", home_n, away_n
        model_home = _outcome_probs(lam_home, lam_away, rho)[0]
        gap = abs(model_home - implied[0])
        if gap > MAX_1X2_GAP:
            logger.warning(
                "Divergenza 1X2 di %.0f punti su %s: modello %.0f%%, quota implicita %.0f%%",
                gap * 100,
                match.match_name,
                model_home * 100,
                implied[0] * 100,
            )
        trusted = source == "dixon-coles" and not small
        if trusted and gap <= MAX_1X2_GAP:
            return chosen
        if trusted:
            base_home, base_away = tournament_baseline(match.tournament)
            return (
                0.5 * lam_home + 0.5 * base_home,
                0.5 * lam_away + 0.5 * base_away,
                -0.05,
                "dixon-coles-shrunk",
                home_n,
                away_n,
            )
        if not small and gap <= MAX_1X2_GAP:
            return chosen
        tilted_home, tilted_away = _baseline_tilt(match.tournament, implied)
        if small:
            tilted_home, tilted_away = _temper_total(tilted_home, tilted_away, match.odds_dict)
        return tilted_home, tilted_away, -0.05, "baseline-sanity", home_n, away_n

    def _count_samples(self, match: CachedMatch) -> tuple[int, int]:
        if not self.db_path.exists():
            return 0, 0
        try:
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True)
        except sqlite3.Error:
            return 0, 0
        try:
            leagues = _league_names_for(conn, match.tournament)
            if not leagues:
                return 0, 0
            marks = ",".join("?" for _ in leagues)
            rows = conn.execute(
                f"""
                SELECT home_team, away_team FROM matches
                WHERE status = 'FT' AND league IN ({marks})
                  AND home_goals IS NOT NULL AND away_goals IS NOT NULL
                """,
                tuple(leagues),
            ).fetchall()
        except sqlite3.Error:
            return 0, 0
        finally:
            conn.close()
        home_n = sum(1 for home, away in rows if team_names_match(match.home_team, home) or team_names_match(match.home_team, away))
        away_n = sum(1 for home, away in rows if team_names_match(match.away_team, home) or team_names_match(match.away_team, away))
        return home_n, away_n

    def _fit_league(self, league: str) -> DixonColesMLE | None:
        if league in self._fits:
            return self._fits[league]
        season = _busiest_season(self.db_path, league)
        engine = DixonColesMLE()
        try:
            engine.fit_from_db(self.db_path, league, season)
        except (OSError, ValueError, sqlite3.Error):
            engine = None
        self._fits[league] = engine
        return engine

    def _require(self) -> MatchScan:
        if self.scan_result is None:
            raise RuntimeError("Chiama scan prima di leggere i mercati")
        return self.scan_result


def _implied_1x2(odds: dict[str, float]) -> tuple[float, float, float] | None:
    for keys in (("1", "X", "2"), ("1 + Over 1.5", "X + Over 1.5", "2 + Over 1.5")):
        parsed = _devig(odds, keys)
        if parsed is not None:
            return parsed
    return None


def _devig(odds: dict[str, float], keys: tuple[str, str, str]) -> tuple[float, float, float] | None:
    prices = []
    for key in keys:
        odd = odds.get(key)
        if odd is None or odd <= 1.0:
            return None
        prices.append(1.0 / float(odd))
    total = sum(prices)
    if total <= 0.0:
        return None
    return prices[0] / total, prices[1] / total, prices[2] / total


def _outcome_probs(lam_home: float, lam_away: float, rho: float) -> tuple[float, float, float]:
    full, _half = _matrices(lam_home, lam_away, rho)
    home, away, total = _axes(full)
    return tuple(
        float(np.sum(full[_goal_market_mask(name, home, away, total)]))
        for name in ("1", "X", "2")
    )


def _temper_total(lam_home: float, lam_away: float, odds: dict[str, float]) -> tuple[float, float]:
    """Avvicina il totale gol alla linea 2.5 quotata, senza copiarla."""
    under = odds.get("Under 2.5")
    over = odds.get("Over 2.5")
    if under is None or over is None or under <= 1.0 or over <= 1.0:
        return lam_home, lam_away
    implied_under = (1.0 / under) / ((1.0 / under) + (1.0 / over))
    current = _under_prob(lam_home, lam_away)
    target = (0.25 * current) + (0.75 * implied_under)
    low, high = 0.45, 2.2
    for _ in range(14):
        scale = (low + high) / 2.0
        if _under_prob(lam_home * scale, lam_away * scale) > target:
            low = scale
        else:
            high = scale
    scale = (low + high) / 2.0
    return lam_home * scale, lam_away * scale


def _under_prob(lam_home: float, lam_away: float) -> float:
    full, _half = _matrices(lam_home, lam_away, -0.05)
    home, away, total = _axes(full)
    mask = _goal_market_mask("Under 2.5", home, away, total)
    if mask is None:
        return 0.5
    return float(np.sum(full[mask]))


def _baseline_tilt(tournament: str, implied: tuple[float, float, float]) -> tuple[float, float]:
    """Media di lega, inclinata appena verso il segno che il book considera favorito."""
    base_home, base_away = tournament_baseline(tournament)
    tilt = (implied[0] / max(implied[2], 0.05)) ** 0.35
    return (
        min(3.2, max(0.35, base_home * tilt)),
        min(3.2, max(0.25, base_away / tilt)),
    )


def _singles_for(family: str, priced: dict[str, PricedMarket]) -> tuple[str, ...]:
    key = family.strip().upper()
    if key in {"1X2", "ESITO", "SINGOLO"}:
        return tuple(name for name in ("1", "2", "Under 2.5", "Over 2.5") if name in priced)
    if key in ALTERNATIVES:
        return (key,)
    return tuple(name for name in ALTERNATIVES if name in priced)


def _matrices(lam_home: float, lam_away: float, rho: float):
    engine = QuantitativeEngine(rho=rho)
    full = engine.generate_score_matrix(lam_home, lam_away, max_goals=8)
    half = engine.generate_score_matrix(lam_home * _HALF_SHARE, lam_away * _HALF_SHARE, max_goals=8)
    return full, half


def _axes(matrix: np.ndarray):
    goals = np.arange(matrix.shape[0])
    home = goals[:, None]
    away = goals[None, :]
    return home, away, home + away


def _probability(market: str, full: np.ndarray, half: np.ndarray) -> float | None:
    if _FIRST_HALF.search(market):
        home, away, total = _axes(half)
        mask = _goal_market_mask(market, home, away, total)
        grid = half
    else:
        home, away, total = _axes(full)
        mask = _goal_market_mask(market, home, away, total)
        grid = full
    if mask is None:
        return None
    return float(np.sum(grid[mask]))


def _count_catalog() -> tuple[str, ...]:
    names: list[str] = []
    for line in _CORNER_LINES:
        names.extend((f"Over {line} Corner", f"Under {line} Corner"))
    for line in _CORNER_TEAM_LINES:
        for side in ("Casa", "Ospite"):
            names.extend((f"Over {line} Corner {side}", f"Under {line} Corner {side}"))
    names.extend(("1 Corner", "X Corner", "2 Corner"))
    for line in _CARD_LINES:
        names.extend((f"Over {line} Cartellini", f"Under {line} Cartellini"))
    for line in _CARD_TEAM_LINES:
        for side in ("Casa", "Ospite"):
            names.extend((f"Over {line} Cartellini {side}", f"Under {line} Cartellini {side}"))
    names.extend(("1 Cartellini", "X Cartellini", "2 Cartellini"))
    return tuple(names)


def _count_axes(mu_home: float, mu_away: float, kind: str):
    if kind == "corner":
        matrix, home, away, total = QuantitativeEngine()._corner_axes(
            max(0.2, mu_home),
            max(0.2, mu_away),
            max_corners=25,
        )
    else:
        index = np.arange(16)
        matrix = np.outer(poisson.pmf(index, max(0.05, mu_home)), poisson.pmf(index, max(0.05, mu_away)))
        home = index[:, None]
        away = index[None, :]
        total = home + away
    mass = float(matrix.sum())
    if mass > 0.0:
        matrix = matrix / mass
    return matrix, home, away, total


def _any_probability(market, full, half, corners, cards) -> float | None:
    if _CORNER_WORD.search(market):
        return _count_probability(market, *corners)
    if _CARD_WORD.search(market):
        return _count_probability(market, *cards)
    return _probability(market, full, half)


def _count_probability(market: str, matrix: np.ndarray, home: np.ndarray, away: np.ndarray, total: np.ndarray) -> float | None:
    raw = market.casefold()
    if re.search(r"\b(casa|home)\b", raw):
        series = home
    elif re.search(r"\b(ospite|away)\b", raw):
        series = away
    else:
        series = total
    parsed = _COUNT_LINE.search(market)
    if parsed:
        line = float(parsed.group(2).replace(",", "."))
        mask = series > line if parsed.group(1).casefold() == "over" else series < line
        return float(np.sum(matrix[np.broadcast_to(mask, matrix.shape)]))
    sign = _COUNT_SIGN.match(raw)
    if sign is None:
        return None
    token = sign.group(1).casefold()
    if token == "1":
        mask = home > away
    elif token == "2":
        mask = away > home
    elif token == "x":
        mask = home == away
    elif token == "1x":
        mask = home >= away
    elif token == "x2":
        mask = away >= home
    else:
        mask = home != away
    return float(np.sum(matrix[mask]))


def _event_rates(
    db_path: Path,
    match: CachedMatch,
    kind: str,
    baseline: tuple[float, float],
) -> tuple[float, float, str]:
    if not db_path.exists():
        return baseline[0], baseline[1], "baseline"
    if kind == "corners":
        home_sql, away_sql = "home_corners", "away_corners"
        present = "home_corners IS NOT NULL AND away_corners IS NOT NULL"
    else:
        home_sql = "COALESCE(home_yellow_cards, 0) + COALESCE(home_red_cards, 0)"
        away_sql = "COALESCE(away_yellow_cards, 0) + COALESCE(away_red_cards, 0)"
        present = "home_yellow_cards IS NOT NULL AND away_yellow_cards IS NOT NULL"
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return baseline[0], baseline[1], "baseline"
    try:
        leagues = _league_names_for(conn, match.tournament)
        if not leagues:
            return baseline[0], baseline[1], "baseline"
        marks = ",".join("?" for _ in leagues)
        rows = conn.execute(
            f"""
            SELECT home_team, away_team, {home_sql}, {away_sql}
            FROM matches
            WHERE status = 'FT' AND league IN ({marks}) AND {present}
            """,
            tuple(leagues),
        ).fetchall()
    except sqlite3.Error:
        return baseline[0], baseline[1], "baseline"
    finally:
        conn.close()
    if len(rows) < 8:
        return baseline[0], baseline[1], "baseline"
    league_home = sum(float(row[2]) for row in rows) / len(rows)
    league_away = sum(float(row[3]) for row in rows) / len(rows)
    home_name = _resolve_team(match.home_team, {str(row[0]): 1.0 for row in rows} | {str(row[1]): 1.0 for row in rows})
    away_name = _resolve_team(match.away_team, {str(row[0]): 1.0 for row in rows} | {str(row[1]): 1.0 for row in rows})
    mu_home = _shrunk_for_rate(rows, home_name, league_home)
    mu_away = _shrunk_for_rate(rows, away_name, league_away)
    return mu_home, mu_away, "storico"


def _shrunk_for_rate(rows: list, team: str | None, prior: float, strength: float = 5.0) -> float:
    if not team:
        return max(0.2, prior)
    produced = [
        float(row[2]) if row[0] == team else float(row[3])
        for row in rows
        if row[0] == team or row[1] == team
    ]
    if not produced:
        return max(0.2, prior)
    rate = (sum(produced) + strength * prior) / (len(produced) + strength)
    return max(0.2, rate)


def _resilience(market: str) -> str:
    folded = market.upper()
    if folded in {"1", "2"} or folded.startswith("1 +") or folded.startswith("2 +"):
        return "bassa"
    if any(token in folded for token in ("1X", "X2", "CHANCE MIX", "DNB")):
        return "alta"
    return "media"


def _resolve_team(label: str, params: dict[str, float]) -> str | None:
    for name in params:
        if team_names_match(label, name):
            return name
    return None


def _busiest_season(db_path: Path, league: str) -> str | None:
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    except sqlite3.Error:
        return None
    try:
        row = conn.execute(
            """
            SELECT season FROM matches
            WHERE status = 'FT' AND league = ? AND home_goals IS NOT NULL
            GROUP BY season
            ORDER BY COUNT(*) DESC
            LIMIT 1
            """,
            (league,),
        ).fetchone()
    except sqlite3.Error:
        return None
    finally:
        conn.close()
    if row is None or row[0] is None:
        return None
    return str(row[0])

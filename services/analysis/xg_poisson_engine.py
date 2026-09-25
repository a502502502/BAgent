"""
Expected Goals (xG) & Bivariate Dixon-Coles Poisson Engine + Negative Binomial Corners
Ottimizzato con NumPy/SciPy per calcoli vettoriali ad alte prestazioni.
"""

from __future__ import annotations
import re
import numpy as np
from scipy.stats import poisson, nbinom
from typing import Dict, Any, List, Optional

_NON_GOAL_TOKENS = ("corner", "cartellin", "tiri", "falli")
_PERIOD_MARKET = re.compile(r"tempo|\b[12]\s*°?\s*t\b|entrambi i tempi")
_CLAUSE_PREFIX = re.compile(r"^(?:chance mix|doppia chance|esito finale|dc)\s+")
_SIDE_WORDS = re.compile(
    r"\b(?:casa|ospite|home|away|squadra\s*[12]|squadra|gol|totali|partita|match)\b"
)


def _normalize_market_name(market_name: str) -> str:
    name = market_name.strip().lower().replace("–", "-").replace("—", "-")
    name = name.replace("+", " + ").replace(":", " ")
    name = re.sub(r"\([^)]*\)", " ", name)
    return re.sub(r"\s+", " ", name).strip()


def _market_clauses(name: str) -> tuple[str, list[str]]:
    if " o " in name:
        parts = [part.strip() for part in name.split(" o ") if part.strip()]
        return "or", parts
    if " + " in name:
        parts = [part.strip() for part in name.split(" + ") if part.strip()]
        return "and", parts
    return "and", [name]


def _clause_side(clause: str) -> Optional[str]:
    if re.search(r"\b(?:casa|home)\b", clause) or re.search(r"squadra\s*1\b", clause):
        return "home"
    if re.search(r"\b(?:ospite|away)\b", clause) or re.search(r"squadra\s*2\b", clause):
        return "away"
    if re.search(r"\bsquadra\b", clause):
        return "ambiguous"
    return "total"


def _goal_clause_mask(clause: str, home: np.ndarray, away: np.ndarray, total: np.ndarray) -> Optional[np.ndarray]:
    clause = _CLAUSE_PREFIX.sub("", clause).strip()
    clause = re.sub(r"\s+(?:si|sì|yes)$", "", clause).strip()
    side = _clause_side(clause)
    if side == "ambiguous":
        return None
    series = {"home": home, "away": away, "total": total}[side]
    if clause in {"gol", "gg", "btts", "gol gol", "gol/gol"} or ("entrambe" in clause and "segn" in clause):
        if side != "total":
            return None
        return (home >= 1) & (away >= 1)
    if clause in {"no gol", "ng"}:
        return ~((home >= 1) & (away >= 1))

    core = re.sub(r"\s+", " ", _SIDE_WORDS.sub(" ", clause)).strip()

    over = re.fullmatch(r"over\s*(\d+(?:\.\d+)?)", core)
    under = re.fullmatch(r"under\s*(\d+(?:\.\d+)?)", core)
    if over or under:
        line = float((over or under).group(1))
        band = series > line if over else series < line
        return np.broadcast_to(band, total.shape)

    multigol = re.fullmatch(r"multigol\s*(\d+)\s*-\s*(\d+)", core)
    if multigol:
        low, high = int(multigol.group(1)), int(multigol.group(2))
        band = (series >= low) & (series <= high)
        return np.broadcast_to(band, total.shape)

    results = {
        "1": home > away,
        "1 fisso": home > away,
        "2": away > home,
        "2 fisso": away > home,
        "1x": home >= away,
        "x2": away >= home,
        "12": home != away,
        "x": home == away,
        "pareggio": home == away,
    }
    return results.get(core)


def _goal_market_mask(
    market_name: str,
    home: np.ndarray,
    away: np.ndarray,
    total: np.ndarray,
) -> Optional[np.ndarray]:
    """Maschera del mercato. 'o' è unione, '+' è intersezione. None se il nome non è un mercato gol."""
    raw = market_name.lower()
    if any(token in raw for token in _NON_GOAL_TOKENS) or _PERIOD_MARKET.search(raw):
        return None
    operator, clauses = _market_clauses(_normalize_market_name(market_name))
    combined: Optional[np.ndarray] = None
    for clause in clauses:
        mask = _goal_clause_mask(clause, home, away, total)
        if mask is None:
            return None
        if combined is None:
            combined = mask
        elif operator == "or":
            combined = combined | mask
        else:
            combined = combined & mask
    return combined


class QuantitativeEngine:
    """
    Motore quantitativo unificato per Calcio (Poisson/Dixon-Coles) e Corner (Binomiale Negativa).
    """

    def __init__(self, rho: float = -0.05):
        # rho: fattore di correlazione per bassi punteggi. 
        # TODO: In futuro, passa un dizionario {league: rho} per calibrazione specifica.
        self.rho = rho

    def generate_score_matrix(self, xg_home: float, xg_away: float, max_goals: int = 7) -> np.ndarray:
        """
        Genera la matrice di probabilità per ogni punteggio esatto [home_goals][away_goals] 
        usando operazioni vettoriali NumPy (molto più veloce dei cicli for).
        """
        # 1. Calcolo vettoriale delle PMF di Poisson
        goals_range = np.arange(max_goals)
        p_home = poisson.pmf(goals_range, xg_home)
        p_away = poisson.pmf(goals_range, xg_away)

        # 2. Matrice base (prodotto esterno)
        matrix = np.outer(p_home, p_away)

        # 3. Applicazione vettoriale della correzione Dixon-Coles Tau
        tau = np.ones((max_goals, max_goals), dtype=float)
        
        # Casi speciali Dixon-Coles
        if xg_home > 0 and xg_away > 0:
            tau[0, 0] = 1.0 - (xg_home * xg_away * self.rho)
            tau[0, 1] = 1.0 + (xg_home * self.rho)
            tau[1, 0] = 1.0 + (xg_away * self.rho)
            tau[1, 1] = 1.0 - self.rho

        # Applica la correzione
        matrix *= tau

        # 4. Normalizzazione per assicurare che la somma sia 1.0
        return matrix / matrix.sum()

    def analyze_football_markets(
        self,
        home_team: str,
        away_team: str,
        xg_home: float,
        xg_away: float,
        bookmaker_odds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Analizza i mercati calcistici usando slicing vettoriale NumPy."""
        matrix = self.generate_score_matrix(xg_home, xg_away)
        book_odds = bookmaker_odds or {}

        # Slicing vettoriale per probabilità (estremamente veloce)
        prob_home = np.tril(matrix, -1).sum()       # i > j
        prob_draw = np.diag(matrix).sum()           # i == j
        prob_away = np.triu(matrix, 1).sum()        # i < j
        
        prob_1x = prob_home + prob_draw
        prob_x2 = prob_draw + prob_away

        # Griglia per calcoli basati sulla somma dei gol (i + j)
        goals_range = np.arange(matrix.shape[0])
        total_goals_grid = goals_range[:, None] + goals_range[None, :]

        prob_over_1_5 = np.sum(matrix[total_goals_grid > 1.5])
        prob_over_2_5 = np.sum(matrix[total_goals_grid > 2.5])
        prob_under_3_5 = np.sum(matrix[total_goals_grid < 3.5])
        
        prob_mg_1_4 = np.sum(matrix[(total_goals_grid >= 1) & (total_goals_grid <= 4)])
        prob_mg_2_4 = np.sum(matrix[(total_goals_grid >= 2) & (total_goals_grid <= 4)])

        # MultiGol Casa (es. 1-2 gol casa: righe 1 e 2, tutte le colonne)
        prob_home_mg_1_2 = matrix[1:3, :].sum()
        prob_home_over_1_5 = matrix[2:, :].sum()

        # Combo Protette
        # 1X + Over 1.5: (i >= j) AND (i + j > 1.5)
        mask_1x_over = (goals_range[:, None] >= goals_range[None, :]) & (total_goals_grid > 1.5)
        prob_1x_over_1_5 = np.sum(matrix[mask_1x_over])

        mask_1x_mg = (goals_range[:, None] >= goals_range[None, :]) & ((total_goals_grid >= 1) & (total_goals_grid <= 4))
        prob_1x_mg_1_4 = np.sum(matrix[mask_1x_mg])

        markets = {
            "MultiGol 1-2 Casa": {"prob": round(prob_home_mg_1_2, 3), "fair_odds": round(1.0 / max(0.01, prob_home_mg_1_2), 2)},
            "MultiGol 2-4 Totale": {"prob": round(prob_mg_2_4, 3), "fair_odds": round(1.0 / max(0.01, prob_mg_2_4), 2)},
            "1X + Over 1.5": {"prob": round(prob_1x_over_1_5, 3), "fair_odds": round(1.0 / max(0.01, prob_1x_over_1_5), 2)},
            "1X + MultiGol 1-4": {"prob": round(prob_1x_mg_1_4, 3), "fair_odds": round(1.0 / max(0.01, prob_1x_mg_1_4), 2)},
            "1X (Doppia Chance)": {"prob": round(prob_1x, 3), "fair_odds": round(1.0 / max(0.01, prob_1x), 2)},
            "Over 2.5": {"prob": round(prob_over_2_5, 3), "fair_odds": round(1.0 / max(0.01, prob_over_2_5), 2)},
        }

        gems = []
        for m_name, data in markets.items():
            netwin_q = book_odds.get(m_name)
            if netwin_q:
                edge = (data["prob"] * netwin_q - 1.0) * 100.0
                data["netwin_odds"] = netwin_q
                data["edge_pct"] = round(edge, 1)
                if edge >= 8.0 and netwin_q >= 1.60:
                    gems.append({
                        "market": m_name,
                        "netwin_odds": netwin_q,
                        "fair_odds": data["fair_odds"],
                        "prob": data["prob"],
                        "edge_pct": round(edge, 1)
                    })

        return {
            "match": f"{home_team} vs {away_team}",
            "xg_home": xg_home,
            "xg_away": xg_away,
            "markets": markets,
            "true_gems": gems
        }

    def goal_market_probability(
        self,
        xg_home: float,
        xg_away: float,
        market_name: str,
    ) -> Optional[float]:
        """Probabilità di un mercato gol dalla matrice Dixon-Coles. None se il nome non è mappato."""
        return self.joint_goal_probability(xg_home, xg_away, [market_name])

    def joint_goal_probability(
        self,
        xg_home: float,
        xg_away: float,
        market_names: List[str],
    ) -> Optional[float]:
        """Intersezione di più mercati gol sulla stessa matrice. None se un nome non è mappato."""
        if not market_names:
            return None
        matrix, home, away, total = self._score_axes(xg_home, xg_away)
        combined: Optional[np.ndarray] = None
        for market_name in market_names:
            mask = _goal_market_mask(market_name, home, away, total)
            if mask is None:
                return None
            combined = mask if combined is None else (combined & mask)
        return float(np.sum(matrix[combined]))

    def _score_axes(self, xg_home: float, xg_away: float):
        matrix = self.generate_score_matrix(xg_home, xg_away)
        goals = np.arange(matrix.shape[0])
        home = goals[:, None]
        away = goals[None, :]
        return matrix, home, away, home + away

    def corner_market_probability(
        self,
        avg_corners_home: float,
        avg_corners_away: float,
        market_name: str,
    ) -> Optional[float]:
        """Probabilità di una linea Over corner totali. None se la linea non è 8.5, 9.5 o 10.5."""
        name = market_name.strip().lower()
        if "corner" not in name:
            return None
        priced = self.analyze_corners(
            "home",
            "away",
            avg_corners_home,
            avg_corners_away,
        )["corner_markets"]
        for label, data in priced.items():
            line = label.lower().split("over ", 1)[-1].split(" ")[0]
            if re.search(rf"(?<!\d){re.escape(line)}(?!\d)", name):
                return float(data["prob"])
        return None

    def corner_over_probability(
        self,
        avg_corners_home: float,
        avg_corners_away: float,
        market_name: str,
    ) -> Optional[float]:
        """Over corner su totale, casa o ospite, dalla stessa binomiale negativa della matrice congiunta.

        None se il nome non è un Over corner. La linea è libera: 4.5 di squadra e 8.5/9.5 totali
        usano la stessa massa, senza una formula derivata dal totale.
        """
        name = market_name.strip().lower()
        if "corner" not in name or "over" not in name:
            return None
        parsed = re.search(r"over\s*(\d+(?:\.\d+)?)", name)
        if parsed is None:
            return None
        line = float(parsed.group(1))
        matrix, home, away, total = self._corner_axes(avg_corners_home, avg_corners_away)
        if re.search(r"\b(?:casa|home)\b", name):
            band = home > line
        elif re.search(r"\b(?:ospite|away)\b", name):
            band = away > line
        else:
            band = total > line
        mask = np.broadcast_to(band, matrix.shape)
        return float(np.sum(matrix[mask]))

    def _corner_axes(
        self,
        avg_corners_home: float,
        avg_corners_away: float,
        dispersion_factor: float = 1.5,
        max_corners: int = 20,
    ):
        """Matrice congiunta dei corner. Stessa parametrizzazione di analyze_corners."""
        alpha = 0.1 * dispersion_factor

        def _params(mu: float) -> tuple[float, float]:
            n = 1.0 / alpha
            p = 1.0 / (1.0 + alpha * mu)
            return n, p

        n_home, p_home = _params(avg_corners_home)
        n_away, p_away = _params(avg_corners_away)
        corners = np.arange(max_corners)
        matrix = np.outer(nbinom.pmf(corners, n_home, p_home), nbinom.pmf(corners, n_away, p_away))
        home = corners[:, None]
        away = corners[None, :]
        return matrix, home, away, home + away

    # Alias per compatibilità con il codice esistente
    analyze_niche_markets = analyze_football_markets

    def analyze_corners(
        self,
        home_team: str,
        away_team: str,
        avg_corners_home: float,
        avg_corners_away: float,
        dispersion_factor: float = 1.5, # >1 indica overdispersion tipica dei corner
        bookmaker_odds: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Modella i corner usando la Distribuzione Binomiale Negativa per gestire l'overdispersion.
        """
        # Parametrizzazione Binomiale Negativa da Media (mu) e Fattore di Dispersione (alpha)
        # Varianza = mu + alpha * mu^2. n = 1 / alpha, p = 1 / (1 + alpha * mu).
        corner_matrix, _home, _away, total_corners_grid = self._corner_axes(
            avg_corners_home,
            avg_corners_away,
            dispersion_factor,
        )

        prob_over_8_5 = np.sum(corner_matrix[total_corners_grid > 8.5])
        prob_over_9_5 = np.sum(corner_matrix[total_corners_grid > 9.5])
        prob_over_10_5 = np.sum(corner_matrix[total_corners_grid > 10.5])

        markets = {
            "Over 8.5 Corner Totali": {"prob": round(prob_over_8_5, 3), "fair_odds": round(1.0 / max(0.01, prob_over_8_5), 2)},
            "Over 9.5 Corner Totali": {"prob": round(prob_over_9_5, 3), "fair_odds": round(1.0 / max(0.01, prob_over_9_5), 2)},
            "Over 10.5 Corner Totali": {"prob": round(prob_over_10_5, 3), "fair_odds": round(1.0 / max(0.01, prob_over_10_5), 2)},
        }

        # Logica Edge per Corner (identica a quella calcistica)
        gems = []
        for m_name, data in markets.items():
            netwin_q = bookmaker_odds.get(m_name) if bookmaker_odds else None
            if netwin_q:
                edge = (data["prob"] * netwin_q - 1.0) * 100.0
                data["netwin_odds"] = netwin_q
                data["edge_pct"] = round(edge, 1)
                if edge >= 8.0 and netwin_q >= 1.50: # Soglia leggermente più bassa per i corner
                    gems.append({
                        "market": m_name,
                        "netwin_odds": netwin_q,
                        "fair_odds": data["fair_odds"],
                        "prob": data["prob"],
                        "edge_pct": round(edge, 1)
                    })

        return {
            "match": f"{home_team} vs {away_team}",
            "avg_corners_home": avg_corners_home,
            "avg_corners_away": avg_corners_away,
            "corner_markets": markets,
            "corner_gems": gems
        }

# Alias per retrocompatibilità
XgPoissonEngine = QuantitativeEngine

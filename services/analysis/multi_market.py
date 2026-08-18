"""
MultiMarketAnalyzer — BAgent
Analizza edge su tutti i mercati disponibili per una partita.

Mercati supportati:
  - 1X2 (Casa, Pareggio, Ospite)
  - Doppia Chance (1X, 12, X2)
  - Over/Under (0.5, 1.5, 2.5, 3.5, 4.5)
  - GG / NG

Flusso:
  1. Inserisci le tue probabilità 1X2 (già aggiustate con Sesto Senso)
  2. Inserisci xG stimato per casa e ospite (usato per O/U e GG/NG)
  3. Inserisci le quote del bookmaker
  4. Ottieni tutti i mercati ordinati per probabilità, con edge come info
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import math


# ---------------------------------------------------------------------------
# Modello Poisson per gol
# ---------------------------------------------------------------------------

def _poisson_pmf(k: int, lam: float) -> float:
    """P(X = k) con X ~ Poisson(lam)"""
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def _build_joint(xg_home: float, xg_away: float, max_goals: int = 8):
    """
    Matrice joint[i][j] = P(home segna i gol, away segna j gol)
    Assumendo indipendenza tra le due distribuzioni Poisson.
    """
    home_pmf = [_poisson_pmf(k, xg_home) for k in range(max_goals + 1)]
    away_pmf = [_poisson_pmf(k, xg_away) for k in range(max_goals + 1)]
    joint = [[home_pmf[i] * away_pmf[j]
              for j in range(max_goals + 1)]
             for i in range(max_goals + 1)]
    return joint, max_goals


def _prob_over(joint, max_goals: int, line: float) -> float:
    """P(totale gol > line)"""
    total = 0.0
    for i in range(max_goals + 1):
        for j in range(max_goals + 1):
            if i + j > line:
                total += joint[i][j]
    return total


def _prob_gg(xg_home: float, xg_away: float) -> float:
    """P(entrambe segnano almeno 1) = P(home≥1) * P(away≥1)"""
    p_home_scores = 1 - _poisson_pmf(0, xg_home)
    p_away_scores = 1 - _poisson_pmf(0, xg_away)
    return p_home_scores * p_away_scores


# ---------------------------------------------------------------------------
# Dataclass risultato
# ---------------------------------------------------------------------------

@dataclass
class MarketResult:
    market: str          # es. "Over/Under", "1X2", "GG/NG"
    selection: str       # es. "Over 2.5", "Casa 1", "NG"
    prob: float          # mia probabilità stimata
    quota: float         # quota bookmaker
    edge: float          # (prob * quota) - 1

    @property
    def edge_pct(self) -> str:
        sign = "+" if self.edge >= 0 else ""
        return f"{sign}{self.edge * 100:.1f}%"

    @property
    def prob_pct(self) -> str:
        return f"{self.prob * 100:.0f}%"


# ---------------------------------------------------------------------------
# Quote bookmaker (input utente)
# ---------------------------------------------------------------------------

@dataclass
class BookmakerOdds:
    # 1X2
    home_1: Optional[float] = None
    draw_x: Optional[float] = None
    away_2: Optional[float] = None
    # Doppia Chance
    dc_1x: Optional[float] = None
    dc_12: Optional[float] = None
    dc_x2: Optional[float] = None
    # Over/Under gol
    over_05: Optional[float] = None
    under_05: Optional[float] = None
    over_15: Optional[float] = None
    under_15: Optional[float] = None
    over_25: Optional[float] = None
    under_25: Optional[float] = None
    over_35: Optional[float] = None
    under_35: Optional[float] = None
    over_45: Optional[float] = None
    under_45: Optional[float] = None
    # GG / NG
    gg: Optional[float] = None
    ng: Optional[float] = None
    # Corner Over/Under
    corner_over_75: Optional[float] = None
    corner_under_75: Optional[float] = None
    corner_over_85: Optional[float] = None
    corner_under_85: Optional[float] = None
    corner_over_95: Optional[float] = None
    corner_under_95: Optional[float] = None
    corner_over_105: Optional[float] = None
    corner_under_105: Optional[float] = None
    corner_over_115: Optional[float] = None
    corner_under_115: Optional[float] = None
    corner_over_125: Optional[float] = None
    corner_under_125: Optional[float] = None
    # Cartellini Over/Under
    card_over_15: Optional[float] = None
    card_under_15: Optional[float] = None
    card_over_25: Optional[float] = None
    card_under_25: Optional[float] = None
    card_over_35: Optional[float] = None
    card_under_35: Optional[float] = None
    card_over_45: Optional[float] = None
    card_under_45: Optional[float] = None
    card_over_55: Optional[float] = None
    card_under_55: Optional[float] = None


# ---------------------------------------------------------------------------
# Analizzatore principale
# ---------------------------------------------------------------------------

class MultiMarketAnalyzer:
    """
    Analizza tutti i mercati disponibili per una partita
    e restituisce i risultati ordinati per probabilità (decrescente).

    Parametri obbligatori:
        prob_home   — mia probabilità vittoria casa (0-1)
        prob_draw   — mia probabilità pareggio (0-1)
        prob_away   — mia probabilità vittoria ospite (0-1)
        xg_home     — gol attesi squadra casa
        xg_away     — gol attesi squadra ospite
        odds        — BookmakerOdds con le quote disponibili

    Parametri facoltativi:
        xc_home     — corner attesi squadra casa (default None → mercato corner saltato)
        xc_away     — corner attesi squadra ospite
        xk_home     — cartellini attesi squadra casa (default None → mercato cartellini saltato)
        xk_away     — cartellini attesi squadra ospite
        min_quota   — quota minima per includere un mercato (default 1.20)
        match_label — stringa descrittiva per output (es. "Monza vs Avellino")
    """

    MIN_QUOTA = 1.20

    def __init__(
        self,
        prob_home: float,
        prob_draw: float,
        prob_away: float,
        xg_home: float,
        xg_away: float,
        odds: BookmakerOdds,
        xc_home: Optional[float] = None,
        xc_away: Optional[float] = None,
        xk_home: Optional[float] = None,
        xk_away: Optional[float] = None,
        min_quota: float = 1.20,
        match_label: str = "",
    ):
        # Normalizza le prob 1X2 (potrebbero non sommare esattamente a 1)
        total = prob_home + prob_draw + prob_away
        self.p1 = prob_home / total
        self.pX = prob_draw / total
        self.p2 = prob_away / total

        self.xg_home = xg_home
        self.xg_away = xg_away
        self.xc_home = xc_home
        self.xc_away = xc_away
        self.xk_home = xk_home
        self.xk_away = xk_away
        self.odds = odds
        self.min_quota = min_quota
        self.match_label = match_label

        # Precalcola distribuzioni Poisson per gol
        self._joint, self._max_goals = _build_joint(xg_home, xg_away)

        # Precalcola per corner (se disponibili)
        if xc_home is not None and xc_away is not None:
            xc_total = xc_home + xc_away
            self._corner_joint, self._corner_max = _build_joint(xc_home, xc_away, max_goals=25)
        else:
            self._corner_joint = None

        # Precalcola per cartellini (se disponibili)
        if xk_home is not None and xk_away is not None:
            self._card_joint, self._card_max = _build_joint(xk_home, xk_away, max_goals=15)
        else:
            self._card_joint = None

        # Calcola tutte le probabilità
        self._probs = self._compute_probs()

    def _compute_probs(self) -> dict:
        p = {}

        # 1X2
        p["home_1"] = self.p1
        p["draw_x"] = self.pX
        p["away_2"] = self.p2

        # Doppia Chance (derivata da 1X2)
        p["dc_1x"] = self.p1 + self.pX
        p["dc_12"] = self.p1 + self.p2
        p["dc_x2"] = self.pX + self.p2

        # Over/Under gol (Poisson)
        for line in [0.5, 1.5, 2.5, 3.5, 4.5]:
            key_over = f"over_{str(line).replace('.', '')}"
            key_under = f"under_{str(line).replace('.', '')}"
            po = _prob_over(self._joint, self._max_goals, line)
            p[key_over] = min(po, 1.0)
            p[key_under] = max(1.0 - po, 0.0)

        # GG / NG
        pgg = _prob_gg(self.xg_home, self.xg_away)
        p["gg"] = min(pgg, 1.0)
        p["ng"] = max(1.0 - pgg, 0.0)

        # Corner Over/Under (Poisson su totale corner)
        if self._corner_joint is not None:
            for line in [7.5, 8.5, 9.5, 10.5, 11.5, 12.5]:
                key = str(line).replace('.', '')
                po = _prob_over(self._corner_joint, self._corner_max, line)
                p[f"corner_over_{key}"] = min(po, 1.0)
                p[f"corner_under_{key}"] = max(1.0 - po, 0.0)

        # Cartellini Over/Under (Poisson su totale cartellini)
        if self._card_joint is not None:
            for line in [1.5, 2.5, 3.5, 4.5, 5.5]:
                key = str(line).replace('.', '')
                po = _prob_over(self._card_joint, self._card_max, line)
                p[f"card_over_{key}"] = min(po, 1.0)
                p[f"card_under_{key}"] = max(1.0 - po, 0.0)

        return p

    def _make_result(self, market: str, selection: str, prob_key: str, quota: Optional[float]) -> Optional[MarketResult]:
        if quota is None or quota < self.min_quota:
            return None
        prob = self._probs.get(prob_key, 0.0)
        if prob <= 0:
            return None
        edge = prob * quota - 1
        return MarketResult(
            market=market,
            selection=selection,
            prob=prob,
            quota=quota,
            edge=edge,
        )

    def analyze(self) -> list[MarketResult]:
        """
        Restituisce tutti i mercati analizzati, ordinati per probabilità decrescente.
        Include anche mercati con edge negativo (info completa).
        """
        o = self.odds
        candidates = [
            ("1X2",       "Casa 1",    "home_1",   o.home_1),
            ("1X2",       "Pareggio X","draw_x",   o.draw_x),
            ("1X2",       "Ospite 2",  "away_2",   o.away_2),
            ("DC",        "1X",        "dc_1x",    o.dc_1x),
            ("DC",        "12",        "dc_12",    o.dc_12),
            ("DC",        "X2",        "dc_x2",    o.dc_x2),
            ("Over/Under","Over 0.5",  "over_05",  o.over_05),
            ("Over/Under","Under 0.5", "under_05", o.under_05),
            ("Over/Under","Over 1.5",  "over_15",  o.over_15),
            ("Over/Under","Under 1.5", "under_15", o.under_15),
            ("Over/Under","Over 2.5",  "over_25",  o.over_25),
            ("Over/Under","Under 2.5", "under_25", o.under_25),
            ("Over/Under","Over 3.5",  "over_35",  o.over_35),
            ("Over/Under","Under 3.5", "under_35", o.under_35),
            ("Over/Under","Over 4.5",  "over_45",  o.over_45),
            ("Over/Under","Under 4.5", "under_45", o.under_45),
            ("GG/NG",     "GG",        "gg",       o.gg),
            ("GG/NG",     "NG",        "ng",       o.ng),
            # Corner
            ("Corner",    "Over 7.5",  "corner_over_75",  o.corner_over_75),
            ("Corner",    "Under 7.5", "corner_under_75", o.corner_under_75),
            ("Corner",    "Over 8.5",  "corner_over_85",  o.corner_over_85),
            ("Corner",    "Under 8.5", "corner_under_85", o.corner_under_85),
            ("Corner",    "Over 9.5",  "corner_over_95",  o.corner_over_95),
            ("Corner",    "Under 9.5", "corner_under_95", o.corner_under_95),
            ("Corner",    "Over 10.5", "corner_over_105", o.corner_over_105),
            ("Corner",    "Under 10.5","corner_under_105",o.corner_under_105),
            ("Corner",    "Over 11.5", "corner_over_115", o.corner_over_115),
            ("Corner",    "Under 11.5","corner_under_115",o.corner_under_115),
            ("Corner",    "Over 12.5", "corner_over_125", o.corner_over_125),
            ("Corner",    "Under 12.5","corner_under_125",o.corner_under_125),
            # Cartellini
            ("Cartellini","Over 1.5",  "card_over_15",  o.card_over_15),
            ("Cartellini","Under 1.5", "card_under_15", o.card_under_15),
            ("Cartellini","Over 2.5",  "card_over_25",  o.card_over_25),
            ("Cartellini","Under 2.5", "card_under_25", o.card_under_25),
            ("Cartellini","Over 3.5",  "card_over_35",  o.card_over_35),
            ("Cartellini","Under 3.5", "card_under_35", o.card_under_35),
            ("Cartellini","Over 4.5",  "card_over_45",  o.card_over_45),
            ("Cartellini","Under 4.5", "card_under_45", o.card_under_45),
            ("Cartellini","Over 5.5",  "card_over_55",  o.card_over_55),
            ("Cartellini","Under 5.5", "card_under_55", o.card_under_55),
        ]

        results = []
        for market, selection, prob_key, quota in candidates:
            r = self._make_result(market, selection, prob_key, quota)
            if r:
                results.append(r)

        # Ordina per probabilità decrescente
        results.sort(key=lambda x: x.prob, reverse=True)
        return results

    def print_table(self, show_all: bool = True):
        """
        Stampa la tabella formattata.
        show_all=True → mostra tutti i mercati
        show_all=False → mostra solo quelli con edge > 0
        """
        results = self.analyze()
        if not show_all:
            results = [r for r in results if r.edge > 0]

        header = f"\n{'='*60}"
        if self.match_label:
            header += f"\n  {self.match_label}"
        header += f"\n  xG: {self.xg_home:.2f} (casa) — {self.xg_away:.2f} (ospite)"
        if self.xc_home is not None:
            header += f"\n  xC: {self.xc_home:.1f} (casa) — {self.xc_away:.1f} (ospite) = {self.xc_home+self.xc_away:.1f} tot"
        if self.xk_home is not None:
            header += f"\n  xK: {self.xk_home:.1f} (casa) — {self.xk_away:.1f} (ospite) = {self.xk_home+self.xk_away:.1f} tot"
        header += f"\n{'='*60}"
        print(header)

        print(f"{'Mercato':<14} {'Selezione':<13} {'Prob':>6} {'Quota':>7} {'Edge':>9}")
        print(f"{'-'*55}")

        for r in results:
            edge_str = r.edge_pct
            flag = "✅" if r.edge >= 0.05 else ("👀" if r.edge > 0 else "❌")
            print(f"{r.market:<14} {r.selection:<13} {r.prob_pct:>6} {r.quota:>7.2f} {edge_str:>9}  {flag}")

        print(f"{'='*60}\n")


# ---------------------------------------------------------------------------
# Helper: stima xG da statistiche stagionali (quando non disponibile manualmente)
# ---------------------------------------------------------------------------

def estimate_xg(
    home_avg_scored: float,
    home_avg_conceded: float,
    away_avg_scored: float,
    away_avg_conceded: float,
    home_advantage: float = 1.15,
) -> tuple[float, float]:
    """
    Stima xG usando il metodo Dixon-Coles semplificato.

    xg_home = home_attack × away_defense × home_advantage
    xg_away = away_attack × home_defense

    dove attack/defense sono normalizzati sulla media di lega.

    Se non hai le medie di lega, passa direttamente le medie di squadra.
    Ritorna (xg_home, xg_away).
    """
    # Media lega approssimata (2.5 gol a partita = 1.25 per squadra)
    league_avg = 1.25

    home_attack  = home_avg_scored   / league_avg
    home_defense = home_avg_conceded / league_avg
    away_attack  = away_avg_scored   / league_avg
    away_defense = away_avg_conceded / league_avg

    xg_home = home_attack * away_defense * league_avg * home_advantage
    xg_away = away_attack * home_defense * league_avg

    # Cap ragionevole
    xg_home = min(max(xg_home, 0.3), 4.5)
    xg_away = min(max(xg_away, 0.2), 4.0)

    return round(xg_home, 2), round(xg_away, 2)

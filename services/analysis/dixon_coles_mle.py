"""Dixon-Coles (1997) via massima verosimiglianza non vincolata.

    log λ = γ + α_casa + β_ospite
    log μ = α_ospite + β_casa

La somma degli attacchi è zero: l'ultima squadra, in ordine alfabetico, ha la
riga di design tutta a -1 e α_n = −∑ α_i. L-BFGS-B non ha vincoli di Lagrange.
Il peso di una partita è exp(−ξ Δt), con ξ = 0.0019 al giorno (Dixon-Coles:
0.0065 a mezza settimana). Dopo il fit gli attacchi moltiplicativi hanno media
aritmetica 1; lo shrinkage N/(N+M) li tira verso 1 insieme alle difese.
"""

from __future__ import annotations

import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

XI_PER_DAY = 0.0019
SHRINKAGE_M = 3.0
RHO_BOUNDS = (-0.25, 0.25)


@dataclass(frozen=True)
class DixonColesResult:
    attack_params: dict[str, float]
    defense_params: dict[str, float]
    home_advantage: float
    rho: float
    sample_sizes: dict[str, int]
    fit_time_seconds: float


class DixonColesMLE:
    """Stima α, β, γ e ρ da un DataFrame o da bagent.db. Nessuna chiamata di rete."""

    def __init__(self, xi: float = XI_PER_DAY, shrinkage_m: float = SHRINKAGE_M):
        self.xi = float(xi)
        self.shrinkage_m = float(shrinkage_m)
        self.result: DixonColesResult | None = None
        self._attack: dict[str, float] = {}
        self._defense: dict[str, float] = {}
        self._home = 1.0
        self._alpha_hat = np.array([])
        self._beta_hat = np.array([])
        self._gamma = 0.0
        self._index: dict[str, int] = {}

    def fit(
        self,
        matches: pd.DataFrame,
        reference_date: datetime | None = None,
    ) -> DixonColesResult:
        """DataFrame con home_team, away_team, home_goals, away_goals e, se ξ ≠ 0, date."""
        started = time.perf_counter()
        frame = _require_matches(matches)
        home = frame["home_team"].to_numpy(dtype=object)
        away = frame["away_team"].to_numpy(dtype=object)
        home_goals = _as_goals(frame["home_goals"].to_numpy())
        away_goals = _as_goals(frame["away_goals"].to_numpy())
        teams = tuple(sorted(set(home.tolist()) | set(away.tolist())))
        if len(teams) < 2:
            raise ValueError("Servono almeno due squadre")
        index = {name: pos for pos, name in enumerate(teams)}
        home_index = np.fromiter((index[name] for name in home), dtype=int, count=len(home))
        away_index = np.fromiter((index[name] for name in away), dtype=int, count=len(away))
        weights = _decay_weights(frame["date"] if "date" in frame.columns else None, self.xi, reference_date, len(frame))
        counts = {
            name: int(np.sum(home_index == pos) + np.sum(away_index == pos))
            for name, pos in index.items()
        }
        x_lam, x_mu = _design_matrix(home_index, away_index, len(teams))
        theta0 = np.zeros(x_lam.shape[1] + 1)
        theta0[-2] = np.log(max(float(home_goals.mean()), 1e-3) / max(float(away_goals.mean()), 1e-3))
        theta0[-1] = -0.05
        bounds = [(-4.0, 4.0)] * x_lam.shape[1] + [RHO_BOUNDS]
        solved = minimize(
            _objective(x_lam, x_mu, home_goals, away_goals, weights),
            theta0,
            method="L-BFGS-B",
            jac=True,
            bounds=bounds,
            options={"maxiter": 250, "ftol": 1e-12},
        )
        alpha_hat, beta_hat, gamma = _unpack_linear(solved.x[:-1], len(teams))
        attack, defense, home_advantage = _multiplicative(teams, alpha_hat, beta_hat, gamma)
        attack = _shrink_toward_one(attack, counts, self.shrinkage_m)
        defense = _shrink_toward_one(defense, counts, self.shrinkage_m)
        result = DixonColesResult(
            attack_params=attack,
            defense_params=defense,
            home_advantage=home_advantage,
            rho=float(solved.x[-1]),
            sample_sizes=counts,
            fit_time_seconds=time.perf_counter() - started,
        )
        self.result = result
        self._attack = attack
        self._defense = defense
        self._home = home_advantage
        self._alpha_hat = alpha_hat
        self._beta_hat = beta_hat
        self._gamma = gamma
        self._index = index
        return result

    def predict_lambdas(self, home_team: str, away_team: str) -> tuple[float, float]:
        """λ casa e μ trasferta dopo lo shrinkage: γ · α_i · β_j e α_j · β_i."""
        self._ready()
        lam = self._home * self._attack[home_team] * self._defense[away_team]
        mu = self._attack[away_team] * self._defense[home_team]
        return float(lam), float(mu)

    def generate_score_matrix(
        self,
        home_team: str,
        away_team: str,
        max_goals: int = 7,
    ) -> np.ndarray:
        """Probabilità dei punteggi da 0 a max_goals, con il τ del ρ stimato, rinormalizzata."""
        if max_goals < 1:
            raise ValueError("max_goals deve essere almeno 1")
        lam, mu = self.predict_lambdas(home_team, away_team)
        rho = _clip_rho(lam, mu, self.result.rho)
        goals = np.arange(max_goals + 1)
        grid = np.outer(poisson.pmf(goals, lam), poisson.pmf(goals, mu))
        tau = np.ones_like(grid)
        tau[0, 0] = 1.0 - lam * mu * rho
        tau[0, 1] = 1.0 + lam * rho
        tau[1, 0] = 1.0 + mu * rho
        tau[1, 1] = 1.0 - rho
        grid = np.clip(grid * tau, 0.0, None)
        total = float(grid.sum())
        if total <= 0.0:
            raise ValueError("La matrice dei punteggi è nulla")
        return grid / total

    def fit_from_db(
        self,
        db_path: Path,
        competition_name: str,
        season: str | None = None,
    ) -> DixonColesResult:
        """Legge le partite status = 'FT' da matches. season None prende tutte le stagioni."""
        path = Path(db_path)
        if not path.exists():
            raise FileNotFoundError(path)
        query = """
            SELECT date_gmt AS date, home_team, away_team, home_goals, away_goals
            FROM matches
            WHERE status = 'FT'
              AND league = ?
              AND home_goals IS NOT NULL
              AND away_goals IS NOT NULL
        """
        params: list[str] = [competition_name]
        if season is not None:
            query += " AND season = ?"
            params.append(str(season))
        with sqlite3.connect(path) as conn:
            frame = pd.read_sql_query(query, conn, params=params)
        if frame.empty:
            raise ValueError(f"Nessuna partita FT per {competition_name} {season or ''}".strip())
        return self.fit(frame)

    def _ready(self) -> None:
        if self.result is None:
            raise RuntimeError("Chiama fit prima di predire")

    def _rates_from_design(self, home_team: str, away_team: str) -> tuple[float, float]:
        """λ e μ del MLE grezzo, dalla riga ridotta. Serve a verificare la somma zero."""
        n = len(self._index)
        beta = _pack_linear(self._alpha_hat, self._beta_hat, self._gamma)
        row_lam, row_mu = _design_rows(self._index[home_team], self._index[away_team], n)
        return float(np.exp(row_lam @ beta)), float(np.exp(row_mu @ beta))


def _require_matches(matches: pd.DataFrame) -> pd.DataFrame:
    required = {"home_team", "away_team", "home_goals", "away_goals"}
    missing = required - set(matches.columns)
    if missing:
        raise ValueError(f"Colonne mancanti: {sorted(missing)}")
    if matches.empty:
        raise ValueError("Il DataFrame non ha partite")
    return matches


def _decay_weights(dates, xi: float, reference: datetime | None, n_rows: int) -> np.ndarray:
    if xi == 0.0:
        return np.ones(n_rows, dtype=float)
    if dates is None:
        raise ValueError("Con ξ diverso da zero serve la colonna date")
    stamps = pd.to_datetime(dates).to_numpy(dtype="datetime64[D]")
    if reference is None:
        ref = np.nanmax(stamps)
    else:
        ref = np.datetime64(pd.Timestamp(reference).normalize(), "D")
    delta = (ref - stamps) / np.timedelta64(1, "D")
    delta = np.clip(np.nan_to_num(delta.astype(float), nan=0.0), 0.0, None)
    return np.exp(-xi * delta)


def _as_goals(values) -> np.ndarray:
    goals = np.asarray(values, dtype=float)
    if np.any(goals < 0) or np.any(~np.isfinite(goals)):
        raise ValueError("I gol devono essere numeri finiti e non negativi")
    if np.any(np.abs(goals - np.rint(goals)) > 1e-6):
        raise ValueError("I gol devono essere interi")
    return np.rint(goals).astype(int)


def _design_rows(home_index: int, away_index: int, n_teams: int) -> tuple[np.ndarray, np.ndarray]:
    width = 2 * n_teams
    lam = np.zeros(width)
    mu = np.zeros(width)
    attack = slice(0, n_teams - 1)
    if home_index == n_teams - 1:
        lam[attack] = -1.0
    else:
        lam[home_index] = 1.0
    lam[(n_teams - 1) + away_index] = 1.0
    lam[-1] = 1.0
    if away_index == n_teams - 1:
        mu[attack] = -1.0
    else:
        mu[away_index] = 1.0
    mu[(n_teams - 1) + home_index] = 1.0
    return lam, mu


def _design_matrix(home_index: np.ndarray, away_index: np.ndarray, n_teams: int) -> tuple[np.ndarray, np.ndarray]:
    rows_lam = []
    rows_mu = []
    for home, away in zip(home_index, away_index):
        lam, mu = _design_rows(int(home), int(away), n_teams)
        rows_lam.append(lam)
        rows_mu.append(mu)
    return np.vstack(rows_lam), np.vstack(rows_mu)


def _pack_linear(alpha: np.ndarray, beta: np.ndarray, gamma: float) -> np.ndarray:
    return np.concatenate([alpha[:-1], beta, np.array([gamma])])


def _unpack_linear(beta_free: np.ndarray, n_teams: int) -> tuple[np.ndarray, np.ndarray, float]:
    alpha = np.zeros(n_teams)
    alpha[:-1] = beta_free[: n_teams - 1]
    alpha[-1] = -np.sum(alpha[:-1])
    defense = beta_free[n_teams - 1 : 2 * n_teams - 1].copy()
    return alpha, defense, float(beta_free[-1])


def _multiplicative(teams, alpha, beta, gamma) -> tuple[dict[str, float], dict[str, float], float]:
    """Media aritmetica degli attacchi = 1. La scala tolta agli α entra nelle difese."""
    raw_attack = np.exp(alpha)
    attack_mean = float(raw_attack.mean())
    attack = {
        name: float(raw_attack[pos] / attack_mean)
        for pos, name in enumerate(teams)
    }
    defense = {
        name: float(np.exp(beta[pos]) * attack_mean)
        for pos, name in enumerate(teams)
    }
    return attack, defense, float(np.exp(gamma))


def _shrink_toward_one(params: dict[str, float], counts: dict[str, int], shrinkage_m: float) -> dict[str, float]:
    if shrinkage_m <= 0.0:
        return dict(params)
    shrunk = {}
    for name, estimate in params.items():
        played = counts[name]
        weight = played / (played + shrinkage_m)
        shrunk[name] = weight * estimate + (1.0 - weight) * 1.0
    return shrunk


def _clip_rho(lam: float, mu: float, rho: float) -> float:
    """max(−1/λ, −1/μ) ≤ ρ ≤ min(1/(λμ), 1), il vincolo del paper."""
    low = max(-1.0 / lam, -1.0 / mu)
    high = min(1.0 / (lam * mu), 1.0)
    if low > high:
        return 0.0
    return float(np.clip(rho, low, high))


def _objective(x_lam, x_mu, home_goals, away_goals, weights):
    """NLL e gradiente. τ corregge solo 0-0, 0-1, 1-0 e 1-1."""

    def value_and_grad(theta):
        beta = theta[:-1]
        rho = theta[-1]
        log_lam = x_lam @ beta
        log_mu = x_mu @ beta
        lam = np.exp(log_lam)
        mu = np.exp(log_mu)
        tau = np.ones(home_goals.shape[0])
        dtau_dlam = np.zeros_like(tau)
        dtau_dmu = np.zeros_like(tau)
        dtau_drho = np.zeros_like(tau)
        zero_zero = (home_goals == 0) & (away_goals == 0)
        zero_one = (home_goals == 0) & (away_goals == 1)
        one_zero = (home_goals == 1) & (away_goals == 0)
        one_one = (home_goals == 1) & (away_goals == 1)
        tau[zero_zero] = 1.0 - lam[zero_zero] * mu[zero_zero] * rho
        tau[zero_one] = 1.0 + lam[zero_one] * rho
        tau[one_zero] = 1.0 + mu[one_zero] * rho
        tau[one_one] = 1.0 - rho
        dtau_dlam[zero_zero] = -mu[zero_zero] * rho
        dtau_dlam[zero_one] = rho
        dtau_dmu[zero_zero] = -lam[zero_zero] * rho
        dtau_dmu[one_zero] = rho
        dtau_drho[zero_zero] = -lam[zero_zero] * mu[zero_zero]
        dtau_drho[zero_one] = lam[zero_one]
        dtau_drho[one_zero] = mu[one_zero]
        dtau_drho[one_one] = -1.0
        invalid = tau <= 1e-12
        tau_safe = np.maximum(tau, 1e-12)
        log_lik = np.log(tau_safe) + home_goals * log_lam - lam + away_goals * log_mu - mu
        nll = float(-np.sum(weights * log_lik) + 1e6 * np.sum(invalid))
        g_lam = (home_goals - lam) + lam * dtau_dlam / tau_safe
        g_mu = (away_goals - mu) + mu * dtau_dmu / tau_safe
        grad_beta = -(x_lam.T @ (weights * g_lam) + x_mu.T @ (weights * g_mu))
        grad_rho = -np.sum(weights * dtau_drho / tau_safe)
        return nll, np.concatenate([grad_beta, np.array([grad_rho])])

    return value_and_grad

"""Dixon-Coles (1997) via massima verosimiglianza non vincolata.

Il log-lineare è

    log λ = γ + α_casa + β_ospite
    log μ = α_ospite + β_casa

La somma degli attacchi è zero, quindi α dell'ultima squadra vale meno la
somma delle altre e la sua riga nella matrice di design è tutta -1.
L'ottimizzazione non ha vincoli di Lagrange: L-BFGS-B, ρ fra -0.25 e 0.25.

Dopo la convergenza gli attacchi exp(α) hanno media geometrica 1. Le difese
vengono centrate allo stesso modo e il livello medio entra in `away_base`.
Una squadra con meno di `shrink_threshold` partite (default 5, Regola #80)
viene tirata verso quella baseline in proporzione alle gare giocate.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

RHO_BOUNDS = (-0.25, 0.25)
_SHRINK_DEFAULT = 5.0


@dataclass
class DixonColesFit:
    """Parametri sulla scala moltiplicativa. attack e defense hanno media geometrica 1 al MLE."""

    teams: tuple[str, ...]
    attack: dict[str, float]
    defense: dict[str, float]
    home_advantage: float
    away_base: float
    rho: float
    n_matches: dict[str, int]
    nll: float
    success: bool
    _alpha: np.ndarray
    _beta: np.ndarray
    _gamma: float
    _alpha_hat: np.ndarray
    _beta_hat: np.ndarray
    _index: dict[str, int]

    def expected_goals(self, home: str, away: str) -> tuple[float, float]:
        """λ e μ dopo lo shrinkage, dalla formula esplicita."""
        hi = self._index[home]
        ai = self._index[away]
        lam = np.exp(self._gamma + self._alpha[hi] + self._beta[ai])
        mu = np.exp(self._alpha[ai] + self._beta[hi])
        return float(lam), float(mu)

    def rates_from_explicit(self, home: str, away: str) -> tuple[float, float]:
        """λ e μ del MLE, prima dello shrinkage, con α_n = −∑ α_i."""
        hi = self._index[home]
        ai = self._index[away]
        lam = np.exp(self._gamma + self._alpha_hat[hi] + self._beta_hat[ai])
        mu = np.exp(self._alpha_hat[ai] + self._beta_hat[hi])
        return float(lam), float(mu)

    def rates_from_design(self, home: str, away: str) -> tuple[float, float]:
        """Stessi λ e μ del MLE, letti dalla riga della matrice di design ridotta."""
        n = len(self.teams)
        beta = _pack_linear(self._alpha_hat, self._beta_hat, self._gamma)
        row_lam, row_mu = _design_rows(self._index[home], self._index[away], n)
        lam = float(np.exp(row_lam @ beta))
        mu = float(np.exp(row_mu @ beta))
        return lam, mu


def exponential_weights(dates, xi: float | None) -> np.ndarray:
    """Peso e^{−ξ Δt} rispetto alla data più recente. ξ assente o zero: peso 1."""
    stamps = np.asarray(dates, dtype="datetime64[D]")
    if xi is None or float(xi) == 0.0:
        return np.ones(stamps.shape[0], dtype=float)
    latest = np.nanmax(stamps)
    delta = (latest - stamps).astype("timedelta64[D]").astype(float)
    delta = np.nan_to_num(delta, nan=0.0)
    return np.exp(-float(xi) * delta)


def fit_matches(
    home_teams,
    away_teams,
    home_goals,
    away_goals,
    *,
    dates=None,
    xi: float | None = None,
    weights=None,
    shrink_threshold: float | None = _SHRINK_DEFAULT,
) -> DixonColesFit:
    """Stima α, β, γ e ρ. `shrink_threshold` None disattiva lo shrinkage."""
    home = np.asarray(home_teams, dtype=object)
    away = np.asarray(away_teams, dtype=object)
    hg = _as_goals(home_goals)
    ag = _as_goals(away_goals)
    if not (len(home) == len(away) == len(hg) == len(ag)) or len(home) == 0:
        raise ValueError("Servono gli stessi numeri di squadre e di gol, almeno una partita")

    teams = tuple(sorted(set(home.tolist()) | set(away.tolist())))
    if len(teams) < 2:
        raise ValueError("Servono almeno due squadre")
    index = {name: pos for pos, name in enumerate(teams)}
    h_idx = np.fromiter((index[name] for name in home), dtype=int, count=len(home))
    a_idx = np.fromiter((index[name] for name in away), dtype=int, count=len(away))

    match_weights = np.ones(len(home), dtype=float)
    if dates is not None:
        match_weights *= exponential_weights(dates, xi)
    if weights is not None:
        match_weights *= np.asarray(weights, dtype=float)
    if np.any(match_weights < 0):
        raise ValueError("I pesi devono essere non negativi")

    counts = {name: int(np.sum(h_idx == pos) + np.sum(a_idx == pos)) for name, pos in index.items()}
    x_lam, x_mu = _design_matrix(h_idx, a_idx, len(teams))
    theta0 = np.zeros(x_lam.shape[1] + 1)
    theta0[-2] = np.log(max(hg.mean(), 1e-3) / max(ag.mean(), 1e-3))
    theta0[-1] = -0.05
    bounds = [(-4.0, 4.0)] * x_lam.shape[1] + [RHO_BOUNDS]
    objective = _objective(x_lam, x_mu, hg, ag, match_weights)
    result = minimize(
        objective,
        theta0,
        method="L-BFGS-B",
        jac=True,
        bounds=bounds,
        options={"maxiter": 250, "ftol": 1e-12},
    )
    alpha_hat, beta_hat, gamma = _unpack_linear(result.x[:-1], len(teams))
    alpha, beta = _shrink(alpha_hat, beta_hat, teams, counts, shrink_threshold)
    attack, defense, away_base = _rescale_named(teams, alpha, beta)
    return DixonColesFit(
        teams=teams,
        attack=attack,
        defense=defense,
        home_advantage=float(np.exp(gamma)),
        away_base=away_base,
        rho=float(result.x[-1]),
        n_matches=counts,
        nll=float(result.fun),
        success=bool(result.success),
        _alpha=alpha,
        _beta=beta,
        _gamma=float(gamma),
        _alpha_hat=alpha_hat,
        _beta_hat=beta_hat,
        _index=index,
    )


def fit_league_from_db(
    db_path,
    competition_name: str,
    season,
    *,
    xi: float | None = None,
    shrink_threshold: float | None = _SHRINK_DEFAULT,
) -> DixonColesFit:
    """Fit sulle partite `status = 'FT'` di una lega e di una stagione in bagent.db."""
    import pandas as pd

    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(path)
    query = """
        SELECT date_gmt, home_team, away_team, home_goals, away_goals
        FROM matches
        WHERE status = 'FT'
          AND league = ?
          AND season = ?
          AND home_goals IS NOT NULL
          AND away_goals IS NOT NULL
    """
    with sqlite3.connect(path) as conn:
        frame = pd.read_sql_query(query, conn, params=(competition_name, str(season)))
    if frame.empty:
        raise ValueError(f"Nessuna partita FT per {competition_name} {season}")
    return fit_matches(
        frame["home_team"].to_numpy(),
        frame["away_team"].to_numpy(),
        frame["home_goals"].to_numpy(),
        frame["away_goals"].to_numpy(),
        dates=frame["date_gmt"].to_numpy(),
        xi=xi,
        shrink_threshold=shrink_threshold,
    )


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
    """α senza l'ultima squadra, β liberi, γ. L'ultima α è la somma a zero."""
    return np.concatenate([alpha[:-1], beta, np.array([gamma])])


def _unpack_linear(beta_free: np.ndarray, n_teams: int) -> tuple[np.ndarray, np.ndarray, float]:
    alpha = np.zeros(n_teams)
    alpha[:-1] = beta_free[: n_teams - 1]
    alpha[-1] = -np.sum(alpha[:-1])
    defense = beta_free[n_teams - 1 : 2 * n_teams - 1].copy()
    gamma = float(beta_free[-1])
    return alpha, defense, gamma


def _shrink(alpha, beta, teams, counts, threshold: float | None):
    if threshold is None or threshold <= 0:
        return alpha.copy(), beta.copy()
    shrunk_a = alpha.copy()
    shrunk_b = beta.copy()
    for pos, name in enumerate(teams):
        played = counts[name]
        if played < threshold:
            scale = played / threshold
            shrunk_a[pos] *= scale
            shrunk_b[pos] *= scale
    return shrunk_a, shrunk_b


def _objective(x_lam, x_mu, home_goals, away_goals, weights):
    """NLL e gradiente. Il tau di Dixon-Coles corregge solo 0-0, 0-1, 1-0 e 1-1."""

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
        log_lik = (
            np.log(tau_safe)
            + home_goals * log_lam
            - lam
            + away_goals * log_mu
            - mu
        )
        nll = float(-np.sum(weights * log_lik) + 1e6 * np.sum(invalid))
        g_lam = (home_goals - lam) + lam * dtau_dlam / tau_safe
        g_mu = (away_goals - mu) + mu * dtau_dmu / tau_safe
        grad_beta = -(x_lam.T @ (weights * g_lam) + x_mu.T @ (weights * g_mu))
        grad_rho = -np.sum(weights * dtau_drho / tau_safe)
        return nll, np.concatenate([grad_beta, np.array([grad_rho])])

    return value_and_grad


def _rescale_named(teams, alpha, beta) -> tuple[dict[str, float], dict[str, float], float]:
    center = float(np.mean(beta))
    away_base = float(np.exp(center))
    attack = {name: float(np.exp(alpha[pos])) for pos, name in enumerate(teams)}
    defense = {name: float(np.exp(beta[pos] - center)) for pos, name in enumerate(teams)}
    return attack, defense, away_base

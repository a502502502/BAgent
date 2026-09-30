"""Dixon-Coles MLE: design somma-zero, ρ, shrinkage e lettura da sqlite."""

import sqlite3
import time

import numpy as np
import pytest
from scipy.optimize import check_grad
from scipy.stats import poisson

from services.analysis.dixon_coles_mle import (
    exponential_weights,
    fit_league_from_db,
    fit_matches,
)


def _sample_score(rng, lam, mu, rho, max_goals=8):
    goals = np.arange(max_goals)
    grid = np.outer(poisson.pmf(goals, lam), poisson.pmf(goals, mu))
    tau = np.ones_like(grid)
    tau[0, 0] = 1.0 - lam * mu * rho
    tau[0, 1] = 1.0 + lam * rho
    tau[1, 0] = 1.0 + mu * rho
    tau[1, 1] = 1.0 - rho
    grid = np.clip(grid * tau, 0.0, None)
    grid /= grid.sum()
    flat = int(rng.choice(grid.size, p=grid.ravel()))
    return divmod(flat, max_goals)


def _season(n_teams=20, rho=-0.12, seed=7):
    rng = np.random.default_rng(seed)
    teams = [f"T{i:02d}" for i in range(n_teams)]
    attack = np.linspace(-0.35, 0.35, n_teams)
    attack -= attack.mean()
    defense = np.linspace(-0.25, 0.25, n_teams)
    defense -= defense.mean()
    gamma = 0.22
    home, away, hg, ag = [], [], [], []
    for i, host in enumerate(teams):
        for j, guest in enumerate(teams):
            if i == j:
                continue
            lam = float(np.exp(gamma + attack[i] + defense[j]))
            mu = float(np.exp(attack[j] + defense[i]))
            gh, ga = _sample_score(rng, lam, mu, rho)
            home.append(host)
            away.append(guest)
            hg.append(gh)
            ag.append(ga)
    return home, away, hg, ag, teams, attack


def test_gradient_matches_finite_differences():
    from services.analysis.dixon_coles_mle import _design_matrix, _objective

    home = np.array([0, 1, 2, 0, 3, 1])
    away = np.array([1, 2, 3, 2, 0, 3])
    hg = np.array([0, 1, 2, 1, 0, 1])
    ag = np.array([0, 0, 1, 1, 1, 2])
    x_lam, x_mu = _design_matrix(home, away, 4)
    fun_grad = _objective(x_lam, x_mu, hg, ag, np.ones(len(hg)))
    theta = np.zeros(x_lam.shape[1] + 1)
    theta[0] = 0.15
    theta[-2] = 0.2
    theta[-1] = -0.08

    def fun(point):
        return fun_grad(point)[0]

    def grad(point):
        return fun_grad(point)[1]

    assert check_grad(fun, grad, theta) < 1e-4


def test_design_row_matches_the_explicit_rates():
    home, away, hg, ag, _, _ = _season()
    model = fit_matches(home, away, hg, ag, shrink_threshold=None)
    for host, guest in list(zip(home, away))[::40]:
        explicit = model.rates_from_explicit(host, guest)
        design = model.rates_from_design(host, guest)
        assert explicit == pytest.approx(design, rel=1e-9, abs=1e-9)


def test_full_season_converges_within_one_and_a_half_seconds():
    home, away, hg, ag, _, _ = _season()
    assert len(home) == 380
    started = time.perf_counter()
    model = fit_matches(home, away, hg, ag, shrink_threshold=None)
    elapsed = time.perf_counter() - started
    assert elapsed < 1.5
    assert model.success
    assert -0.25 <= model.rho <= 0.25


def test_rho_and_attack_are_recovered():
    true_rho = -0.12
    home, away, hg, ag, teams, attack = _season(rho=true_rho, seed=11)
    model = fit_matches(home, away, hg, ag, shrink_threshold=None)
    assert model.rho == pytest.approx(true_rho, abs=0.08)
    order = [model._index[name] for name in teams]
    estimated = model._alpha_hat[order]
    assert np.corrcoef(attack, estimated)[0, 1] > 0.8
    assert estimated[int(np.argmax(attack))] > estimated[int(np.argmin(attack))]


def test_shrinkage_pulls_a_two_match_team_toward_one():
    hosts, guests, hg, ag = [], [], [], []
    regulars = ["A", "B", "C", "D", "E"]
    for i, home in enumerate(regulars):
        for away in regulars:
            if home == away:
                continue
            hosts += [home, home]
            guests += [away, away]
            hg += [1, 1]
            ag += [1, 1]
    hosts += ["Tiny", "Tiny"]
    guests += ["A", "B"]
    hg += [6, 6]
    ag += [0, 0]

    raw = fit_matches(hosts, guests, hg, ag, shrink_threshold=None)
    shrunk = fit_matches(hosts, guests, hg, ag, shrink_threshold=5)
    assert raw.n_matches["Tiny"] == 2
    assert shrunk.n_matches["Tiny"] < 3
    assert raw.attack["Tiny"] > 1.4
    assert abs(shrunk.attack["Tiny"] - 1.0) < abs(raw.attack["Tiny"] - 1.0)
    assert shrunk.attack["A"] == pytest.approx(raw.attack["A"])
    lam_raw, mu_raw = raw.expected_goals("A", "B")
    lam_shrunk, mu_shrunk = shrunk.expected_goals("A", "B")
    assert lam_shrunk == pytest.approx(lam_raw, rel=1e-9)
    assert mu_shrunk == pytest.approx(mu_raw, rel=1e-9)


def test_time_decay_downweights_old_matches():
    day = np.datetime64("2026-09-01")
    dates = np.array([day, day + np.timedelta64(100, "D")])
    weights = exponential_weights(dates, xi=0.01)
    assert weights[-1] == pytest.approx(1.0)
    assert weights[0] == pytest.approx(np.exp(-1.0))
    assert exponential_weights(dates, xi=None).tolist() == [1.0, 1.0]

    hosts, guests, hg, ag, played = [], [], [], [], []
    clubs = ["A", "B", "C", "D"]
    early = np.datetime64("2026-01-01")
    late = np.datetime64("2026-07-01")
    for stamp, hot_goals, conceded in ((early, 0, 2), (late, 3, 0)):
        for i, home in enumerate(clubs):
            for away in clubs[i + 1 :]:
                hosts.append(home)
                guests.append(away)
                hg.append(1)
                ag.append(1)
                played.append(stamp)
        for away in clubs:
            hosts.append("Hot")
            guests.append(away)
            hg.append(hot_goals)
            ag.append(conceded)
            played.append(stamp)
    flat = fit_matches(hosts, guests, hg, ag, dates=played, xi=0.0, shrink_threshold=None)
    recent = fit_matches(hosts, guests, hg, ag, dates=played, xi=0.02, shrink_threshold=None)
    assert recent.attack["Hot"] > flat.attack["Hot"]


def test_fit_league_from_db_uses_only_finished_matches(tmp_path):
    db = tmp_path / "bagent.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE matches (
            league TEXT, season TEXT, date_gmt TEXT, status TEXT,
            home_team TEXT, away_team TEXT, home_goals REAL, away_goals REAL
        )
        """
    )
    rows = [
        ("Serie A", "2026", "2026-09-01", "FT", "Milan", "Roma", 2, 1),
        ("Serie A", "2026", "2026-09-02", "FT", "Roma", "Milan", 0, 0),
        ("Serie A", "2026", "2026-09-03", "FT", "Milan", "Lazio", 1, 1),
        ("Serie A", "2026", "2026-09-04", "FT", "Lazio", "Roma", 1, 2),
        ("Serie A", "2026", "2026-09-05", "NS", "Milan", "Roma", None, None),
        ("Serie B", "2026", "2026-09-01", "FT", "Como", "Pisa", 4, 0),
    ]
    conn.executemany("INSERT INTO matches VALUES (?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()

    model = fit_league_from_db(db, "Serie A", 2026, shrink_threshold=None)
    assert set(model.teams) == {"Lazio", "Milan", "Roma"}
    assert "Como" not in model.teams
    lam, mu = model.expected_goals("Milan", "Roma")
    assert lam > 0 and mu > 0

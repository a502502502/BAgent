"""Dixon-Coles MLE: velocità, media degli attacchi, decay, shrinkage, niente rete."""

import sqlite3
import time
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from scipy.optimize import check_grad
from scipy.stats import poisson

from services.analysis.dixon_coles_mle import DixonColesMLE, _design_matrix, _objective


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


def _frame(home, away, hg, ag, dates=None) -> pd.DataFrame:
    if dates is None:
        dates = np.full(len(home), np.datetime64("2026-05-01"))
    return pd.DataFrame(
        {
            "home_team": home,
            "away_team": away,
            "home_goals": hg,
            "away_goals": ag,
            "date": dates,
        }
    )


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
    return _frame(home, away, hg, ag), teams, attack


def _tiny_league():
    home, away, hg, ag = [], [], [], []
    regulars = ["A", "B", "C", "D", "E"]
    for host in regulars:
        for guest in regulars:
            if host == guest:
                continue
            home += [host, host]
            away += [guest, guest]
            hg += [1, 1]
            ag += [1, 1]
    home += ["Tiny", "Tiny"]
    away += ["A", "B"]
    hg += [6, 6]
    ag += [0, 0]
    return _frame(home, away, hg, ag)


def test_gradient_matches_finite_differences():
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


def test_design_row_matches_predict_lambdas_without_shrinkage():
    frame, _, _ = _season()
    engine = DixonColesMLE(xi=0.0, shrinkage_m=0.0)
    engine.fit(frame)
    sample = frame.iloc[::40]
    for row in sample.itertuples(index=False):
        explicit = engine.predict_lambdas(row.home_team, row.away_team)
        design = engine._rates_from_design(row.home_team, row.away_team)
        assert explicit == pytest.approx(design, rel=1e-8, abs=1e-8)


def test_full_season_fits_within_one_and_a_half_seconds_and_attack_mean_is_one():
    frame, _, _ = _season()
    assert len(frame) == 380
    engine = DixonColesMLE()
    started = time.perf_counter()
    result = engine.fit(frame)
    assert time.perf_counter() - started < 1.5
    assert result.fit_time_seconds < 1.5
    attack_mean = float(np.mean(list(result.attack_params.values())))
    assert attack_mean == pytest.approx(1.0, abs=0.001)
    assert -0.25 <= result.rho <= 0.25


def test_rho_sign_and_attack_order_are_recovered():
    true_rho = -0.12
    frame, teams, attack = _season(rho=true_rho, seed=11)
    engine = DixonColesMLE(xi=0.0, shrinkage_m=0.0)
    result = engine.fit(frame)
    assert result.rho == pytest.approx(true_rho, abs=0.08)
    order = [engine._index[name] for name in teams]
    estimated = engine._alpha_hat[order]
    assert np.corrcoef(attack, estimated)[0, 1] > 0.8
    assert estimated[int(np.argmax(attack))] > estimated[int(np.argmin(attack))]


def test_two_match_team_shrinks_toward_one():
    frame = _tiny_league()
    pure = DixonColesMLE(xi=0.0, shrinkage_m=0.0).fit(frame)
    shrunk = DixonColesMLE(xi=0.0, shrinkage_m=3.0).fit(frame)
    assert pure.sample_sizes["Tiny"] == 2
    played, prior = 2.0, 3.0
    expected = played / (played + prior) * pure.attack_params["Tiny"] + prior / (played + prior)
    assert shrunk.attack_params["Tiny"] == pytest.approx(expected)
    assert abs(shrunk.attack_params["Tiny"] - 1.0) < abs(pure.attack_params["Tiny"] - 1.0)
    expected_defense = played / (played + prior) * pure.defense_params["Tiny"] + prior / (played + prior)
    assert shrunk.defense_params["Tiny"] == pytest.approx(expected_defense)


def test_matches_from_six_months_ago_weigh_less_than_recent_ones():
    home, away, hg, ag, played = [], [], [], [], []
    clubs = ["A", "B", "C", "D"]
    early = np.datetime64("2026-01-01")
    late = np.datetime64("2026-07-01")
    for stamp, hot_goals, conceded in ((early, 0, 2), (late, 3, 0)):
        for i, host in enumerate(clubs):
            for guest in clubs[i + 1 :]:
                home.append(host)
                away.append(guest)
                hg.append(1)
                ag.append(1)
                played.append(stamp)
        for guest in clubs:
            home.append("Hot")
            away.append(guest)
            hg.append(hot_goals)
            ag.append(conceded)
            played.append(stamp)
    frame = _frame(home, away, hg, ag, played)
    reference = datetime(2026, 7, 1)
    flat = DixonColesMLE(xi=0.0, shrinkage_m=0.0).fit(frame, reference_date=reference)
    recent = DixonColesMLE(xi=0.0019, shrinkage_m=0.0).fit(frame, reference_date=reference)
    assert recent.attack_params["Hot"] > flat.attack_params["Hot"]
    gap_days = (late - early) / np.timedelta64(1, "D")
    assert np.exp(-0.0019 * float(gap_days)) < 1.0


def test_score_matrix_uses_tau_and_sums_to_one():
    engine = DixonColesMLE(xi=0.0, shrinkage_m=0.0)
    engine.fit(_season(rho=-0.12, seed=3)[0])
    names = list(engine.result.attack_params)
    matrix = engine.generate_score_matrix(names[0], names[1], max_goals=7)
    assert matrix.shape == (8, 8)
    assert matrix.sum() == pytest.approx(1.0)
    lam, mu = engine.predict_lambdas(names[0], names[1])
    independent = poisson.pmf(0, lam) * poisson.pmf(0, mu)
    if engine.result.rho < 0:
        assert matrix[0, 0] > independent * 0.5


def test_fit_from_db_keeps_finished_matches_of_one_competition(tmp_path):
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
        ("Serie A", "2025", "2025-09-01", "FT", "Juve", "Napoli", 1, 0),
    ]
    conn.executemany("INSERT INTO matches VALUES (?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()

    result = DixonColesMLE(xi=0.0, shrinkage_m=0.0).fit_from_db(db, "Serie A", season="2026")
    assert set(result.attack_params) == {"Lazio", "Milan", "Roma"}
    assert "Como" not in result.attack_params
    assert "Juve" not in result.attack_params

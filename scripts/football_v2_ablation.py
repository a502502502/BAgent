import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import math

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset
from services.football_backtester import FootballBacktester
from services.football_historical_profile import FootballHistoricalProfile
from services.football_team_strength_factor import FootballTeamStrengthFactor


def score(
    win,
    goal,
    mh,
    md,
    ma,
    mode,
):
    # Coefficienti V2 ufficiali
    if mode == "FULL":
        wi, wg = 0.1861200968, 0.0441877135
        di, dg = -0.1134477779, -0.0124175087
        ai, ag = -0.0726723189, -0.0317702048
        h = (1.4750910499, -0.1955832904, -1.2227137413)
        d = (-0.1880471526, 0.1290842096, -0.0889775531)
        a = (-1.2870438973, 0.0664990808, 1.3116912944)
        ints = (0.0567940181, -0.1479404962, 0.0911464780)

    elif mode == "NO_WIN":
        wi = wg = 0.0
        di = dg = 0.0
        ai = ag = 0.0
        h = (1.4750910499, -0.1955832904, -1.2227137413)
        d = (-0.1880471526, 0.1290842096, -0.0889775531)
        a = (-1.2870438973, 0.0664990808, 1.3116912944)
        ints = (0.0567940181, -0.1479404962, 0.0911464780)

    elif mode == "NO_GOAL":
        wi = 0.1861200968
        di = -0.1134477779
        ai = -0.0726723189
        wg = dg = ag = 0.0
        h = (1.4750910499, -0.1955832904, -1.2227137413)
        d = (-0.1880471526, 0.1290842096, -0.0889775531)
        a = (-1.2870438973, 0.0664990808, 1.3116912944)
        ints = (0.0567940181, -0.1479404962, 0.0911464780)

    elif mode == "MARKET":
        wi = wg = di = dg = ai = ag = 0.0
        h = (1.4750910499, -0.1955832904, -1.2227137413)
        d = (-0.1880471526, 0.1290842096, -0.0889775531)
        a = (-1.2870438973, 0.0664990808, 1.3116912944)
        ints = (0.0567940181, -0.1479404962, 0.0911464780)

    elif mode == "HISTORY":
        wi, wg = 0.1861200968, 0.0441877135
        di, dg = -0.1134477779, -0.0124175087
        ai, ag = -0.0726723189, -0.0317702048
        h = d = a = (0.0, 0.0, 0.0)
        ints = (0.0567940181, -0.1479404962, 0.0911464780)

    elif mode == "MARKET_WIN":
        wg = dg = ag = 0.0
        wi = 0.1861200968
        di = -0.1134477779
        ai = -0.0726723189
        h = (1.4750910499, -0.1955832904, -1.2227137413)
        d = (-0.1880471526, 0.1290842096, -0.0889775531)
        a = (-1.2870438973, 0.0664990808, 1.3116912944)
        ints = (0.0567940181, -0.1479404962, 0.0911464780)

    elif mode == "MARKET_GOAL":
        wi = di = ai = 0.0
        wg = 0.0441877135
        dg = -0.0124175087
        ag = -0.0317702048
        h = (1.4750910499, -0.1955832904, -1.2227137413)
        d = (-0.1880471526, 0.1290842096, -0.0889775531)
        a = (-1.2870438973, 0.0664990808, 1.3116912944)
        ints = (0.0567940181, -0.1479404962, 0.0911464780)

    else:
        raise ValueError(mode)

    home = (
        ints[0]
        + wi * win
        + wg * goal
        + h[0] * mh
        + d[0] * md
        + a[0] * ma
    )

    draw = (
        ints[1]
        + di * win
        + dg * goal
        + h[1] * mh
        + d[1] * md
        + a[1] * ma
    )

    away = (
        ints[2]
        + ai * win
        + ag * goal
        + h[2] * mh
        + d[2] * md
        + a[2] * ma
    )

    mx = max(home, draw, away)

    ph = math.exp(home - mx)
    pd = math.exp(draw - mx)
    pa = math.exp(away - mx)

    total = ph + pd + pa

    return ph / total, pd / total, pa / total


loader = FootballDataLoader()

files = sorted(
    Path("data/football/raw").glob("E0_*.csv")
)

matches = []

for f in files:
    matches.extend(loader.load(f))

dataset = FootballHistoricalDataset(matches)
profile = FootballHistoricalProfile(dataset)
factor = FootballTeamStrengthFactor()

rows = []

for hm in dataset.all():

    if not hm.is_completed:
        continue

    if hm.odds is None or not hm.odds.is_1x2_available:
        continue

    home = profile.get_team_profile(
        hm.match.home.id,
        hm.date,
    )

    away = profile.get_team_profile(
        hm.match.away.id,
        hm.date,
    )

    if home is None or away is None:
        continue

    contribution = factor.evaluate(home, away)

    if contribution is None:
        continue

    details = contribution.details

    inv_h = 1.0 / hm.odds.home
    inv_d = 1.0 / hm.odds.draw
    inv_a = 1.0 / hm.odds.away

    overround = inv_h + inv_d + inv_a

    mh = inv_h / overround
    md = inv_d / overround
    ma = inv_a / overround

    rows.append(
        (
            hm.date,
            details["difference"],
            details["goal_difference"],
            mh,
            md,
            ma,
            {"HOME": 0, "DRAW": 1, "AWAY": 2}[hm.result],
        )
    )


rows.sort(key=lambda x: x[0])

# Usiamo la stessa struttura temporale del backtest:
# per ogni partita le feature sono costruite prima del match.
# Qui confrontiamo direttamente le formule V2 sullo stesso insieme.

modes = [
    "FULL",
    "NO_WIN",
    "NO_GOAL",
    "MARKET",
    "HISTORY",
    "MARKET_WIN",
    "MARKET_GOAL",
]

print()
print("V2 ABLATION")
print("===========")
print("ROWS:", len(rows))
print()

for mode in modes:

    log_loss = 0.0
    brier = 0.0
    correct = 0

    for (
        _,
        win,
        goal,
        mh,
        md,
        ma,
        actual,
    ) in rows:

        ph, pd, pa = score(
            win,
            goal,
            mh,
            md,
            ma,
            mode,
        )

        probabilities = [ph, pd, pa]

        predicted = max(
            range(3),
            key=lambda i: probabilities[i],
        )

        if predicted == actual:
            correct += 1

        log_loss += -math.log(
            max(probabilities[actual], 1e-15)
        )

        actual_vector = [
            1.0 if actual == i else 0.0
            for i in range(3)
        ]

        brier += sum(
            (probabilities[i] - actual_vector[i]) ** 2
            for i in range(3)
        )

    n = len(rows)

    print(
        f"{mode:12s}"
        f" ACC={correct / n:.6f}"
        f" LOGLOSS={log_loss / n:.6f}"
        f" BRIER={brier / n:.6f}"
    )

print()
print("REFERENCE CURRENT V2")
print("ACC=0.541228")
print("LOGLOSS=0.968937")
print("BRIER=0.575667")

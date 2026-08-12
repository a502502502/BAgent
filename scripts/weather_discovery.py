import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

weather_path = Path("data/football/weather_enriched.json")
data = json.loads(weather_path.read_text())

print("TOTAL ROWS:", len(data))
print("DRAW ROWS:", sum(1 for d in data if d["result"] == "DRAW"))
print()

feature_names = ["temperature", "precipitation", "wind_speed"]

# --- Discovery per DRAW ---
print("=== SEGNALE METEO vs DRAW ===")
print(f"{'FEATURE':20s} {'DRAW_MEAN':>12s} {'NONDRAW_MEAN':>14s} {'COHENS_D':>10s}")
print("-" * 60)

for name in feature_names:
    d = np.array([row[name] for row in data if row["result"] == "DRAW"])
    nd = np.array([row[name] for row in data if row["result"] != "DRAW"])

    d_mean = d.mean()
    nd_mean = nd.mean()

    pooled_std = np.sqrt(
        ((len(d) - 1) * d.std(ddof=1) ** 2 + (len(nd) - 1) * nd.std(ddof=1) ** 2)
        / (len(d) + len(nd) - 2)
    )

    cohens_d = (d_mean - nd_mean) / pooled_std if pooled_std > 0 else 0.0

    print(f"{name:20s} {d_mean:12.4f} {nd_mean:14.4f} {cohens_d:10.4f}")

# --- Discovery per HOME (extra: forse il meteo aiuta di più HOME che DRAW) ---
print()
print("=== SEGNALE METEO vs HOME WIN ===")
print(f"{'FEATURE':20s} {'HOME_MEAN':>12s} {'NONHOME_MEAN':>14s} {'COHENS_D':>10s}")
print("-" * 60)

for name in feature_names:
    h = np.array([row[name] for row in data if row["result"] == "HOME"])
    nh = np.array([row[name] for row in data if row["result"] != "HOME"])

    h_mean = h.mean()
    nh_mean = nh.mean()

    pooled_std = np.sqrt(
        ((len(h) - 1) * h.std(ddof=1) ** 2 + (len(nh) - 1) * nh.std(ddof=1) ** 2)
        / (len(h) + len(nh) - 2)
    )

    cohens_d = (h_mean - nh_mean) / pooled_std if pooled_std > 0 else 0.0

    print(f"{name:20s} {h_mean:12.4f} {nh_mean:14.4f} {cohens_d:10.4f}")

# --- Extra: precipitazione come categoria (pioggia sì/no) ---
print()
print("=== PIOGGIA (sì/no) vs RISULTATO ===")

has_rain = [row for row in data if row["precipitation"] > 0.5]
no_rain = [row for row in data if row["precipitation"] <= 0.5]

print(f"Partite con pioggia (>0.5mm): {len(has_rain)}")
print(f"Partite senza pioggia: {len(no_rain)}")
print()

for label, subset in [("CON PIOGGIA", has_rain), ("SENZA PIOGGIA", no_rain)]:
    total = len(subset)
    if total == 0:
        continue
    home = sum(1 for r in subset if r["result"] == "HOME") / total
    draw = sum(1 for r in subset if r["result"] == "DRAW") / total
    away = sum(1 for r in subset if r["result"] == "AWAY") / total
    print(f"{label:15s}  HOME={home:.1%}  DRAW={draw:.1%}  AWAY={away:.1%}  (n={total})")

# --- Extra: vento forte ---
print()
print("=== VENTO FORTE (>20 km/h) vs RISULTATO ===")

windy = [row for row in data if row["wind_speed"] > 20]
calm = [row for row in data if row["wind_speed"] <= 20]

print(f"Partite ventose (>20km/h): {len(windy)}")
print(f"Partite calme: {len(calm)}")
print()

for label, subset in [("VENTOSE", windy), ("CALME", calm)]:
    total = len(subset)
    if total == 0:
        continue
    home = sum(1 for r in subset if r["result"] == "HOME") / total
    draw = sum(1 for r in subset if r["result"] == "DRAW") / total
    away = sum(1 for r in subset if r["result"] == "AWAY") / total
    print(f"{label:15s}  HOME={home:.1%}  DRAW={draw:.1%}  AWAY={away:.1%}  (n={total})")

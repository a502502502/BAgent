"""Calcolo completo proiezioni e quote stimate per le partite di stasera."""

import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from services.analysis.xg_poisson_engine import QuantitativeEngine

engine = QuantitativeEngine(rho=-0.05)

# Lambdas stimate dai match recenti di Nations League (ottobre 2026):
# Italia: 0 gol col Belgio, 4 in Turchia -> lambda home 1.85, away Turchia 0.95
# Francia: 1 in Turchia, 1 in Belgio -> lambda home 1.70, away Belgio 1.10
# Bosnia: 2 con Romania, 1 con Svezia -> lambda home 1.25, away Polonia 1.45
# Ucraina: 1 con Ungheria/Georgia -> lambda home 1.20, away Ungheria 0.90
# Irlanda del Nord: 0-1 con Ucraina -> lambda home 1.15, away Georgia 1.05

nl_fixtures = [
    ("Francia", "Belgio", 1.70, 1.10, "Francia vs Belgio"),
    ("Italia", "Turchia", 1.85, 0.95, "Italia vs Turchia"),
    ("Bosnia Erzegovina", "Polonia", 1.25, 1.45, "Bosnia vs Polonia"),
    ("Ucraina", "Ungheria", 1.20, 0.90, "Ucraina vs Ungheria"),
    ("Irlanda Del Nord", "Georgia", 1.15, 1.05, "Irlanda Del Nord vs Georgia"),
]

markets_to_price = [
    "1X",
    "X2",
    "12",
    "Under 2.5",
    "Over 1.5",
    "Under 3.5",
    "Gol in entrambi i tempi",
    "Casa Segna in Entrambi i Tempi: SI",
    "Ospite Segna in Entrambi i Tempi: SI",
    "1X + Under 3.5",
    "1X + Under 4.5",
    "X2 + Under 3.5",
    "1X + Over 1.5",
    "Chance Mix: 1X o Gol",
    "MultiGol 1-4 Casa",
    "MultiGol 0-1 1° Tempo",
    "Under 1.5 1° Tempo",
]

print("=" * 80)
print("🇪🇺 PROIEZIONI QUANTITATIVE NATIONS LEAGUE (05/10/2026)")
print("=" * 80)

for home, away, lam_h, lam_a, label in nl_fixtures:
    print(f"\n⚽ MATCH: {label} (Ore 20:45)")
    print(f"📊 xG attesi: {home} {lam_h:.2f} vs {away} {lam_a:.2f}")
    print("-" * 80)
    print(f"  {'Mercato':<35} {'Probabilità':<12} {'Fair Odd':<10}")
    print("  " + "-" * 60)

    for m in markets_to_price:
        p = engine.goal_market_probability(lam_h, lam_a, m)
        if p is not None and p >= 0.65:
            fair = 1.0 / p
            print(f"  {m:<35} {p*100:>6.1f}%      {fair:>5.2f}")

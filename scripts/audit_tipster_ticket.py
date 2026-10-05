import sys
from pathlib import Path
ROOT = Path("C:/Project/BAgent")
sys.path.insert(0, str(ROOT))

from services.analysis.xg_poisson_engine import QuantitativeEngine

engine = QuantitativeEngine(rho=-0.05)

# Leg 1: Bosnia - Polonia
# xG: Bosnia 1.15, Polonia 1.35
# Market: MultiGol 0-2 1°Tempo + 1-3 2°Tempo
p_leg1 = engine.goal_market_probability(1.15, 1.35, "0-2 1°T + 1-3 2°T")
# Let's also compute manually first and second half
first_half_lam = (1.15 + 1.35) * 0.45 # ~1.125
second_half_lam = (1.15 + 1.35) * 0.55 # ~1.375

import math
def pois(k, l): return (l**k * math.exp(-l)) / math.factorial(k)

# First half: 0 to 2 goals
p_1t_02 = sum(pois(k, first_half_lam) for k in range(3))
# Second half: 1 to 3 goals (fails on 0 goals or >=4 goals)
p_2t_13 = sum(pois(k, second_half_lam) for k in range(1, 4))
p_leg1_manual = p_1t_02 * p_2t_13

# Leg 2: Francia - Belgio
# xG Francia 1.75, Belgio 1.05
# Market: MultiGol 2-5 Casa (Francia segna 2, 3, 4 o 5 gol)
p_francia_25 = sum(pois(k, 1.75) for k in range(2, 6))

# Leg 3: Italia - Turchia
# xG Italia 2.05, Turchia 0.80
# Market: 1X + MultiGol 2-5
# Matrix evaluation
p_it_1x_mg25 = 0.0
for h in range(8):
    for a in range(8):
        prob = pois(h, 2.05) * pois(a, 0.80)
        tot = h + a
        if h >= a and (2 <= tot <= 5):
            p_it_1x_mg25 += prob

# Prob of 1-0 or 0-0 for Italia
p_10 = pois(1, 2.05) * pois(0, 0.80)
p_00 = pois(0, 2.05) * pois(0, 0.80)

# Leg 4: Romania - Svezia Corner 1X2 = 2
# Expected corners: Romania ~3.8, Svezia ~5.8
# Skellam / Bivariate corner model
lam_c_rom = 3.8
lam_c_swe = 5.8
p_swe_more_corners = 0.0
for c_rom in range(15):
    for c_swe in range(15):
        pr = pois(c_rom, lam_c_rom) * pois(c_swe, lam_c_swe)
        if c_swe > c_rom:
            p_swe_more_corners += pr

print(f"--- ANALISI QUANTITATIVA SCHEDINA TIPSTER ---")
print(f"Leg 1: Bosnia-Polonia MultiGol 0-2 1T + 1-3 2T: Quota 1.43 | Prob: {p_leg1_manual*100:.1f}% | Fair: {1/p_leg1_manual:.2f} | EV: {(p_leg1_manual*1.43-1)*100:+.1f}%")
print(f"Leg 2: Francia-Belgio MultiGol 2-5 Casa:       Quota 1.49 | Prob: {p_francia_25*100:.1f}% | Fair: {1/p_francia_25:.2f} | EV: {(p_francia_25*1.49-1)*100:+.1f}%")
print(f"Leg 3: Italia-Turchia 1X + MultiGol 2-5:       Quota 1.34 | Prob: {p_it_1x_mg25*100:.1f}% | Fair: {1/p_it_1x_mg25:.2f} | EV: {(p_it_1x_mg25*1.34-1)*100:+.1f}%")
print(f"   -> Rischio trappola 1-0/0-0: {((p_10+p_00)*100):.1f}% di probabilita che uccide la giocata!")
print(f"Leg 4: Romania-Svezia Corner 1X2: 2:           Quota 1.75 | Prob: {p_swe_more_corners*100:.1f}% | Fair: {1/p_swe_more_corners:.2f} | EV: {(p_swe_more_corners*1.75-1)*100:+.1f}%")

total_prob = p_leg1_manual * p_francia_25 * p_it_1x_mg25 * p_swe_more_corners
total_odd = 1.43 * 1.49 * 1.34 * 1.75
fair_total = 1.0 / total_prob
print(f"\nSCHEDINA TOTALE TIPSTER:")
print(f"Quota Totale: {total_odd:.2f}")
print(f"Probabilita Congiunta: {total_prob*100:.2f}% (Quota Equa: {fair_total:.2f})")
print(f"Edge Globale della Schedina: {(total_prob * total_odd - 1)*100:+.1f}%")

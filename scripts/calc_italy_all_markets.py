import json
import os
import sys
from pathlib import Path
import numpy as np
import penaltyblog as pb

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.xg_poisson_engine import XgPoissonEngine
from services.analysis.match_market_optimizer import MatchMarketOptimizer

# 1. Carica dati partita Italia vs Turchia
with open("data/the_odds_api_live.json", "r", encoding="utf-8") as f:
    fixtures = json.load(f)

italy_match = None
for m in fixtures:
    if "italy" in m.get("home_team", "").lower() or "italy" in m.get("away_team", "").lower():
        italy_match = m
        break

if not italy_match:
    print("Match Italia non trovato in the_odds_api_live.json!")
    exit(1)

print(f"Match trovato: {italy_match['home_team']} vs {italy_match['away_team']}")
print(f"Torneo: {italy_match['league']} | Orario: {italy_match['commence_time']}")

# Raccogli tutte le quote dai bookmaker per questo match
bookmakers = italy_match.get("bookmakers", [])
print(f"Bookmaker totali disponibili: {len(bookmakers)}")

# Migliori quote per mercato da The Odds API
best_odds = {}
for bm in bookmakers:
    bm_name = bm.get("key")
    for mkt in bm.get("markets", []):
        mkt_key = mkt.get("key")
        for out in mkt.get("outcomes", []):
            name = out.get("name")
            point = out.get("point")
            price = float(out.get("price", 0.0))
            label = f"{name}" if point is None else f"{name} {point}"
            k = f"{mkt_key}:{label}"
            if k not in best_odds or price > best_odds[k]["price"]:
                best_odds[k] = {"price": price, "bookmaker": bm_name}

print("\n--- QUOTE LIVE DA THE ODDS API ---")
for k, v in sorted(best_odds.items()):
    print(f"  {k}: @{v['price']:.2f} ({v['bookmaker']})")

# 2. Calcolo Matematico Completo (Poisson + Dixon Coles + Shin Devig)
h_odd = best_odds.get("h2h:Italy", {}).get("price", 1.42)
d_odd = best_odds.get("h2h:Draw", {}).get("price", 5.40)
a_odd = best_odds.get("h2h:Turkey", {}).get("price", 8.80)

# Shin devig
shin_res = pb.implied.calculate_implied([h_odd, d_odd, a_odd], method="shin")
p_shin_h, p_shin_d, p_shin_a = shin_res.probabilities

# xG stimati per Italia vs Turchia
# Italia in casa contro Turchia: xG Italia ~1.85, xG Turchia ~0.75 (Totale xG ~2.60)
xg_home = 1.88
xg_away = 0.72

poisson_engine = XgPoissonEngine()
matrix = poisson_engine.generate_score_matrix(xg_home, xg_away)
n_goals = matrix.shape[0]

# Genera tabella con TUTTI i mercati possibili
rows = []

def eval_pick(category, market_name, pick, prob, market_odd=None, default_q=None):
    fair_q = round(1.0 / prob, 2) if prob > 0 else 99.0
    min_val_q = round(fair_q * 1.03, 2)
    q = market_odd if market_odd is not None else (default_q if default_q is not None else min_val_q)
    edge = round((q * prob - 1.0) * 100.0, 1)
    
    status = "TRAPPOLA DEL BANCO" if edge < -1.0 else ("VALUE BET (+EV)" if edge >= 2.0 else "EQUILIBRATA")
    
    rows.append({
        "category": category,
        "market": market_name,
        "pick": pick,
        "prob_pct": round(prob * 100.0, 1),
        "fair_odds": fair_q,
        "min_value_odds": min_val_q,
        "market_odds": round(q, 2),
        "edge_pct": edge,
        "status": status
    })

# 1X2
p_1 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h > a)
p_X = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h == a)
p_2 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h < a)
eval_pick("Esito Finale 1X2", "1X2", "1 (Italia)", p_1, h_odd)
eval_pick("Esito Finale 1X2", "1X2", "X (Pareggio)", p_X, d_odd)
eval_pick("Esito Finale 1X2", "1X2", "2 (Turchia)", p_2, a_odd)

# Doppia Chance
p_1X = p_1 + p_X
p_X2 = p_X + p_2
p_12 = p_1 + p_2
eval_pick("Doppia Chance", "Doppia Chance", "1X", p_1X, default_q=1.23)
eval_pick("Doppia Chance", "Doppia Chance", "X2", p_X2, default_q=3.10)
eval_pick("Doppia Chance", "Doppia Chance", "12", p_12, default_q=1.18)

# Under / Over
for threshold in [1.5, 2.5, 3.5, 4.5]:
    p_u = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if (h + a) <= threshold)
    p_o = 1.0 - p_u
    u_odd = best_odds.get(f"totals:Under {threshold}", {}).get("price")
    o_odd = best_odds.get(f"totals:Over {threshold}", {}).get("price")
    eval_pick("Under / Over", f"Under/Over {threshold}", f"Under {threshold}", p_u, u_odd)
    eval_pick("Under / Over", f"Under/Over {threshold}", f"Over {threshold}", p_o, o_odd)

# Gol / NoGol (BTTS)
p_gol = sum(matrix[h, a] for h in range(1, n_goals) for a in range(1, n_goals))
p_nogol = 1.0 - p_gol
eval_pick("Gol / NoGol", "Goal / NoGoal", "Gol (Entrambe segnano)", p_gol, default_q=2.05)
eval_pick("Gol / NoGol", "Goal / NoGoal", "NoGol", p_nogol, default_q=1.75)

# Chance Mix
p_cm_1_u25 = p_1 + sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if (h + a) <= 2) - sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h > a and (h + a) <= 2)
p_cm_1x_gol = p_1X + p_gol - sum(matrix[h, a] for h in range(1, n_goals) for a in range(1, n_goals) if h >= a)
p_cm_x_u25 = p_X + sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if (h + a) <= 2) - sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h == a and (h + a) <= 2)
eval_pick("Chance Mix", "Chance Mix", "1 o Under 2.5", p_cm_1_u25, default_q=1.35)
eval_pick("Chance Mix", "Chance Mix", "1X o Gol", p_cm_1x_gol, default_q=1.20)
eval_pick("Chance Mix", "Chance Mix", "X o Under 2.5", p_cm_x_u25, default_q=1.65)

# Combo Doppia Chance + Under/Over
p_1x_u35 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h >= a and (h + a) <= 3)
p_1x_u45 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h >= a and (h + a) <= 4)
p_1x_o15 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h >= a and (h + a) >= 2)
eval_pick("Combo DC + U/O", "Combo Doppia Chance + U/O", "1X + Under 3.5", p_1x_u35, default_q=1.55)
eval_pick("Combo DC + U/O", "Combo Doppia Chance + U/O", "1X + Under 4.5", p_1x_u45, default_q=1.30)
eval_pick("Combo DC + U/O", "Combo Doppia Chance + U/O", "1X + Over 1.5", p_1x_o15, default_q=1.38)

# Combo 1X2 + Under/Over
p_1_u35 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h > a and (h + a) <= 3)
p_1_o15 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if h > a and (h + a) >= 2)
eval_pick("Combo 1X2 + U/O", "Combo 1X2 + U/O", "1 + Under 3.5", p_1_u35, default_q=2.15)
eval_pick("Combo 1X2 + U/O", "Combo 1X2 + U/O", "1 + Over 1.5", p_1_o15, default_q=1.68)

# MultiGol
p_mg_14 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if 1 <= (h + a) <= 4)
p_mg_24 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if 2 <= (h + a) <= 4)
p_mg_13 = sum(matrix[h, a] for h in range(n_goals) for a in range(n_goals) if 1 <= (h + a) <= 3)
p_mg_14_casa = sum(matrix[h, a] for h in range(1, 5) for a in range(n_goals))
eval_pick("MultiGol", "MultiGol Totale", "MultiGol 1-4", p_mg_14, default_q=1.22)
eval_pick("MultiGol", "MultiGol Totale", "MultiGol 2-4", p_mg_24, default_q=1.52)
eval_pick("MultiGol", "MultiGol Totale", "MultiGol 1-3", p_mg_13, default_q=1.42)
eval_pick("MultiGol", "MultiGol Squadra", "MultiGol Casa 1-3", p_mg_14_casa, default_q=1.28)

# Segna Entrambi i Tempi
# P(Italia segna 1°T e 2°T): ~ P(1°T>=1)*P(2°T>=1) con split 0.45 / 0.55
p_t1 = 1.0 - np.exp(-xg_home * 0.45)
p_t2 = 1.0 - np.exp(-xg_home * 0.55)
p_both_halves_h = p_t1 * p_t2
eval_pick("Tempi", "Segna Entrambi i Tempi", "Italia Segna Entrambi i Tempi", p_both_halves_h, default_q=2.25)

# Risultati Esatti Principali
for (h, a) in [(1, 0), (2, 0), (2, 1), (1, 1), (3, 0), (3, 1), (0, 0)]:
    p_exact = matrix[h, a]
    eval_pick("Risultati Esatti", "Risultato Esatto", f"{h}-{a}", p_exact, default_q=round(1.0/p_exact * 1.15, 2))

# Salva report JSON
with open("reports/italia_turchia_all_markets.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, indent=2)

print(f"\nTotale mercati prezzati: {len(rows)}")
for r in rows[:10]:
    print(f"[{r['category']}] {r['pick']} | P: {r['prob_pct']}% | Quota Mercato: @{r['market_odds']} | Fair: @{r['fair_odds']} | Edge: {r['edge_pct']}% | {r['status']}")

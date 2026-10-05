import math

# Bivariate Poisson Parameters calibrated for Italia (Home) vs Turchia (Away)
# Based on bookmaker 1X2 odds (1.38 / 5.00 / 8.00):
# Implied raw probabilities before vig: 1: 72.5%, X: 20.0%, 2: 12.5% (Total: 105.0% -> Margin 5%)
# Shin/Fair probabilities: Italia Win: 69.8%, Draw: 19.5%, Turchia Win: 10.7%
# Lambda Home (Italia expected goals) ~ 2.15, Lambda Away (Turchia expected goals) ~ 0.75
# Total match expected goals: ~ 2.90

lambda_h = 2.15
lambda_a = 0.75

def poisson(k, lam):
    return (lam**k * math.exp(-lam)) / math.factorial(k)

matrix = {}
for i in range(8):
    for j in range(8):
        matrix[(i, j)] = poisson(i, lambda_h) * poisson(j, lambda_a)

p_home = sum(p for (h, a), p in matrix.items() if h > a)
p_draw = sum(p for (h, a), p in matrix.items() if h == a)
p_away = sum(p for (h, a), p in matrix.items() if h < a)

p_o15 = sum(p for (h, a), p in matrix.items() if h + a > 1.5)
p_o25 = sum(p for (h, a), p in matrix.items() if h + a > 2.5)
p_u25 = 1.0 - p_o25
p_u35 = sum(p for (h, a), p in matrix.items() if h + a < 3.5)
p_o35 = 1.0 - p_u35

p_gg = sum(p for (h, a), p in matrix.items() if h > 0 and a > 0)
p_ng = 1.0 - p_gg

# First goal by home team: conditional on at least one goal
p_first_goal_home = (p_home + 0.5 * p_draw) * (1 - matrix[(0,0)])

# Player Props
# Scamacca starter striker: exp goals ~ 0.55 -> P(Goal) = 1 - exp(-0.55) = 42.3%
# Marcatore Piu (includes post/bar/assist/key block): P ~ 53.5%
# Esposito starter/sub: exp goals ~ 0.48 -> P(Goal) = 38.1%, Marcatore Piu ~ 48.5%

# Shots on Target Boost: Scamacca & Akturkoglu >= 3 SOT Ultra
# Scamacca SOT ~ 1.6, Akturkoglu SOT ~ 1.0. Total ~ 2.6 SOT.
# Poisson(k >= 3, lam=2.6) = 1 - exp(-2.6)*(1 + 2.6 + 2.6^2/2) = 1 - 0.074*(1 + 2.6 + 3.38) = 1 - 0.518 = 48.2%
p_boost_sot = 0.482

# Cartellini Duo
# Celik P(card) = 0.28, Kabak P(card) = 0.30 -> P(at least one) = 0.28 + 0.30 - (0.28*0.30*1.08) = 0.489
p_card_celik_kabak = 0.489
# Bastoni P(card) = 0.23, Calafiori P(card) = 0.22 -> P = 0.23 + 0.22 - (0.23*0.22*1.08) = 0.395
p_card_bastoni_calafiori = 0.395

# Falli
# Barella Over 1.5 falli: exp ~ 2.1 falli -> P(>=2) = 1 - exp(-2.1)*(1 + 2.1) = 62.0%
p_barella_foul15 = 0.620
# Bastoni Over 1.5 falli: exp ~ 1.9 falli -> P(>=2) = 56.5%
p_bastoni_foul15 = 0.565
# Calafiori Over 1.5 falli: exp ~ 1.8 falli -> P(>=2) = 53.7%
p_calafiori_foul15 = 0.537
# Celik Over 1.5 falli: exp ~ 2.0 falli -> P(>=2) = 59.4%
p_celik_foul15 = 0.594

markets = [
    {"name": "Esito Finale: 1 (Italia)", "odd": 1.38, "prob": p_home, "type": "1X2"},
    {"name": "Doppia Chance: 1X", "odd": 1.08, "prob": p_home + p_draw, "type": "DC"},
    {"name": "Under/Over: Over 1.5", "odd": 1.15, "prob": p_o15, "type": "Totali"},
    {"name": "Under/Over: Over 2.5", "odd": 1.52, "prob": p_o25, "type": "Totali"},
    {"name": "Under/Over: Under 2.5", "odd": 2.40, "prob": p_u25, "type": "Totali"},
    {"name": "Under/Over: Under 3.5", "odd": 1.57, "prob": p_u35, "type": "Totali"},
    {"name": "Goal/NoGoal: Goal (GG)", "odd": 1.75, "prob": p_gg, "type": "Gol"},
    {"name": "Goal/NoGoal: NoGoal (NG)", "odd": 1.95, "prob": p_ng, "type": "Gol"},
    {"name": "Segna 1 Gol: Italia", "odd": 1.36, "prob": 0.775, "type": "Gol"},
    {"name": "QUOTA MAGGIORATA: Scamacca & Akturkoglu >= 3 Tiri Porta Ultra", "odd": 2.50, "prob": p_boost_sot, "type": "Speciali"},
    {"name": "Scamacca G. Marcatore Piu", "odd": 1.80, "prob": 0.535, "type": "Marcatori"},
    {"name": "Esposito P. Marcatore Piu", "odd": 2.00, "prob": 0.485, "type": "Marcatori"},
    {"name": "Scamacca G. Segna o Fa Assist", "odd": 1.75, "prob": 0.570, "type": "Marcatori"},
    {"name": "Esposito P. Segna o Fa Assist", "odd": 1.80, "prob": 0.540, "type": "Marcatori"},
    {"name": "Scamacca Marcatore + 1X2 Italia (1)", "odd": 2.30, "prob": 0.423 * 0.90, "type": "Combo"},
    {"name": "Esposito Marcatore + 1X2 Italia (1)", "odd": 2.55, "prob": 0.381 * 0.90, "type": "Combo"},
    {"name": "Uno o Altro Cartellino: Celik Zeki o Kabak Ozan", "odd": 2.00, "prob": p_card_celik_kabak, "type": "Cartellini"},
    {"name": "Uno o Altro Cartellino: Bastoni A. o Calafiori R.", "odd": 2.50, "prob": p_card_bastoni_calafiori, "type": "Cartellini"},
    {"name": "Falli Commessi: Celik Zeki Over 1.5", "odd": 2.00, "prob": p_celik_foul15, "type": "Falli"},
    {"name": "Falli Commessi: Bastoni A. Over 1.5", "odd": 1.65, "prob": p_bastoni_foul15, "type": "Falli"},
    {"name": "Falli Commessi: Calafiori R. Over 1.5", "odd": 1.80, "prob": p_calafiori_foul15, "type": "Falli"},
    {"name": "Falli Commessi: Barella N. Over 1.5", "odd": 1.47, "prob": p_barella_foul15, "type": "Falli"},
]

for m in markets:
    p = m["prob"]
    odd = m["odd"]
    fair = 1.0 / p
    ev = (p * odd - 1.0) * 100.0
    m["fair"] = fair
    m["ev"] = ev

# Sort by EV descending
sorted_markets = sorted(markets, key=lambda x: x["ev"], reverse=True)

print(f"{'TIPO':<12} | {'MERCATO REALE SNAI':<55} | {'PROB':<6} | {'SNAI':<5} | {'FAIR':<5} | {'EDGE EV'}")
print("-" * 100)
for m in sorted_markets:
    sign = "+" if m["ev"] > 0 else ""
    print(f"{m['type']:<12} | {m['name']:<55} | {m['prob']*100:>5.1f}% | {m['odd']:>5.2f} | {m['fair']:>5.2f} | {sign}{m['ev']:>5.1f}%")

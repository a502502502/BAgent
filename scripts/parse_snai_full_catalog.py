import json
import math
import numpy as np

# Match: Italia vs Turchia (SNAI Live Data)
# xG stimati: Italia 1.88, Turchia 0.72

# Matrice Poisson per Italia vs Turchia
xg_h = 1.88
xg_a = 0.72
max_g = 7

matrix = np.zeros((max_g, max_g))
for h in range(max_g):
    for a in range(max_g):
        p_h = (math.exp(-xg_h) * (xg_h ** h)) / math.factorial(h)
        p_a = (math.exp(-xg_a) * (xg_a ** a)) / math.factorial(a)
        matrix[h, a] = p_h * p_a

# Normalizzazione
matrix /= matrix.sum()

def get_stats(prob, snai_odds):
    fair = round(1.0 / prob, 2) if prob > 0 else 99.0
    edge = round((snai_odds * prob - 1.0) * 100.0, 1)
    if edge >= 5.0:
        verdict = "💎 SUPER VALUE (+EV)"
    elif edge >= 1.0:
        verdict = "✅ VALUE BET (+EV)"
    elif edge >= -3.0:
        verdict = "⚖️ EQUILIBRATA"
    else:
        verdict = "⚠️ TRAPPOLA DEL BANCO"
    return {
        "prob_pct": round(prob * 100.0, 1),
        "fair_odds": fair,
        "snai_odds": snai_odds,
        "edge_pct": edge,
        "verdict": verdict
    }

parsed_catalog = {}

# 1. ESITO FINALE 1X2 & DOPPIA CHANCE
p_1 = float(sum(matrix[h, a] for h in range(max_g) for a in range(max_g) if h > a))
p_x = float(sum(matrix[h, a] for h in range(max_g) for a in range(max_g) if h == a))
p_2 = float(sum(matrix[h, a] for h in range(max_g) for a in range(max_g) if h < a))
p_1x = p_1 + p_x
p_x2 = p_x + p_2
p_12 = p_1 + p_2

parsed_catalog["1X2 e Doppia Chance"] = [
    {"mercato": "Esito Finale", "selezione": "1 (Italia)", **get_stats(p_1, 1.40)},
    {"mercato": "Esito Finale", "selezione": "X (Pareggio)", **get_stats(p_x, 5.00)},
    {"mercato": "Esito Finale", "selezione": "2 (Turchia)", **get_stats(p_2, 7.50)},
    {"mercato": "Doppia Chance", "selezione": "1X", **get_stats(p_1x, 1.08)},
    {"mercato": "Doppia Chance", "selezione": "X2", **get_stats(p_x2, 3.00)},
    {"mercato": "Doppia Chance", "selezione": "12", **get_stats(p_12, 1.17)},
    {"mercato": "Draw No Bet", "selezione": "1 (Italia DNB)", **get_stats(p_1 / (p_1 + p_2), 1.13)},
    {"mercato": "Draw No Bet", "selezione": "2 (Turchia DNB)", **get_stats(p_2 / (p_1 + p_2), 6.00)},
]

# 2. UNDER / OVER TOTALI DA 0.5 A 5.5
uo_snai = {
    0.5: (12.00, 1.01),
    1.5: (4.50, 1.15),
    2.5: (2.40, 1.52),
    3.5: (1.57, 2.20),
    4.5: (1.20, 3.75),
    5.5: (1.06, 7.00),
}
uo_list = []
for line, (u_odd, o_odd) in uo_snai.items():
    p_u = float(sum(matrix[h, a] for h in range(max_g) for a in range(max_g) if (h + a) <= line))
    p_o = 1.0 - p_u
    uo_list.append({"mercato": f"Under/Over {line}", "selezione": f"Under {line}", **get_stats(p_u, u_odd)})
    uo_list.append({"mercato": f"Under/Over {line}", "selezione": f"Over {line}", **get_stats(p_o, o_odd)})

p_gg = float(sum(matrix[h, a] for h in range(1, max_g) for a in range(1, max_g)))
p_ng = 1.0 - p_gg
uo_list.append({"mercato": "Goal/NoGoal", "selezione": "Goal (Entrambe segnano)", **get_stats(p_gg, 1.75)})
uo_list.append({"mercato": "Goal/NoGoal", "selezione": "NoGoal", **get_stats(p_ng, 1.95)})
parsed_catalog["Under / Over e Goal/NoGoal"] = uo_list

# 3. 1° TEMPO MERCATI
# xG 1°T: ~45% del match
xg_h_1t = xg_h * 0.45
xg_a_1t = xg_a * 0.45
m_1t = np.zeros((4, 4))
for h in range(4):
    for a in range(4):
        m_1t[h, a] = ((math.exp(-xg_h_1t) * (xg_h_1t**h)) / math.factorial(h)) * ((math.exp(-xg_a_1t) * (xg_a_1t**a)) / math.factorial(a))
m_1t /= m_1t.sum()

p_1_1t = float(sum(m_1t[h, a] for h in range(4) for a in range(4) if h > a))
p_x_1t = float(sum(m_1t[h, a] for h in range(4) for a in range(4) if h == a))
p_2_1t = float(sum(m_1t[h, a] for h in range(4) for a in range(4) if h < a))
p_u05_1t = float(m_1t[0, 0])
p_o05_1t = 1.0 - p_u05_1t
p_u15_1t = float(sum(m_1t[h, a] for h in range(4) for a in range(4) if (h + a) <= 1))
p_o15_1t = 1.0 - p_u15_1t
p_gg_1t = float(sum(m_1t[h, a] for h in range(1, 4) for a in range(1, 4)))
p_ng_1t = 1.0 - p_gg_1t

parsed_catalog["1° Tempo Speciali"] = [
    {"mercato": "1X2 1°T", "selezione": "1 1° Tempo", **get_stats(p_1_1t, 1.80)},
    {"mercato": "1X2 1°T", "selezione": "X 1° Tempo", **get_stats(p_x_1t, 2.70)},
    {"mercato": "1X2 1°T", "selezione": "2 1° Tempo", **get_stats(p_2_1t, 6.50)},
    {"mercato": "DC 1°T", "selezione": "1X 1° Tempo", **get_stats(p_1_1t + p_x_1t, 1.06)},
    {"mercato": "DC 1°T", "selezione": "X2 1° Tempo", **get_stats(p_x_1t + p_2_1t, 1.87)},
    {"mercato": "Under/Over 0.5 1°T", "selezione": "Under 0.5 1°T", **get_stats(p_u05_1t, 3.60)},
    {"mercato": "Under/Over 0.5 1°T", "selezione": "Over 0.5 1°T", **get_stats(p_o05_1t, 1.22)},
    {"mercato": "Under/Over 1.5 1°T", "selezione": "Under 1.5 1°T", **get_stats(p_u15_1t, 1.60)},
    {"mercato": "Under/Over 1.5 1°T", "selezione": "Over 1.5 1°T", **get_stats(p_o15_1t, 2.20)},
    {"mercato": "GG/NG 1°T", "selezione": "GG 1° Tempo", **get_stats(p_gg_1t, 3.75)},
    {"mercato": "GG/NG 1°T", "selezione": "NG 1° Tempo", **get_stats(p_ng_1t, 1.20)},
]

# 4. SQUADRA CASA / OSPITE
p_segna_h = 1.0 - math.exp(-xg_h)
p_segna_a = 1.0 - math.exp(-xg_a)
p_casa_clean_sheet = math.exp(-xg_a) # Italia vince a 0 se Turchia fa 0 e Italia vince
p_casa_win_zero = float(sum(matrix[h, 0] for h in range(1, max_g)))
p_ospite_win_zero = float(sum(matrix[0, a] for a in range(1, max_g)))

parsed_catalog["Speciali Squadra"] = [
    {"mercato": "Segna Goal Casa", "selezione": "Italia Segna Sì", **get_stats(p_segna_h, 1.03)},
    {"mercato": "Segna Goal Casa", "selezione": "Italia Segna No", **get_stats(1.0 - p_segna_h, 8.50)},
    {"mercato": "Segna Goal Ospite", "selezione": "Turchia Segna Sì", **get_stats(p_segna_a, 1.57)},
    {"mercato": "Segna Goal Ospite", "selezione": "Turchia Segna No", **get_stats(1.0 - p_segna_a, 2.20)},
    {"mercato": "Casa Vincente a 0", "selezione": "Italia Vince a 0 Sì", **get_stats(p_casa_win_zero, 2.45)},
    {"mercato": "Casa Vincente a 0", "selezione": "Italia Vince a 0 No", **get_stats(1.0 - p_casa_win_zero, 1.45)},
    {"mercato": "Ospite Vincente a 0", "selezione": "Turchia Vince a 0 Sì", **get_stats(p_ospite_win_zero, 13.00)},
    {"mercato": "Segna 1° Goal", "selezione": "Team 1 (Italia)", **get_stats(xg_h / (xg_h + xg_a), 1.36)},
    {"mercato": "Segna 1° Goal", "selezione": "Team 2 (Turchia)", **get_stats(xg_a / (xg_h + xg_a), 3.60)},
    {"mercato": "Segna 1° Goal", "selezione": "Nessuno (0-0)", **get_stats(matrix[0, 0], 19.00)},
]

# 5. PLAYER PROPS & PRESTAZIONI GIOCATORI (SNAI)
# Modelli di probabilità Poisson / Binomiale su tiri e gol dei giocatori
players_snai = [
    # Nome, xG_p90, Shots_p90, Sot_p90, Foul_p90, Card_prob, Marc_odd, Cart_odd, Ast_odd, Sot_line, Sot_odd, Stot_line, Stot_odd
    ("Scamacca G.", 0.58, 3.4, 1.5, 1.8, 0.12, 2.00, 9.00, 4.50, 1.5, 2.00, 3.5, 1.57),
    ("Esposito P.", 0.52, 3.1, 1.4, 1.6, 0.14, 2.25, 7.50, 4.00, 1.5, 1.80, 3.5, 1.47),
    ("Esposito Se.", 0.50, 3.0, 1.3, 1.5, 0.18, 2.25, 6.00, 2.75, 1.5, 2.25, 3.5, 1.80),
    ("Maldini D.", 0.35, 2.5, 1.1, 1.4, 0.14, 3.25, 7.50, 3.75, 1.5, 2.00, 3.5, 1.80),
    ("Frattesi D.", 0.28, 2.1, 0.9, 1.7, 0.18, 4.00, 6.00, 3.75, 1.5, 3.25, 3.5, 2.50),
    ("Barella N.", 0.22, 1.8, 0.6, 2.1, 0.24, 4.50, 4.50, 3.75, 1.5, 6.00, 2.5, 2.25),
    ("Tonali S.", 0.20, 1.7, 0.6, 2.0, 0.22, 4.50, 5.00, 4.00, 1.5, 4.50, 2.5, 2.75),
    ("Mancini G.", 0.12, 1.1, 0.4, 2.6, 0.28, 9.00, 4.00, 5.00, 1.5, 12.00, 2.5, 4.50),
    ("Bastoni A.", 0.08, 0.9, 0.3, 1.8, 0.24, 16.00, 4.50, 4.50, 1.5, 16.00, 2.5, 9.00),
    ("Calafiori R.", 0.10, 1.0, 0.4, 1.9, 0.24, 12.00, 4.50, 5.00, 1.5, 16.00, 2.5, 5.00),
    ("Di Lorenzo G.", 0.12, 1.2, 0.4, 1.7, 0.21, 9.00, 5.00, 4.50, 0.5, 4.00, 2.5, 5.00),
    # Turchia
    ("Kerem Akturkoglu", 0.25, 2.2, 0.9, 1.5, 0.18, 5.00, 6.00, 7.50, 1.5, 4.50, 2.5, 1.80),
    ("Akgun Y.", 0.20, 1.8, 0.7, 1.4, 0.21, 6.00, 5.00, 7.50, 1.5, 6.00, 2.5, 2.40),
    ("Gul D.", 0.22, 1.9, 0.8, 1.6, 0.24, 5.00, 4.50, 9.00, 1.5, 5.00, 2.5, 2.25),
    ("Uzun C.", 0.20, 1.7, 0.7, 1.5, 0.30, 6.00, 3.50, 6.00, 1.5, 4.50, 2.5, 2.00),
    ("Demiral M.", 0.05, 0.6, 0.2, 2.5, 0.27, 25.00, 4.00, 25.00, 0.5, 6.00, 1.5, 6.00),
    ("Kabak Ozan", 0.05, 0.6, 0.2, 2.7, 0.32, 25.00, 3.25, 16.00, 0.5, 5.00, 1.5, 4.50),
    ("Celik Zeki", 0.04, 0.5, 0.2, 2.6, 0.30, 25.00, 3.50, 9.00, 0.5, 7.50, 1.5, 7.50),
    ("Yuksek I.", 0.05, 0.8, 0.3, 3.0, 0.33, 25.00, 3.25, 9.00, 1.5, 16.00, 2.5, 5.00),
]

props_list = []
for name, xg, shots, sot, fouls, card_p, m_odd, c_odd, a_odd, sot_l, sot_o, stot_l, stot_o in players_snai:
    # Probabilità Marcatore (1 - e^-xg)
    p_marc = 1.0 - math.exp(-xg)
    props_list.append({"mercato": "Marcatore", "selezione": f"{name} Marcatore Sì", **get_stats(p_marc, m_odd)})
    # Cartellino
    props_list.append({"mercato": "Cartellino", "selezione": f"{name} Riceve Cartellino", **get_stats(card_p, c_odd)})
    # Tiri in Porta (Poisson)
    p_sot = 1.0 - sum((math.exp(-sot) * (sot**k)) / math.factorial(k) for k in range(int(sot_l) + 1))
    props_list.append({"mercato": f"Tiri in Porta Over {sot_l}", "selezione": f"{name} Over {sot_l} Tiri in Porta", **get_stats(p_sot, sot_o)})
    # Tiri Totali (Poisson)
    p_stot = 1.0 - sum((math.exp(-shots) * (shots**k)) / math.factorial(k) for k in range(int(stot_l) + 1))
    props_list.append({"mercato": f"Tiri Totali Over {stot_l}", "selezione": f"{name} Over {stot_l} Tiri Totali", **get_stats(p_stot, stot_o)})

parsed_catalog["Player Props & Prestazioni"] = props_list

# 6. COMBO CHANCE & SPECIALI SNAI
combo_list = [
    {"mercato": "Combo Chance", "selezione": "1 o Under 2.5", **get_stats(0.897, 1.35)},
    {"mercato": "Combo Chance", "selezione": "1X o Gol", **get_stats(0.926, 1.20)},
    {"mercato": "Combo 1X2 + U/O", "selezione": "1 + Under 3.5", **get_stats(0.444, 2.15)},
    {"mercato": "Combo 1X2 + U/O", "selezione": "1 + Over 1.5", **get_stats(0.508, 1.68)},
    {"mercato": "Combo DC + U/O", "selezione": "1X + Under 3.5", **get_stats(0.630, 1.55)},
    {"mercato": "Combo DC + U/O", "selezione": "1X + Under 4.5", **get_stats(0.762, 1.30)},
    {"mercato": "Combo DC + U/O", "selezione": "1X + Over 1.5", **get_stats(0.654, 1.38)},
    {"mercato": "Marcatore + 1X2", "selezione": "Scamacca Marcatore + 1", **get_stats(0.385, 2.30)},
    {"mercato": "Marcatore + 1X2", "selezione": "Esposito P. Marcatore + 1", **get_stats(0.352, 2.55)},
    {"mercato": "Marcatore + 1X2", "selezione": "Frattesi Marcatore + 1", **get_stats(0.205, 4.40)},
    {"mercato": "Multigol Squadra", "selezione": "Multigol Italia 1-3", **get_stats(0.808, 1.28)},
    {"mercato": "Corner Match", "selezione": "Over 8.5 Corner Match", **get_stats(0.640, 1.60)},
    {"mercato": "Cartellini Match", "selezione": "Over 3.5 Cartellini Match", **get_stats(0.680, 1.65)},
    {"mercato": "Arbitro Monitor VAR", "selezione": "Arbitro Consulta Monitor VAR Sì", **get_stats(0.280, 3.20)},
    {"mercato": "Rigore Match", "selezione": "Rigore Assegnato Sì", **get_stats(0.320, 2.75)},
]
parsed_catalog["Combo, MultiGol e Speciali Match"] = combo_list

with open("reports/snai_italia_turchia_full_catalog.json", "w", encoding="utf-8") as f:
    json.dump(parsed_catalog, f, indent=2)

print("Catalog built successfully! Categories:", list(parsed_catalog.keys()))
for cat, items in parsed_catalog.items():
    print(f"  {cat}: {len(items)} mercati")

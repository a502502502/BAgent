import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

# Probabilità di cartellino per giocatore (basate su storico falli p90, cartellini per 90 min, e arbitro internazionale)
# Barella: 24%
# Bastoni: 24%
# Calafiori: 24%
# Celik Zeki: 30%
# Kabak Ozan: 32%

p_cards = {
    "BARELLA N.": 0.24,
    "BASTONI A.": 0.24,
    "CALAFIORI R.": 0.24,
    "CELIK ZEKI": 0.30,
    "KABAK OZAN": 0.32,
}

# Quota SNAI per "UNO O L'ALTRO: CARTELLINO ULTRA"
duos_cards = [
    ("BARELLA N.", "BASTONI A.", 2.65),
    ("BARELLA N.", "CALAFIORI R.", 2.65),
    ("BARELLA N.", "CELIK ZEKI", 2.30),
    ("BARELLA N.", "KABAK OZAN", 2.25),
    ("BASTONI A.", "CALAFIORI R.", 2.50),
    ("BASTONI A.", "CELIK ZEKI", 2.25),
    ("BASTONI A.", "KABAK OZAN", 2.10),
    ("CALAFIORI R.", "CELIK ZEKI", 2.25),
    ("CALAFIORI R.", "KABAK OZAN", 2.10),
    ("CELIK ZEKI", "KABAK OZAN", 2.00),
]

print("=== VALUTAZIONE QUANTITATIVA: UNO O L'ALTRO CARTELLINO ===")
results_cards = []

for p1, p2, odd in duos_cards:
    p_a = p_cards[p1]
    p_b = p_cards[p2]
    # P(A o B) = 1 - (1 - P(A)) * (1 - P(B))
    p_union = 1.0 - (1.0 - p_a) * (1.0 - p_b)
    fair_odd = round(1.0 / p_union, 2)
    edge_pct = round((odd * p_union - 1.0) * 100.0, 1)
    ev_status = "💎 SUPER VALUE (+EV)" if edge_pct >= 5.0 else ("✅ VALUE (+EV)" if edge_pct > 0 else "⚠️ TRAPPOLA DEL BANCO")
    
    res = {
        "coppia": f"{p1} o {p2}",
        "p_union_pct": round(p_union * 100.0, 1),
        "fair_odd": fair_odd,
        "snai_odd": odd,
        "edge_pct": edge_pct,
        "status": ev_status
    }
    results_cards.append(res)
    print(f"{res['coppia']:<32} | P(Almeno 1): {res['p_union_pct']:>5}% | Fair: @{fair_odd:<4} | SNAI: @{odd:<4} | Edge: {edge_pct:>6}% | {ev_status}")

# Primo Marcatore "Uno o l'Altro"
# P(Esposito P. 1° Marc) ~ 1/6.00 = 16.7% fair ~ 14.5%
# P(Esposito Se. 1° Marc) ~ 1/7.50 = 13.3% fair ~ 11.5%
# P(Kerem Akturkoglu 1° Marc) ~ 1/12.00 ~ 8.5%
# Per il primo marcatore, gli eventi sono MUTUAMENTE ESCLUSIVI (non possono essere entrambi il 1° marcatore!)
# P(A o B 1° marcatore) = P(A) + P(B)!

print("\n=== VALUTAZIONE QUANTITATIVA: UNO O L'ALTRO PRIMO MARCATORE ===")
p_first_scorer = {
    "ESPOSITO P.": 0.145,
    "ESPOSITO SE.": 0.115,
    "KEREM AKTURKOGLU M.": 0.080,
    "SCAMACCA G.": 0.165,
    "YILMAZ BARIS": 0.075
}

first_scorer_pairs = [
    ("ESPOSITO P.", "ESPOSITO SE.", 2.75),
    ("KEREM AKTURKOGLU M.", "ESPOSITO P.", 3.75),
    ("KEREM AKTURKOGLU M.", "ESPOSITO SE.", 3.75),
]

for p1, p2, odd in first_scorer_pairs:
    p_a = p_first_scorer[p1]
    p_b = p_first_scorer[p2]
    p_union = p_a + p_b  # mutuamente esclusivi!
    fair_odd = round(1.0 / p_union, 2)
    edge_pct = round((odd * p_union - 1.0) * 100.0, 1)
    ev_status = "💎 SUPER VALUE (+EV)" if edge_pct >= 5.0 else ("✅ VALUE (+EV)" if edge_pct > 0 else "⚠️ TRAPPOLA DEL BANCO")
    print(f"{p1} o {p2:<22} | P: {round(p_union*100, 1):>5}% | Fair: @{fair_odd:<4} | SNAI: @{odd:<4} | Edge: {edge_pct:>6}% | {ev_status}")

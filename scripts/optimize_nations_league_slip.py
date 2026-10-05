import sys
from pathlib import Path

ROOT = Path("C:/Project/BAgent")
sys.path.insert(0, str(ROOT))

from services.analysis.xg_poisson_engine import QuantitativeEngine
from services.analysis.match_market_optimizer import MatchMarketOptimizer

engine = QuantitativeEngine(rho=-0.05)
optimizer = MatchMarketOptimizer()

fixtures = [
    {
        "match": "Italia vs Turchia",
        "home": "Italia", "away": "Turchia",
        "lam_h": 2.05, "lam_a": 0.80,
        "note": "Italia favorita netta ma Turchia a blocco basso. Copertura ideale su vittoria casa o pochi gol."
    },
    {
        "match": "Francia vs Belgio",
        "home": "Francia", "away": "Belgio",
        "lam_h": 1.75, "lam_a": 1.05,
        "note": "Big match di cartello: Francia superiore ma Belgio pericoloso in transizione. Ottima Doppia Chance con paracadute gol."
    },
    {
        "match": "Bosnia Erzegovina vs Polonia",
        "home": "Bosnia Erzegovina", "away": "Polonia",
        "lam_h": 1.15, "lam_a": 1.35,
        "note": "Gara molto equilibrata e fisica a Zenica. Polonia leggermente superiore tecnicamente. Mercato Under/Multigol aperto."
    },
    {
        "match": "Ucraina vs Ungheria",
        "home": "Ucraina", "away": "Ungheria",
        "lam_h": 1.25, "lam_a": 0.95,
        "note": "Gara tattica in campo neutro/est: squadre prudenti, primo tempo di studio, baricentro compatto."
    },
    {
        "match": "Irlanda del Nord vs Georgia",
        "home": "Irlanda Del Nord", "away": "Georgia",
        "lam_h": 1.10, "lam_a": 1.05,
        "note": "Belfast, clima britannico, duelli aerei e ritmi serrati. Pochissimi spazi centrali."
    },
    {
        "match": "Romania vs Svezia",
        "home": "Romania", "away": "Svezia",
        "lam_h": 1.00, "lam_a": 1.65,
        "note": "Svezia con attacco di qualita superiore (Gyokeres/Isak), Romania solida in casa. X2 con filtro gol."
    },
    {
        "match": "Montenegro vs Armenia",
        "home": "Montenegro", "away": "Armenia",
        "lam_h": 1.55, "lam_a": 0.85,
        "note": "Montenegro a Podgorica fa valere il fattore campo contro una Armenia debole in trasferta."
    }
]

candidate_markets = [
    "1X",
    "X2",
    "1X + Under 3.5",
    "1X + Under 4.5",
    "X2 + Under 3.5",
    "X2 + Under 4.5",
    "1X + Over 1.5",
    "X2 + Over 1.5",
    "Under 3.5",
    "Over 1.5",
    "MultiGol 1-4",
    "MultiGol 2-5",
    "MultiGol 1-3",
    "Gol in entrambi i tempi",
    "Casa Segna 1-3 Gol",
    "Ospite Segna 1-3 Gol"
]

print("================================================================================")
print("ANALISI QUANTITATIVA COMBINAZIONI RESILIENTI NATIONS LEAGUE (05/10/2026)")
print("================================================================================\n")

results = []

for f in fixtures:
    h, a = f["home"], f["away"]
    lh, la = f["lam_h"], f["lam_a"]
    match_name = f["match"]
    
    print(f"MATCH: {match_name} (xG: {h} {lh:.2f} - {a} {la:.2f})")
    
    # Valuta tutti i mercati candidati
    scored_markets = []
    for m in candidate_markets:
        prob = engine.goal_market_probability(lh, la, m)
        if prob is not None and prob >= 0.70:
            fair = 1.0 / prob
            scored_markets.append((m, prob, fair))
            
    scored_markets.sort(key=lambda x: x[1], reverse=True)
    
    # Seleziona il mercato migliore per profilo tattico
    best = scored_markets[0]
    print(f"  -> Miglior Mercato Selezionato: {best[0]} | Probabilita: {best[1]*100:.1f}% | Quota Equa: {best[2]:.2f}")
    for sm in scored_markets[1:5]:
        print(f"     Alt: {sm[0]:<25} P: {sm[1]*100:>5.1f}% (Fair: {sm[2]:.2f})")
    print()
    results.append({
        "match": match_name,
        "best_market": best[0],
        "prob": best[1],
        "fair": best[2],
        "note": f["note"],
        "all_top": scored_markets[:4]
    })

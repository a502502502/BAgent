import sys
import os
import math

sys.path.insert(0, r"C:\Users\demarj\.gemini\antigravity\scratch\BAgent")
from services.analysis.multigol_bracket_analyzer import MultigolBracketAnalyzer

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def calc_joint(xg_h: float, xg_a: float, max_g: int = 8):
    h = [_poisson_pmf(k, xg_h) for k in range(max_g + 1)]
    a = [_poisson_pmf(k, xg_a) for k in range(max_g + 1)]
    return [[h[i] * a[j] for j in range(max_g + 1)] for i in range(max_g + 1)]

EARLY_SLATE = [
    {
        "time": "14:30",
        "league": "Ucraina: Premier League",
        "home": "Dynamo Kyiv",
        "away": "Epitsentr",
        "xg_h": 2.45,
        "xg_a": 0.55,
        "note": "Dynamo nettamente dominante, differenza tecnica abissale."
    },
    {
        "time": "17:00",
        "league": "Ucraina: Premier League",
        "home": "Shakhtar Donetsk",
        "away": "Ch. Odesa",
        "xg_h": 2.50,
        "xg_a": 0.60,
        "note": "Shakhtar macchina da gol, Chornomorets arroccato."
    },
    {
        "time": "17:00",
        "league": "Romania: Superliga",
        "home": "U. Cluj",
        "away": "Otelul Galati",
        "xg_h": 1.45,
        "xg_a": 0.85,
        "note": "U. Cluj capolista imbattuta in casa; Otelul squadra rognosa da Under."
    },
    {
        "time": "17:00",
        "league": "Finlandia: Veikkausliiga (Championship)",
        "home": "Inter Turku",
        "away": "VPS",
        "xg_h": 1.70,
        "xg_a": 1.25,
        "note": "Playoff scudetto finlandese, campo veloce, xG tot 2.95."
    },
    {
        "time": "18:00",
        "league": "Asia: AFC Champions League",
        "home": "Al Shamal",
        "away": "Al Ittihad",
        "xg_h": 0.90,
        "xg_a": 2.20,
        "note": "Al Ittihad con le stelle d'Arabia (Benzema/Fabinho) contro i qatarioti."
    },
    {
        "time": "18:00",
        "league": "Croazia: HNL",
        "home": "Gorica",
        "away": "Varazdin",
        "xg_h": 1.20,
        "xg_a": 1.15,
        "note": "Campionato croato: gara equilibrata, pochi spazi concessi."
    }
]

analyzer = MultigolBracketAnalyzer()
print("=== ANALISI QUANTITATIVA MATCH POMERIDIANI (14:30 - 18:00) ===")
for m in EARLY_SLATE:
    tot = m["xg_h"] + m["xg_a"]
    j = calc_joint(m["xg_h"], m["xg_a"])
    
    p_1 = sum(j[i][k] for i in range(9) for k in range(9) if i > k)
    p_1x = sum(j[i][k] for i in range(9) for k in range(9) if i >= k)
    p_x2 = sum(j[i][k] for i in range(9) for k in range(9) if i <= k)
    p_o15 = sum(j[i][k] for i in range(9) for k in range(9) if i + k > 1)
    p_u35 = sum(j[i][k] for i in range(9) for k in range(9) if i + k < 4)
    p_1_o15 = sum(j[i][k] for i in range(9) for k in range(9) if i > k and i + k > 1)
    p_2_o15 = sum(j[i][k] for i in range(9) for k in range(9) if i < k and i + k > 1)
    p_x2_o15 = sum(j[i][k] for i in range(9) for k in range(9) if i <= k and i + k > 1)
    p_1x_u35 = sum(j[i][k] for i in range(9) for k in range(9) if i >= k and i + k < 4)
    p_1x_mg14 = sum(j[i][k] for i in range(9) for k in range(9) if i >= k and 1 <= i + k <= 4)
    
    brk = analyzer.analyze_match_brackets(m["home"], m["away"], tot)
    
    print(f"\n⚽ [{m['time']}] {m['home']} vs {m['away']} ({m['league']})")
    print(f"   xG: {m['xg_h']} - {m['xg_a']} (Tot: {tot:.2f}) | P(O1.5): {p_o15*100:.1f}% | P(U3.5): {p_u35*100:.1f}%")
    print(f"   🎯 Bracket Multigol: 1°T (0-2) & 2°T (1-3) ➔ {brk['recommendations'][0]['estimated_prob']}% | MG 1-4 ➔ {brk['prob_mg_1_4']}%")
    
    # Best pick
    if "Dynamo" in m["home"] or "Shakhtar" in m["home"]:
        print(f"   👉 Consigliato: 1 + Over 1.5 Gol ➔ Prob: {p_1_o15*100:.1f}% (Fair Odd: {1/p_1_o15:.2f})")
        print(f"   👉 Alternativa Blindata: 1X + MultiGol 1-4 ➔ Prob: {p_1x_mg14*100:.1f}% (Fair Odd: {1/p_1x_mg14:.2f})")
    elif "U. Cluj" in m["home"]:
        print(f"   👉 Consigliato: 1X + Under 3.5 Gol ➔ Prob: {p_1x_u35*100:.1f}% (Fair Odd: {1/p_1x_u35:.2f})")
        print(f"   👉 Alternativa Blindata: MultiGol Match 1-4 ➔ Prob: {brk['prob_mg_1_4']}% (Fair Odd: {100/brk['prob_mg_1_4']:.2f})")
    elif "Ittihad" in m["away"]:
        print(f"   👉 Consigliato: X2 + Over 1.5 Gol ➔ Prob: {p_x2_o15*100:.1f}% (Fair Odd: {1/p_x2_o15:.2f})")
        print(f"   👉 Alternativa: 2 + Over 1.5 Gol ➔ Prob: {p_2_o15*100:.1f}% (Fair Odd: {1/p_2_o15:.2f})")
    elif "Inter Turku" in m["home"]:
        print(f"   👉 Consigliato: 1X + Over 1.5 Gol ➔ Prob: {sum(j[i][k] for i in range(9) for k in range(9) if i >= k and i+k > 1)*100:.1f}%")
        print(f"   👉 Bracket: 1°T (0-2) & 2°T (1-3) ➔ Prob: {brk['recommendations'][0]['estimated_prob']}%")
    elif "Gorica" in m["home"]:
        print(f"   👉 Consigliato: Under 3.5 Gol ➔ Prob: {p_u35*100:.1f}% (Fair Odd: {1/p_u35:.2f})")

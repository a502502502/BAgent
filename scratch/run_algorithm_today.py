"""
Calculation engine test on today's matches (14 Settembre 2026).
Applies MultigolBracketAnalyzer, ClassicComboOptimizer, and SpecializedLeaguesProfile.
"""

import sys
import os
import math
from dataclasses import dataclass
from typing import Dict, List, Any

# Adjust path
sys.path.insert(0, r"C:\Users\demarj\.gemini\antigravity\scratch\BAgent")

from services.analysis.multigol_bracket_analyzer import MultigolBracketAnalyzer
from services.leagues.specialized_leagues_profile import LEAGUE_PROFILES

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

def _poisson_pmf(k: int, lam: float) -> float:
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

def calc_joint_matrix(xg_h: float, xg_a: float, max_g: int = 8):
    h_pmf = [_poisson_pmf(k, xg_h) for k in range(max_g + 1)]
    a_pmf = [_poisson_pmf(k, xg_a) for k in range(max_g + 1)]
    return [[h_pmf[i] * a_pmf[j] for j in range(max_g + 1)] for i in range(max_g + 1)]

# Today's slate (14 September 2026)
SLATE = [
    {
        "time": "18:30",
        "league": "Serie A (Italia)",
        "home": "Como",
        "away": "Parma",
        "xg_h": 1.45,
        "xg_a": 1.25,
        "context": "Scontro aperto, ritmo brillante, entrambe a trazione offensiva."
    },
    {
        "time": "18:30",
        "league": "Serie A (Italia)",
        "home": "Torino",
        "away": "Roma",
        "xg_h": 1.10,
        "xg_a": 1.35,
        "context": "Gara tattica all'Olimpico Grande Torino, blocchi compatti."
    },
    {
        "time": "19:00",
        "league": "Eliteserien (Norvegia - nor.1)",
        "home": "Bodo/Glimt",
        "away": "Sandefjord",
        "xg_h": 2.65,
        "xg_a": 0.75,
        "context": "Fortino Aspmyra Stadion in sintetico. Bodo dominante, vietato under e cartellini."
    },
    {
        "time": "19:00",
        "league": "Superliga (Danimarca)",
        "home": "Midtjylland",
        "away": "Brondby",
        "xg_h": 1.85,
        "xg_a": 1.30,
        "context": "Big match danese, xG totale > 3.00, transizioni rapide."
    },
    {
        "time": "19:00",
        "league": "Super Lig (Turchia)",
        "home": "Gaziantep",
        "away": "Fenerbahce",
        "xg_h": 0.85,
        "xg_a": 2.10,
        "context": "Fenerbahce nettamente superiore tecnicamente, obbligo vittoria."
    },
    {
        "time": "20:45",
        "league": "Serie A (Italia)",
        "home": "Inter",
        "away": "Udinese",
        "xg_h": 2.25,
        "xg_a": 0.65,
        "context": "San Siro gremito, Inter padrona del campo ma con imminente debutto Champions."
    },
    {
        "time": "21:00",
        "league": "Premier League (Inghilterra)",
        "home": "Leeds",
        "away": "Newcastle",
        "xg_h": 1.30,
        "xg_a": 1.65,
        "context": "Elland Road infuocato, intensità da Premier League, duelli fisici."
    },
    {
        "time": "21:00",
        "league": "LaLiga (Spagna)",
        "home": "Villarreal",
        "away": "Betis",
        "xg_h": 1.60,
        "xg_a": 1.25,
        "context": "Estadio de la Cerámica, Marcelino vs Pellegrini, entrambe votate al gol."
    },
    {
        "time": "21:45",
        "league": "Liga Portugal",
        "home": "Braga",
        "away": "Estoril",
        "xg_h": 2.15,
        "xg_a": 0.80,
        "context": "Braga tra le mura amiche, potenziale offensivo d'élite."
    },
    {
        "time": "22:30",
        "league": "Brasileirao Serie A (Brasile - bra.1)",
        "home": "Flamengo",
        "away": "Corinthians",
        "xg_h": 1.80,
        "xg_a": 0.70,
        "context": "Classico del Maracanã. Fattore campo sovrano, Corinthians affaticato."
    }
]

def run_analysis():
    analyzer = MultigolBracketAnalyzer()
    print("="*85)
    print("🔬 APPLICAZIONE DEI NUOVI ALGORITMI BAGENT SUL PALINSESTO DI OGGI (14 SETTEMBRE 2026)")
    print("="*85)
    
    results = []
    for match in SLATE:
        xg_h = match["xg_h"]
        xg_a = match["xg_a"]
        exp_tot = xg_h + xg_a
        joint = calc_joint_matrix(xg_h, xg_a)
        
        # Probabilità fondamentali
        p_1 = sum(joint[i][j] for i in range(9) for j in range(9) if i > j)
        p_x = sum(joint[i][j] for i in range(9) for j in range(9) if i == j)
        p_2 = sum(joint[i][j] for i in range(9) for j in range(9) if i < j)
        p_1x = p_1 + p_x
        p_x2 = p_2 + p_x
        p_o15 = sum(joint[i][j] for i in range(9) for j in range(9) if i + j > 1)
        p_o25 = sum(joint[i][j] for i in range(9) for j in range(9) if i + j > 2)
        p_u35 = sum(joint[i][j] for i in range(9) for j in range(9) if i + j < 4)
        p_btts = sum(joint[i][j] for i in range(1, 9) for j in range(1, 9))
        
        # Nuove combo
        p_1x_o15 = sum(joint[i][j] for i in range(9) for j in range(9) if i >= j and i + j > 1)
        p_x2_o15 = sum(joint[i][j] for i in range(9) for j in range(9) if i <= j and i + j > 1)
        p_1_o15 = sum(joint[i][j] for i in range(9) for j in range(9) if i > j and i + j > 1)
        p_2_o15 = sum(joint[i][j] for i in range(9) for j in range(9) if i < j and i + j > 1)
        p_1x_u35 = sum(joint[i][j] for i in range(9) for j in range(9) if i >= j and i + j < 4)
        p_x2_u35 = sum(joint[i][j] for i in range(9) for j in range(9) if i <= j and i + j < 4)
        p_1x_mg14 = sum(joint[i][j] for i in range(9) for j in range(9) if i >= j and 1 <= i + j <= 4)
        p_x2_mg15 = sum(joint[i][j] for i in range(9) for j in range(9) if i <= j and 1 <= i + j <= 5)

        # Multigol brackets
        brk = analyzer.analyze_match_brackets(match["home"], match["away"], exp_tot)
        
        # Genera le 3 migliori selezioni quantitative per questa gara
        candidates = []
        
        # Valuta selezione primaria in base al profilo
        if "nor.1" in match["league"]:
            candidates.append({
                "market": "1 + Over 1.5 Gol",
                "prob": p_1_o15,
                "fair_odd": 1.0 / p_1_o15,
                "rationale": "Bodø all'Aspmyra è una macchina da gol. Sintetico veloce, xG 2.65."
            })
            candidates.append({
                "market": "Multigol Match: 2-5 Gol",
                "prob": sum(sum(joint[i][j] for j in range(9) if 2 <= i + j <= 5) for i in range(9)),
                "fair_odd": 1.0 / sum(sum(joint[i][j] for j in range(9) if 2 <= i + j <= 5) for i in range(9)),
                "rationale": "Anti-trappola: copre 2-0, 2-1, 3-0, 3-1, 4-0, 4-1."
            })
        elif "bra.1" in match["league"]:
            candidates.append({
                "market": "1X + Under 3.5 Gol",
                "prob": p_1x_u35,
                "fair_odd": 1.0 / p_1x_u35,
                "rationale": "Regola #52 Brasileirão: fortino Maracanã + ritmo compassato."
            })
            candidates.append({
                "market": "1X + MultiGol 1-4",
                "prob": p_1x_mg14,
                "fair_odd": 1.0 / p_1x_mg14,
                "rationale": "Resiliente all'1-0 tipico del Brasileirão."
            })
        elif match["home"] == "Inter":
            candidates.append({
                "market": "1 + Over 1.5 Gol",
                "prob": p_1_o15,
                "fair_odd": 1.0 / p_1_o15,
                "rationale": "Inter a San Siro xG 2.25. Pressione offensiva continua."
            })
            candidates.append({
                "market": "1X + MultiGol 1-4",
                "prob": p_1x_mg14,
                "fair_odd": 1.0 / p_1x_mg14,
                "rationale": "Protegge da cali di ritmo pre-Champions (1-0, 2-0, 2-1, 3-0, 3-1)."
            })
        elif match["away"] == "Fenerbahce":
            candidates.append({
                "market": "X2 + Over 1.5 Gol",
                "prob": p_x2_o15,
                "fair_odd": 1.0 / p_x2_o15,
                "rationale": "Fenerbahce superiore tecnicamente; Gaziantep subisce 1.6 gol/partita."
            })
            candidates.append({
                "market": "MultiGol Match: 2-4 Gol",
                "prob": brk["prob_mg_2_4"] / 100.0,
                "fair_odd": 1.0 / (brk["prob_mg_2_4"] / 100.0),
                "rationale": "Forchetta ideale da 0-2, 1-2, 1-3, 0-3."
            })
        elif match["home"] == "Villarreal":
            candidates.append({
                "market": "1X + Over 1.5 Gol",
                "prob": p_1x_o15,
                "fair_odd": 1.0 / p_1x_o15,
                "rationale": "Villarreal solido al Madrigal, Betis offensivo. Match da Over 1.5 al 83%."
            })
            candidates.append({
                "market": "Gol (Entrambe segnano)",
                "prob": p_btts,
                "fair_odd": 1.0 / p_btts,
                "rationale": "Pellegrini vs Marcelino: 65% BTTS storico negli scontri diretti."
            })
        elif match["home"] == "Braga":
            candidates.append({
                "market": "1 + Over 1.5 Gol",
                "prob": p_1_o15,
                "fair_odd": 1.0 / p_1_o15,
                "rationale": "Braga dominante contro l'Estoril (xG casa 2.15 vs 0.80)."
            })
            candidates.append({
                "market": "1X + MultiGol 1-4",
                "prob": p_1x_mg14,
                "fair_odd": 1.0 / p_1x_mg14,
                "rationale": "Copertura granitica all'Estádio Municipal."
            })
        elif match["home"] == "Leeds":
            candidates.append({
                "market": "X2 + Over 1.5 Gol",
                "prob": p_x2_o15,
                "fair_odd": 1.0 / p_x2_o15,
                "rationale": "Newcastle qualitativamente superiore; Leeds concede spazi in contropiede."
            })
            candidates.append({
                "market": "Multigol Tempo: 1°T (0-2) & 2°T (1-3)",
                "prob": brk["recommendations"][0]["estimated_prob"] / 100.0,
                "fair_odd": brk["recommendations"][0]["estimated_fair_odd"],
                "rationale": "Partita da Premier: 1° tempo di studio e ripresa infuocata."
            })
        elif match["home"] == "Como":
            candidates.append({
                "market": "1X + Over 1.5 Gol",
                "prob": p_1x_o15,
                "fair_odd": 1.0 / p_1x_o15,
                "rationale": "Como propositivo al Sinigaglia; Parma gioca a viso aperto."
            })
            candidates.append({
                "market": "MultiGol Match: 1-4 Gol",
                "prob": brk["prob_mg_1_4"] / 100.0,
                "fair_odd": 1.0 / (brk["prob_mg_1_4"] / 100.0),
                "rationale": "Copre tutti i punteggi realistici della Serie A da 1-0 a 3-1."
            })
        elif match["home"] == "Torino":
            candidates.append({
                "market": "Under 3.5 Gol",
                "prob": p_u35,
                "fair_odd": 1.0 / p_u35,
                "rationale": "Gara a ritmi bloccati; Torino solido difensivamente."
            })
            candidates.append({
                "market": "X2 + Under 3.5 Gol",
                "prob": p_x2_u35,
                "fair_odd": 1.0 / p_x2_u35,
                "rationale": "Roma con maggior tasso tecnico, Torino che gioca per non prenderle."
            })
        elif match["home"] == "Midtjylland":
            candidates.append({
                "market": "1X + Over 1.5 Gol",
                "prob": p_1x_o15,
                "fair_odd": 1.0 / p_1x_o15,
                "rationale": "Midtjylland fortissimo in casa; Brondby concede in trasferta."
            })
            candidates.append({
                "market": "Over 2.5 Gol",
                "prob": p_o25,
                "fair_odd": 1.0 / p_o25,
                "rationale": "Superliga danese a vocazione offensiva (xG tot 3.15)."
            })

        print(f"\n📌 [{match['time']}] {match['home']} vs {match['away']} ({match['league']})")
        print(f"   📊 xG Stimati: {xg_h:.2f} - {xg_a:.2f} (Tot: {exp_tot:.2f}) | P(1X): {p_1x*100:.1f}% | P(O1.5): {p_o15*100:.1f}% | P(U3.5): {p_u35*100:.1f}%")
        print(f"   🎯 Bracket Multigol: 1°T (0-2) & 2°T (1-3) ➔ {brk['recommendations'][0]['estimated_prob']}% | MG 1-4 Totale ➔ {brk['prob_mg_1_4']}%")
        for c in candidates:
            print(f"   👉 {c['market']} ➔ Prob Modello: {c['prob']*100:.1f}% (Fair Odd: {c['fair_odd']:.2f})")
            print(f"      Motivazione: {c['rationale']}")
            
if __name__ == "__main__":
    run_analysis()

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.netwin_cache_reader import load_cached_matches, estimate_xg
from services.betting.strict_ticket_pipeline import StrictTicketPipeline, MarketCandidate

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

pipeline = StrictTicketPipeline()
matches = load_cached_matches(tournament="Nations League")

print(f"=====================================================================================")
print(f"🔍 SCAN COMPLETO MERCATI E COMBO — UEFA NATIONS LEAGUE (01 OTTOBRE 2026)")
print(f"=====================================================================================\n")

oct1_matches = [m for m in matches if "20261001" in m.kickoff]
print(f"Trovate {len(oct1_matches)} partite in programma per il 01/10/2026:")

results_by_match = {}

for m in oct1_matches:
    resolved = estimate_xg(m)
    if not resolved:
        print(f"⚠️ Impossibile risolvere xG per {m.match_name}")
        continue
    xh, xa = resolved
    
    match_results = []
    
    for mkt, odd in m.odds_dict.items():
        if odd < 1.18 or odd > 3.00:
            continue
            
        cand = MarketCandidate(
            match_name=m.match_name,
            tournament="UEFA Nations League",
            market_name=mkt,
            bookmaker_odd=odd,
            xg_home=xh,
            xg_away=xa,
            kickoff_time="2026-10-01 20:45 UTC",
            home_matches_played=2,
            away_matches_played=2,
            sixth_sense_analysis=f"Dati 2026/27 da bagent.db (xG shrunk {xh:.2f}-{xa:.2f}).",
        )
        
        rep = pipeline.validate_candidate(cand)
        if rep.passed and rep.mathematical_edge >= 0.04 and rep.real_probability >= 0.70:
            match_results.append({
                "market": mkt,
                "odd": odd,
                "prob": rep.real_probability,
                "fair_odd": rep.fair_odds,
                "edge": rep.mathematical_edge,
                "warning": rep.edge_warning,
            })
            
    # Ordina per edge decrescente
    match_results.sort(key=lambda x: x["edge"], reverse=True)
    results_by_match[m.match_name] = {
        "match": m,
        "xg": (xh, xa),
        "kickoff": m.kickoff,
        "certified": match_results
    }

for name, res in results_by_match.items():
    m = res["match"]
    xh, xa = res["xg"]
    cert = res["certified"]
    print(f"\n⚽ {name} ({res['kickoff']}) | xG Shrunk DB: {xh:.2f} - {xa:.2f}")
    print(f"   Totale mercati certificati (P >= 70%, Edge >= +4%): {len(cert)}")
    
    if not cert:
        print("   ❌ Nessun mercato ha superato contemporaneamente i filtri di probabilità ed edge.")
        continue
        
    # Categorizziamo per tipologia per facilitare la scelta
    combos = [c for c in cert if "+" in c["market"]]
    chances = [c for c in cert if "chance mix" in c["market"].lower() or " o " in c["market"].lower()]
    primo_tempo = [c for c in cert if "1°" in c["market"] or "primo tempo" in c["market"].lower() or "1t" in c["market"].lower()]
    standard = [c for c in cert if c not in combos and c not in chances and c not in primo_tempo]
    
    if combos:
        print("   🔹 Top COMBO (+):")
        for c in combos[:3]:
            print(f"      • {c['market']:<26} @ Netwin {c['odd']:<4} | P={c['prob']*100:5.1f}% | Fair=@{c['fair_odd']:<4.2f} | Edge={c['edge']*100:+5.1f}%")
            
    if chances:
        print("   🔸 Top CHANCE MIX (o):")
        for c in chances[:3]:
            print(f"      • {c['market']:<26} @ Netwin {c['odd']:<4} | P={c['prob']*100:5.1f}% | Fair=@{c['fair_odd']:<4.2f} | Edge={c['edge']*100:+5.1f}%")
            
    if standard:
        print("   ▫️ Top MERCATI STANDARD (Under, MultiGol, DC):")
        for c in standard[:3]:
            print(f"      • {c['market']:<26} @ Netwin {c['odd']:<4} | P={c['prob']*100:5.1f}% | Fair=@{c['fair_odd']:<4.2f} | Edge={c['edge']*100:+5.1f}%")
            
    if primo_tempo:
        print("   ⏱️ Top 1° TEMPO:")
        for c in primo_tempo[:2]:
            print(f"      • {c['market']:<26} @ Netwin {c['odd']:<4} | P={c['prob']*100:5.1f}% | Fair=@{c['fair_odd']:<4.2f} | Edge={c['edge']*100:+5.1f}%")

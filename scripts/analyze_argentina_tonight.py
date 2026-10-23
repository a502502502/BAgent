import sys
import json
import sqlite3
from datetime import datetime, timezone

sys.stdout.reconfigure(encoding="utf-8")

from services.betting.strict_ticket_pipeline import (
    StrictTicketPipeline,
    MarketCandidate,
    normalize_kickoff,
    _fold_team,
)
from services.football.reality_gate_guardian import RealityGateGuardian

print("=" * 78)
print("🇦🇷 ANALISI APPROFONDITA: LIGA PROFESIONAL ARGENTINA — SERATA 23 OTTOBRE 2026")
print("=" * 78)

conn = sqlite3.connect("data/bagent.db")
c = conn.cursor()

# 1. Recupero contesto storico del torneo
c.execute("""
    SELECT match_date, home_team, away_team, home_goals, away_goals 
    FROM matches 
    WHERE league = 'Argentina' 
    ORDER BY match_date DESC 
    LIMIT 10
""")
recent_matches = c.fetchall()
print(f"\n📊 ULTIMI MATCH REGISTRATI NEL DATABASE (LIGA PROFESIONAL):")
for rm in recent_matches:
    print(f"  • {rm[0]}: {rm[1]} {rm[3]}-{rm[4]} {rm[2]}")

# 2. Carica quote Netwin
raw_odds = json.load(open("data/netwin_live_odds.json", encoding="utf-8"))
matches = raw_odds.get("matches", [])
arg_matches = [m for m in matches if "아르헨티나" in m.get("tournament", "") or "argentin" in m.get("tournament", "").lower()]

print(f"\n🏟️ PARTITE DI STASERA SU NETWIN ({len(arg_matches)} match):")
for am in arg_matches:
    print(f"  • {am.get('match_name')} (Kickoff: {am.get('kickoff')})")

pipeline = StrictTicketPipeline()
guardian = RealityGateGuardian()

# Costruisci indice telemetria con folding
c.execute("""
    SELECT team_name, normalized_name, xg_home_shrunk, xg_away_shrunk, xga_home_shrunk, xga_away_shrunk, 
           avg_goals_total, first_half_ratio, over15_pct, over25_pct, btts_pct, matches_played
    FROM team_telemetry_2026
""")
all_tele = c.fetchall()
tele_map = {}
for r in all_tele:
    t_name = r[0]
    norm_name = r[1]
    tele_map[_fold_team(t_name)] = r
    tele_map[_fold_team(norm_name)] = r

def get_tele(name):
    folded = _fold_team(name)
    if folded in tele_map:
        return tele_map[folded]
    for k, v in tele_map.items():
        if len(k) >= 5 and (k in folded or folded in k):
            return v
    return None

for am in arg_matches:
    match_name = am.get("match_name")
    parts = [p.strip() for p in match_name.split(" vs ")]
    home_name, away_name = parts[0], parts[1]
    
    h_tele = get_tele(home_name)
    a_tele = get_tele(away_name)
    
    print("\n" + "=" * 78)
    print(f"⚽ ANALISI DETTAGLIATA: {home_name.upper()} vs {away_name.upper()}")
    print(f"⏰ Kickoff: {am.get('kickoff')} | Torneo: {am.get('tournament')}")
    print("=" * 78)
    
    if not h_tele or not a_tele:
        print(f"⚠️ Telemetria mancante per una delle squadre! H: {bool(h_tele)}, A: {bool(a_tele)}")
        continue
        
    xg_home = float(h_tele[2] or 1.20)
    xg_away = float(a_tele[3] or 1.00)
    xga_home = float(h_tele[4] or 1.10)
    xga_away = float(a_tele[5] or 1.20)
    
    print(f"📈 TELEMETRIA 2026:")
    print(f"  • {h_tele[0]} (Casa - {h_tele[11]} gare): xG Fatti {xg_home:.3f} | xG Subiti {xga_home:.3f} | Over 1.5: {h_tele[8]}% | Over 2.5: {h_tele[9]}% | Gol/BTTS: {h_tele[10]}%")
    print(f"  • {a_tele[0]} (Trasferta - {a_tele[11]} gare): xG Fatti {xg_away:.3f} | xG Subiti {xga_away:.3f} | Over 1.5: {a_tele[8]}% | Over 2.5: {a_tele[9]}% | Gol/BTTS: {a_tele[10]}%")
    print(f"  • Attesa Gol Totale: xG Combinato = {xg_home + xg_away:.2f}")

    # Esame Quote Netwin e Calcolo Probabilità / Edge
    markets_dict = am.get("markets", {})
    all_evaluated = []
    
    # 1. 1X2 e Doppia Chance
    for cat in ["1X2", "DOPPIA_CHANCE", "UNDER_OVER", "GOL_NOGOL", "MULTIGOL", "COMBO", "CHANCE_MIX", "PRIMO_TEMPO"]:
        items = markets_dict.get(cat, {})
        if isinstance(items, dict):
            for lbl, odd in items.items():
                if isinstance(odd, dict):
                    for sub_lbl, sub_odd in odd.items():
                        full_lbl = f"{sub_lbl} {lbl}" if cat == "UNDER_OVER" else f"{lbl} {sub_lbl}"
                        try:
                            o_val = float(sub_odd)
                            prob = pipeline.engine.goal_market_probability(xg_home, xg_away, full_lbl)
                            if prob and prob > 0:
                                edge = (prob * o_val) - 1.0
                                all_evaluated.append((cat, full_lbl, o_val, prob, edge))
                        except Exception:
                            pass
                else:
                    try:
                        o_val = float(odd)
                        prob = pipeline.engine.goal_market_probability(xg_home, xg_away, lbl)
                        if prob and prob > 0:
                            edge = (prob * o_val) - 1.0
                            all_evaluated.append((cat, lbl, o_val, prob, edge))
                    except Exception:
                        pass
                        
    # Ordina per edge decrescente
    all_evaluated.sort(key=lambda x: (x[4] * 2.0) + (x[3] * 1.5), reverse=True)
    
    print("\n🎯 TOP MERCATI PER SCORE QUANTITATIVO (Dixon-Coles vs Quote Netwin):")
    print(f"{'Categoria':<15} | {'Mercato':<26} | {'Quota':<6} | {'P(Reale)':<8} | {'Fair Odd':<8} | {'Edge %':<8} | {'Gate Audit'}")
    print("-" * 95)
    
    for cat, lbl, o_val, prob, edge in all_evaluated[:15]:
        fair_odd = 1.0 / prob if prob > 0 else 0
        cand = MarketCandidate(
            match_name=match_name,
            tournament="Argentina",
            market_name=lbl,
            bookmaker_odd=o_val,
            market_type=cat,
            kickoff_time=normalize_kickoff(am.get("kickoff")),
            xg_home=xg_home,
            xg_away=xg_away,
            home_matches_played=h_tele[11],
            away_matches_played=a_tele[11],
            sixth_sense_analysis=f"{home_name} vs {away_name} mercato {lbl}"
        )
        guard_ok, guard_msg = guardian.audit_candidate(cand)
        val_rep = pipeline.validate_candidate(cand)
        
        status_txt = "✅ PASS" if (guard_ok and val_rep.passed) else f"❌ {val_rep.rejection_reason or guard_msg}"
        print(f"{cat:<15} | {lbl:<26} | {o_val:<6.2f} | {prob*100:<7.1f}% | @{fair_odd:<7.2f} | {edge*100:<+7.1f}% | {status_txt}")

#!/usr/bin/env python3
"""
scripts/scan_rolling_ten_gems.py — Scanner Data-First "Rolling-10" (Squadre & Singoli Giocatori).

Flusso:
1. Sincronizza le ultime 10 partite di tutte le squadre nel database `data/bagent.db`.
2. Sincronizza le ultime 10 presenze dei singoli calciatori certificati (Regola #84 & #87).
3. Estrae solo le statistiche con frequenza di avveramento dominante (Hit-Rate >= 85% - 100%).
4. Incrocia le anomalie statistiche con i mercati dei bookmaker per preparare le Gemme.
"""

from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.analysis.rolling_ten_engine import RollingTenEngine

TOP_LEAGUES = [
    "Serie A",
    "Premier League",
    "LaLiga",
    "Bundesliga",
    "Ligue 1",
    "Eredivisie",
]


def main() -> int:
    engine = RollingTenEngine()
    added_today = engine.sync_today_completed_matches()
    teams_updated = engine.compute_all_teams_rolling_ten(min_matches=5)
    players_updated = engine.sync_player_rolling_ten()

    print("=" * 95)
    print("🚀 BAGENT ROLLING-10 ENGINE — DATA-FIRST STATISTICAL SCANNER (SQUADRE & GIOCATORI)")
    print("=" * 95)
    print(f"• Partite odierne sincronizzate : {added_today}")
    print(f"• Squadre analizzate (ultime 10): {teams_updated}")
    print(f"• Giocatori analizzati (ult. 10): {players_updated}")
    print("-" * 95)

    # 1. Top Gemme di Squadra nei campionati principali
    team_gems = engine.get_top_team_gems(leagues=TOP_LEAGUES, min_hit_rate=90.0, limit=20)
    print("\n📊 1. TOP STATISTICHE SQUADRA (Hit-Rate >= 90% nelle Ultime 10 Partite):")
    print(f"{'Squadra':<22} | {'Campionato':<15} | {'Statistica Dominante (Mercato)':<30} | {'Hit-Rate':<9} | {'Medie Reali 10 Gare'}")
    print("-" * 110)
    for g in team_gems:
        medie = (
            f"Gol: {g['avg_goals_scored']:.1f}F/{g['avg_goals_conceded']:.1f}S | "
            f"Tiri: {g['avg_shots_for']:.1f} | Corner: {g['avg_corners_for']:.1f}"
        )
        print(
            f"{g['team_name']:<22} | {g['league']:<15} | {g['top_stat_market']:<30} | "
            f"{g['top_stat_hit_rate']:>6.1f}%  | {medie}"
        )

    # 2. Top Gemme Singoli Giocatori
    player_gems = engine.get_top_player_gems(min_hit_rate=90.0)
    print("\n🎯 2. TOP GEMME SINGOLI GIOCATORI (Hit-Rate >= 90% nelle Ultime 10 Presenze):")
    print(f"{'Giocatore (Squadra)':<32} | {'Ruolo':<14} | {'Gemma Mercato Bookmaker':<36} | {'Hit-Rate':<8} | {'Quota Tip.'}")
    print("-" * 110)
    for p in player_gems:
        label = f"{p['player_name']} ({p['team_name']})"
        print(
            f"{label:<32} | {p['role']:<14} | {p['best_gem_market']:<36} | "
            f"{p['best_gem_hit_rate']:>6.1f}% | @{p['typical_odd']:.2f}"
        )

    # 3. Demo Incrocio Match Data-First
    print("\n🔍 3. ESEMPIO INCROCIO DATA-FIRST SU BIG MATCH (Squadre + Giocatori):")
    for h_team, a_team in [("Milan", "Atalanta"), ("Inter", "Como")]:
        cross = engine.cross_analyze_match(h_team, a_team)
        print(f"\n  ⚽ {cross['match']} ({cross.get('league', '')}):")
        if cross["netwin_gems"]:
            top_nw = cross["netwin_gems"][0]
            print(f"     • [NETWIN NATIVE]   {top_nw['market']} ➔ Hit-Rate: {top_nw['hit_rate']:.1f}% ({top_nw['detail']})")
        if cross["specialist_gems"]:
            top_sp = cross["specialist_gems"][0]
            print(f"     • [GOLDBET/SNAI]    {top_sp['market']} ➔ Hit-Rate: {top_sp['hit_rate']:.1f}% ({top_sp['detail']})")
        if cross["player_gems"]:
            for pg in cross["player_gems"][:2]:
                print(
                    f"     • [PLAYER GEM]      {pg['player_name']} ({pg['team_name']}): "
                    f"{pg['best_gem_market']} ➔ Hit-Rate: {pg['best_gem_hit_rate']:.0f}% (@{pg['typical_odd']:.2f})"
                )

    print("\n" + "=" * 95)
    print("✅ STEP COMPLETATO: Database `team_rolling_ten_telemetry` e `player_rolling_ten_telemetry` pronti.")
    print("=" * 95)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

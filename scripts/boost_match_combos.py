#!/usr/bin/env python3
"""
scripts/boost_match_combos.py — Motore per Quote Potenziate su Combinazioni Classiche.

Scaricamento mercati da API-Football (Bet365 / William Hill) e calcolo delle migliori
combinazioni pre-compilate classiche (1X2 + U/O, 1X2 + Gol, DC + U/O, Team Over 1.5)
per alzare le quote basse nella fascia Valore / Raddoppio (1.80 – 2.25+).

Utilizzo:
    # Per singola partita tramite ID fixture:
    python scripts/boost_match_combos.py --fixture 1492360

    # Per squadre:
    python scripts/boost_match_combos.py --teams "Juventus" "Roma"

    # Per campionato imminente:
    python scripts/boost_match_combos.py --league serie_a
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
load_dotenv()
from typing import Any, Dict, List, Optional

# Aggiunge root al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.football.external.collector import FootballExternalCollector
from services.analysis.classic_combo_optimizer import ClassicComboOptimizer, ComboSelection

LEAGUES = {
    "serie_a": 135,
    "serie_b": 136,
    "premier_league": 39,
    "la_liga": 140,
    "bundesliga": 78,
    "ligue_1": 61,
    "champions_league": 2,
    "europa_league": 3,
    "brasileirao": 71,
}


def estimate_xg(
    collector: FootballExternalCollector,
    league_id: int,
    season: int,
    home_id: int,
    away_id: int,
) -> tuple[float, float]:
    """
    Stima xG attesi per squadra casa e ospite usando le statistiche della stagione in corso.
    Se non disponibili, usa una media ponderata di default (1.50 - 1.15).
    """
    xg_home = 1.50
    xg_away = 1.15

    try:
        # Statistiche casa
        stats_h = collector.team_stats(home_id, league_id, season)
        # Statistiche trasferta
        stats_a = collector.team_stats(away_id, league_id, season)

        resp_h = stats_h.get("response", {})
        resp_a = stats_a.get("response", {})

        # Gol fatti in casa da Home
        gf_home_avg = float(resp_h.get("goals", {}).get("for", {}).get("average", {}).get("home", 0.0) or 0.0)
        # Gol subiti in trasferta da Away
        ga_away_avg = float(resp_a.get("goals", {}).get("against", {}).get("average", {}).get("away", 0.0) or 0.0)

        # Gol fatti in trasferta da Away
        gf_away_avg = float(resp_a.get("goals", {}).get("for", {}).get("average", {}).get("away", 0.0) or 0.0)
        # Gol subiti in casa da Home
        ga_home_avg = float(resp_h.get("goals", {}).get("against", {}).get("average", {}).get("home", 0.0) or 0.0)

        if gf_home_avg > 0 and ga_away_avg > 0:
            xg_home = (gf_home_avg + ga_away_avg) / 2.0
        elif gf_home_avg > 0:
            xg_home = gf_home_avg

        if gf_away_avg > 0 and ga_home_avg > 0:
            xg_away = (gf_away_avg + ga_home_avg) / 2.0
        elif gf_away_avg > 0:
            xg_away = gf_away_avg

    except Exception:
        pass

    return round(xg_home, 2), round(xg_away, 2)


def extract_base_odds(odds_response: dict) -> dict[str, float]:
    """Estrae le quote 1X2 base dalla risposta quote per confronto."""
    base: dict[str, float] = {}
    resp = odds_response.get("response", [])
    if not resp:
        return base
    for bm in resp[0].get("bookmakers", []):
        for bet in bm.get("bets", []):
            if bet.get("id") == 1 or "match winner" in bet.get("name", "").lower():
                for v in bet.get("values", []):
                    val = str(v.get("value", "")).lower()
                    odd = float(v.get("odd", 0.0))
                    if "home" in val:
                        base["1"] = odd
                    elif "draw" in val:
                        base["X"] = odd
                    elif "away" in val:
                        base["2"] = odd
                if len(base) == 3:
                    return base
    return base


def analyze_fixture_combos(
    collector: FootballExternalCollector,
    fixture_id: int,
    min_quota: float = 1.75,
    max_quota: float = 2.40,
    min_prob: float = 0.40,
):
    """Analizza e stampa le migliori combo per una fixture."""
    # Dettagli fixture
    raw_fix = collector.fixture(fixture_id)
    resp = raw_fix.get("response", [])
    if not resp:
        print(f"❌ Nessun dato trovato per la fixture {fixture_id}")
        return

    f_data = resp[0]
    fixture_info = f_data.get("fixture", {})
    league_info = f_data.get("league", {})
    home = f_data.get("teams", {}).get("home", {})
    away = f_data.get("teams", {}).get("away", {})

    home_name = home.get("name", "Home")
    away_name = away.get("name", "Away")
    home_id = home.get("id")
    away_id = away.get("id")
    league_name = league_info.get("name", "Campionato")
    league_id = league_info.get("id", 0)
    season = league_info.get("season", datetime.now().year)
    match_date = fixture_info.get("date", "")[:16].replace("T", " ")

    print("\n" + "=" * 78)
    print(f"⚽ {home_name} vs {away_name}")
    print(f"🏆 {league_name} ({season}) | 📅 {match_date} UTC | ID: {fixture_id}")
    print("=" * 78)

    # 1. Download quote
    odds_data = collector.odds(fixture_id)
    if not odds_data.get("response"):
        print("⚠️ Nessuna quota pre-partita attualmente disponibile per questo evento.")
        return

    # Quote 1X2 base
    base_odds = extract_base_odds(odds_data)
    if base_odds:
        print(f"📊 Quote 1X2 Base:  1 @ {base_odds.get('1', '-')}  |  X @ {base_odds.get('X', '-')}  |  2 @ {base_odds.get('2', '-')}")

    # 2. Stima xG rolling
    xg_h, xg_a = estimate_xg(collector, league_id, season, home_id, away_id)
    print(f"🎯 Stima xG Modello: {home_name} {xg_h:.2f} — {xg_a:.2f} {away_name} (Totale atteso: {xg_h + xg_a:.2f} gol)")

    # 3. Ottimizzatore Combo
    optimizer = ClassicComboOptimizer(
        xg_home=xg_h,
        xg_away=xg_a,
        home_team=home_name,
        away_team=away_name,
        min_quota=min_quota,
        max_quota=max_quota,
        min_prob=min_prob,
    )

    combos = optimizer.extract_and_evaluate_combos(odds_data)

    if not combos:
        print(f"\n⚠️ Nessuna combo classica soddisfa i requisiti nella fascia quota {min_quota:.2f} - {max_quota:.2f} con probabilità ≥ {min_prob*100:.0f}%.")
        return

    print(f"\n🚀 TOP COMBINAZIONI VALORE / RADDOPPIO ({min_quota:.2f} – {max_quota:.2f}):")
    print("-" * 78)
    print(f"{'#':<3} {'MERCATO / SELEZIONE':<25} {'QUOTA':<8} {'PROB':<7} {'EDGE':<8} {'RISCHIO':<8} {'NOTE TATTICHE'}")
    print("-" * 78)

    for idx, c in enumerate(combos[:8], 1):
        risk_badge = "🟢" if c.risk_level == "BASSO" else ("🟡" if c.risk_level == "MEDIO" else "🔴")
        print(
            f"{idx:<3} {c.netwin_label:<25} @ {c.odd:<6.2f} {c.prob_pct:<7} {c.edge_pct:<8} {risk_badge} {c.risk_level:<6} {c.tactical_rationale[:35]}..."
        )

    print("-" * 78)

    # Evidenzia la migliore opzione di boost
    best = combos[0]
    base_target = base_odds.get("1" if "1" in best.selection else ("2" if "2" in best.selection else "1X"), 0.0)
    print(f"\n💡 MIGLIOR BOOST RACCOMANDATO: 【 {best.netwin_label} @ {best.odd:.2f} 】")
    if base_target > 1.0:
        boost_pct = ((best.odd - base_target) / base_target) * 100
        print(f"   ➔ Trasforma quota base {base_target:.2f} in {best.odd:.2f} (+{boost_pct:.1f}% di rendimento a parità di cassa)")
    print(f"   ➔ Probabilità calcolata: {best.prob_pct} | Edge matematico: {best.edge_pct}")
    print(f"   ➔ Rationale: {best.tactical_rationale}")
    print("=" * 78 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Calcolatore Quote Potenziate su Combo Classiche")
    parser.add_argument("--fixture", type=int, help="ID della fixture API-Football")
    parser.add_argument("--teams", nargs=2, help="Nomi delle due squadre (es. 'Juventus' 'Roma')")
    parser.add_argument("--league", type=str, choices=list(LEAGUES.keys()), help="Campionato per cui cercare match")
    parser.add_argument("--min_quota", type=float, default=1.75, help="Quota minima (default: 1.75)")
    parser.add_argument("--max_quota", type=float, default=2.40, help="Quota massima (default: 2.40)")
    parser.add_argument("--min_prob", type=float, default=0.40, help="Probabilità minima modello (default: 0.40)")

    args = parser.parse_args()

    collector = FootballExternalCollector()

    if args.fixture:
        analyze_fixture_combos(
            collector,
            args.fixture,
            min_quota=args.min_quota,
            max_quota=args.max_quota,
            min_prob=args.min_prob,
        )
    elif args.teams:
        t_home, t_away = args.teams
        today_str = date.today().isoformat()
        fix_id = collector.find_fixture(t_home, t_away, today_str)
        if not fix_id:
            # Prova domani o ieri
            tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
            fix_id = collector.find_fixture(t_home, t_away, tomorrow_str)

        if not fix_id:
            print(f"❌ Impossibile trovare la fixture tra {t_home} e {t_away}")
            sys.exit(1)

        analyze_fixture_combos(
            collector,
            fix_id,
            min_quota=args.min_quota,
            max_quota=args.max_quota,
            min_prob=args.min_prob,
        )
    elif args.league:
        lid = LEAGUES[args.league]
        print(f"🔍 Ricerca partite imminenti per la lega {args.league.upper()} (ID {lid})...")
        today_str = date.today().isoformat()
        fixtures = collector.fixtures_by_date(today_str, league_id=lid)
        if not fixtures.get("response"):
            tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
            fixtures = collector.fixtures_by_date(tomorrow_str, league_id=lid)

        resp = fixtures.get("response", [])
        if not resp:
            print(f"⚠️ Nessuna partita trovata oggi/domani per {args.league.upper()}.")
            return

        print(f"Trovate {len(resp)} partite. Analisi in corso...\n")
        for f in resp[:5]:
            fid = f["fixture"]["id"]
            analyze_fixture_combos(
                collector,
                fid,
                min_quota=args.min_quota,
                max_quota=args.max_quota,
                min_prob=args.min_prob,
            )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

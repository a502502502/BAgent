#!/usr/bin/env python3
"""
scripts/audit_match_dna.py — CLI Audit DNA Tattico di Campionato & Squadre (Regola #71).

Analizza qualsiasi partita e certifica all'istante:
1. Il Profilo Tattico di Lega e Squadre (DEFENSIVE_ATTRITION, OPEN_BALLISTIC, ASYMMETRIC_DOMINANCE, PRAGMATIC_MANAGEMENT)
2. Il Check di Idoneità su uno specifico mercato proposto (--market) con punteggio da 0 a 100
3. I mercati a SEMAFORO VERDE (quelli che il DNA della partita rende naturali e protetti)
4. I mercati a SEMAFORO ROSSO (le trappole da cui stare lontani)

Uso:
    python scripts/audit_match_dna.py --league "MLS" --home "San Jose Earthquakes" --away "LAFC" --market "Over 6.5 Corner"
    python scripts/audit_match_dna.py --league "Argentina" --home "River Plate" --away "Huracan" --market "Over 0.5 Gol"
    python scripts/audit_match_dna.py --league "Argentina" --home "River Plate" --away "Huracan" --market "Under 3.0 Asiatico"
    python scripts/audit_match_dna.py --demo
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.league_dna_market_matcher import LeagueDNAMarketMatcher


def print_dna_report(
    league: str,
    home: str,
    away: str,
    matcher: LeagueDNAMarketMatcher,
    tested_market: str = "",
    tested_odd: float = 0.0
):
    rec = matcher.get_market_recommendations(league, home, away)

    print("\n" + "=" * 90)
    print(f"🧬 AUDIT DNA TATTICO: {home} vs {away} ({league})")
    print("=" * 90)
    print(f"📌 CLUSTER LEGA:        [{rec.league_cluster}]")
    print(f"📌 ARCHETIPO MATCH:     [{rec.match_archetype}]")
    print(f"ℹ️  Diagnosi:            {rec.cluster_description}")

    if rec.league_stats:
        stats_str = ", ".join(f"{k}: {v}" for k, v in rec.league_stats.items())
        print(f"📊 Metriche Campionato:  {stats_str}")
    print("-" * 90)

    # Check specifico sul mercato se richiesto
    if tested_market:
        check_res = matcher.check_market_suitability(
            league=league,
            home_team=home,
            away_team=away,
            market_name=tested_market,
            bookmaker_odd=tested_odd
        )
        print("\n🔍 CHECK IDONEITÀ MERCATO:")
        print(f"  • Mercato Testato:     '{check_res.market_name}'" + (f" @ {tested_odd:.2f}" if tested_odd > 0 else ""))
        if check_res.status == "GREEN":
            status_icon = "🟢 APPROVATO (SEMAFORO VERDE - MASSIMA IDONEITÀ)"
        elif check_res.status == "YELLOW":
            status_icon = "🟡 ACCETTABILE (SEMAFORO GIALLO - NEUTRO)"
        else:
            status_icon = "🔴 VIETATO (SEMAFORO ROSSO - INCOMPATIBILE COL DNA)"
        print(f"  • Stato:               {status_icon}")
        print(f"  • Suitability Score:   {check_res.suitability_score:.1f} / 100")
        print(f"  • Valutazione:         {check_res.tactical_rationale}")
        if check_res.rejection_reason:
            print(f"  • Motivo Rifiuto:      ⚠️  {check_res.rejection_reason}")
        if check_res.recommended_alternatives:
            alts_str = ", ".join(check_res.recommended_alternatives)
            print(f"  • Alternative Ideali:  ⭐ {alts_str}")
        print("-" * 90)

    print("\n🟢 SEMAFORO VERDE: MERCATI NATURALI CONSIGLIATI (P >= 88-96%):")
    for idx, r in enumerate(rec.recommended_archetypes, 1):
        print(f"  {idx}. ⭐ {r['name']} [{r['category']}] — Priorità: {r['priority']}")
        print(f"     ➔ {r['why']}")

    print("\n🔴 SEMAFORO ROSSO: MERCATI TOSSICI / VIETATI:")
    for idx, p in enumerate(rec.prohibited_archetypes, 1):
        print(f"  {idx}. ❌ {p['name']}")
        print(f"     ⚠️  {p['risk']}")

    print("\n💡 INSIGHTS CHIAVE:")
    for ins in rec.key_insights:
        print(f"  • {ins}")
    print("=" * 90)


def main():
    parser = argparse.ArgumentParser(description="Audit DNA Tattico di Campionato & Squadre")
    parser.add_argument("--league", type=str, help="Nome del campionato (es. 'Argentina', 'MLS', 'Premier League')")
    parser.add_argument("--home", type=str, help="Squadra di casa")
    parser.add_argument("--away", type=str, help="Squadra ospite")
    parser.add_argument("--market", type=str, default="", help="Mercato specifico da testare (es. 'Over 6.5 Corner', 'Under 3.0 Asiatico')")
    parser.add_argument("--odd", type=float, default=0.0, help="Quota bookmaker del mercato testato")
    parser.add_argument("--demo", action="store_true", help="Esegui demo comparativa sui cluster chiave")
    args = parser.parse_args()

    matcher = LeagueDNAMarketMatcher()

    if args.demo or not (args.league and args.home and args.away):
        demo_fixtures = [
            ("Argentina Liga Profesional", "River Plate", "Huracan", "Over 0.5 Gol", 1.08),
            ("MLS Stati Uniti", "San Jose Earthquakes", "LAFC", "Over 6.5 Corner Incontro", 1.15),
            ("Premier League", "Manchester City", "Sunderland", "1 Fisso", 1.22),
            ("Serie A", "Napoli", "Lecce", "1X + Over 1.5", 1.35),
        ]
        print("\n🚀 AVVIO DEMO COMPARATIVA AUDIT DNA TATTICO E CHECK IDONEITÀ MERCATO")
        for l, h, a, m, odd in demo_fixtures:
            print_dna_report(l, h, a, matcher, tested_market=m, tested_odd=odd)
    else:
        print_dna_report(args.league, args.home, args.away, matcher, tested_market=args.market, tested_odd=args.odd)


if __name__ == "__main__":
    main()

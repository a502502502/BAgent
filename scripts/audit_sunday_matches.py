#!/usr/bin/env python3
"""
scripts/audit_sunday_matches.py — Audit DNA Tattico e Validazione Schedina Domenica (Regole #70 & #71).

Esegue l'audit completo sulle partite di domenica:
1. Premier League: Manchester City vs Sunderland
2. Serie A: Milan vs Lecce
3. Serie A: Fiorentina vs Napoli
4. LaLiga: Villarreal vs Levante
5. Liga Profesional: San Lorenzo vs Boca Juniors
6. MLS: San Jose Earthquakes vs LAFC
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analysis.league_dna_market_matcher import LeagueDNAMarketMatcher
from services.betting.strict_ticket_pipeline import StrictTicketPipeline, MarketCandidate

def main():
    matcher = LeagueDNAMarketMatcher()
    pipeline = StrictTicketPipeline()

    sunday_fixtures = [
        {
            "league": "Premier League",
            "home": "Manchester City",
            "away": "Sunderland",
            "tested_market": "Corner Squadra Man City Over 3.5",
            "tested_odd": 1.16,
            "market_type": "TEAM_CORNERS",
            "shots": 21.5,
            "p_real": 0.93,
            "sixth_sense": "City all'Etihad schiaccia il Sunderland con oltre il 70% di possesso. La difesa a 5 avversaria concede 7-10 corner."
        },
        {
            "league": "Serie A",
            "home": "Milan",
            "away": "Lecce",
            "tested_market": "1X + MultiGol 1-5",
            "tested_odd": 1.18,
            "market_type": "COMBO",
            "shots": 17.2,
            "p_real": 0.91,
            "sixth_sense": "Milan a San Siro deve riscattare il passo falso; Lecce imposterà una gara di puro contenimento."
        },
        {
            "league": "Serie A",
            "home": "Fiorentina",
            "away": "Napoli",
            "tested_market": "Under 3.5 Gol Totali",
            "tested_odd": 1.34,
            "market_type": "GOALS_UNDER",
            "shots": 14.5,
            "p_real": 0.84,
            "sixth_sense": "Napoli di Allegri fedele al corto muso e gestione del ritmo. Fiorentina al Franchi non concede spazi."
        },
        {
            "league": "LaLiga",
            "home": "Villarreal",
            "away": "Levante",
            "tested_market": "Chance Mix: 1X o Over 1.5",
            "tested_odd": 1.14,
            "market_type": "CHANCE_MIX",
            "shots": 18.0,
            "p_real": 0.96,
            "sixth_sense": "Villarreal travolgente alla Cerámica contro un Levante debole in trasferta. Copre l'1-0 e qualsiasi pareggio."
        },
        {
            "league": "Liga Profesional Argentina",
            "home": "San Lorenzo",
            "away": "Boca Juniors",
            "tested_market": "Under 3.0 Asiatico",
            "tested_odd": 1.24,
            "market_type": "ASIAN_UNDER",
            "shots": 11.0,
            "p_real": 0.88,
            "sixth_sense": "Clasico al Nuevo Gasometro ad altissima tensione: duelli a centrocampo, falli e pochissimo spazio."
        },
        {
            "league": "MLS Stati Uniti",
            "home": "San Jose Earthquakes",
            "away": "LAFC",
            "tested_market": "Over 6.5 Corner Totali Incontro",
            "tested_odd": 1.16,
            "market_type": "CORNER",
            "shots": 24.8,
            "p_real": 0.92,
            "sixth_sense": "MLS campo largo e transizioni veloci: media MLS oltre 10.8 corner a gara."
        }
    ]

    print("=" * 90)
    print("📋 AUDIT COMPLETO DNA TATTICO SULLE PARTITE DI DOMENICA")
    print("=" * 90)

    for idx, f in enumerate(sunday_fixtures, 1):
        league = f["league"]
        home = f["home"]
        away = f["away"]
        m_name = f["tested_market"]
        m_odd = f["tested_odd"]

        dna_rec = matcher.get_market_recommendations(league, home, away)
        check = matcher.check_market_suitability(
            league=league,
            home_team=home,
            away_team=away,
            market_name=m_name,
            market_category=f["market_type"],
            bookmaker_odd=m_odd
        )

        c = MarketCandidate(
            match_name=f"{home} vs {away}",
            tournament=league,
            market_name=m_name,
            bookmaker_odd=m_odd,
            market_type=f["market_type"],
            team_avg_shots=f["shots"],
            estimated_p_90=f["p_real"],
            sixth_sense_analysis=f["sixth_sense"]
        )
        report = pipeline.validate_candidate(c)

        print(f"\n{idx}. {home} vs {away} ({league})")
        print(f"   • Profilo Tattico: [{dna_rec.match_archetype}] in [{dna_rec.league_cluster}]")
        print(f"   • Mercato Scelto:  '{m_name}' @ {m_odd:.2f}")
        print(f"   • Check DNA:       {check.status} (Score: {check.suitability_score:.1f}/100)")
        print(f"   • Rationale DNA:   {check.tactical_rationale}")
        print(f"   • Pipeline Gate:   {'🟢 CERTIFICATO ED APPROVATO' if report.passed else '🔴 BOCCIATO'}")
        if report.passed:
            print(f"   • P_reale: {report.real_probability*100:.1f}% | Fair Odd: @{report.fair_odds:.2f} | Edge: {report.mathematical_edge*100:+.1f}%")
        else:
            print(f"   • Motivo: {report.rejection_reason}")

    print("\n" + "=" * 90)

if __name__ == "__main__":
    main()

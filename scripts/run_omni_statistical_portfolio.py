#!/usr/bin/env python3
"""
scripts/run_omni_statistical_portfolio.py — Pipeline di Generazione e Ottimizzazione Statistica dei Ticket.

Utilizza il nuovo OmniStatisticalOptimizer per:
1. Ingerire i cataloghi reali SNAI (in reports/snai/*.json) per tutte le partite di Nations League.
2. Applicare i modelli statistici multi-dominio:
   - Gol/Tempi (Bivariate Dixon-Coles Poisson)
   - Calci d'Angolo (Bivariate Negative Binomial / Race-to-X Poisson)
   - Disciplinari / Falli (Poisson/Gamma cartellini e falli giocatore)
   - Player Props Ultra (xG/90 + legni + subentrante)
3. Calcolare per ciascun mercato lo Sweet-Spot Score S(p, q) a campana gaussiana centrata su p=80%, q=1.45.
4. Eseguire l'ottimizzazione combinatoria per costruire 5 ticket diversificati (max 4 leg ciascuno).
5. Eseguire l'audit indipendente di Seconda AI con Groq Cloud (modello openai/gpt-oss-120b).
6. Salvare e stampare il portafoglio certificato.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path("C:/Project/BAgent")
sys.path.insert(0, str(ROOT))

from services.analysis.omni_statistical_optimizer import (
    MatchDossier,
    OmniStatisticalPricer,
    CombinatorialPortfolioOptimizer
)
from services.debate.groq_auditor import GroqAuditor


# Database statistico delle 17 partite di Nations League
STATISTICAL_DOSSIERS = {
    "italia-turchia.json": MatchDossier(
        match_name="Italia vs Turchia",
        kickoff="2026-10-05 20:45 CEST",
        xg_home=2.05,
        xg_away=0.80,
        corners_home=6.5,
        corners_away=3.2,
        cards_home=1.8,
        cards_away=2.6,
        players={
            "scamacca": {"xg_90": 0.58, "fouls_avg": 1.1, "minutes": 75},
            "celik": {"xg_90": 0.05, "fouls_avg": 2.1, "minutes": 90}
        }
    ),
    "francia-belgio.json": MatchDossier(
        match_name="Francia vs Belgio",
        kickoff="2026-10-05 20:45 CEST",
        xg_home=1.75,
        xg_away=1.05,
        corners_home=5.8,
        corners_away=4.2,
        cards_home=1.9,
        cards_away=2.2
    ),
    "romania-svezia.json": MatchDossier(
        match_name="Romania vs Svezia",
        kickoff="2026-10-05 20:45 CEST",
        xg_home=1.15,
        xg_away=1.65,
        corners_home=3.8,
        corners_away=6.0,
        cards_home=2.5,
        cards_away=1.9
    ),
    "bosnia-erzegovina-polonia.json": MatchDossier(
        match_name="Bosnia Erzegovina vs Polonia",
        kickoff="2026-10-05 20:45 CEST",
        xg_home=1.15,
        xg_away=1.35,
        corners_home=4.2,
        corners_away=4.8,
        cards_home=2.6,
        cards_away=2.2
    ),
    "irlanda-del-nord-georgia.json": MatchDossier(
        match_name="Irlanda del Nord vs Georgia",
        kickoff="2026-10-05 20:45 CEST",
        xg_home=1.05,
        xg_away=0.90,
        corners_home=4.8,
        corners_away=3.8,
        cards_home=2.2,
        cards_away=2.4
    ),
    "ucraina-ungheria.json": MatchDossier(
        match_name="Ucraina vs Ungheria",
        kickoff="2026-10-05 20:45 CEST",
        xg_home=1.25,
        xg_away=1.15,
        corners_home=4.4,
        corners_away=4.2,
        cards_home=2.5,
        cards_away=2.6
    ),
    "montenegro-armenia.json": MatchDossier(
        match_name="Montenegro vs Armenia",
        kickoff="2026-10-05 20:45 CEST",
        xg_home=1.60,
        xg_away=0.75,
        corners_home=6.2,
        corners_away=2.8,
        cards_home=2.1,
        cards_away=2.8
    ),
    "croazia-spagna.json": MatchDossier(
        match_name="Croazia vs Spagna",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=0.95,
        xg_away=1.95,
        corners_home=3.2,
        corners_away=6.8,
        cards_home=2.7,
        cards_away=1.6,
        players={
            "yamal": {"xg_90": 0.52, "fouls_avg": 0.9, "minutes": 80}
        }
    ),
    "inghilterra-repubblica-ceca.json": MatchDossier(
        match_name="Inghilterra vs Repubblica Ceca",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=2.20,
        xg_away=0.70,
        corners_home=7.4,
        corners_away=2.2,
        cards_home=1.4,
        cards_away=2.9,
        players={
            "gordon": {"xg_90": 0.50, "fouls_avg": 0.8, "minutes": 70},
            "bellingham": {"xg_90": 0.48, "fouls_avg": 1.4, "minutes": 85}
        }
    ),
    "svizzera-macedonia.json": MatchDossier(
        match_name="Svizzera vs Macedonia del Nord",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=1.70,
        xg_away=0.65,
        corners_home=6.1,
        corners_away=2.9,
        cards_home=1.8,
        cards_away=2.6
    ),
    "albania-san-marino.json": MatchDossier(
        match_name="Albania vs San Marino",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=2.80,
        xg_away=0.20,
        corners_home=8.5,
        corners_away=1.2,
        cards_home=1.2,
        cards_away=3.1
    ),
    "kazakistan-isole-far-oer.json": MatchDossier(
        match_name="Kazakistan vs Isole Far Oer",
        kickoff="2026-10-06 16:00 CEST",
        xg_home=1.40,
        xg_away=0.80,
        corners_home=5.1,
        corners_away=3.6,
        cards_home=2.2,
        cards_away=2.3
    ),
    "moldova-slovacchia.json": MatchDossier(
        match_name="Moldova vs Slovacchia",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=0.70,
        xg_away=1.75,
        corners_home=2.7,
        corners_away=6.4,
        cards_home=2.8,
        cards_away=1.9
    ),
    "bielorussia-finlandia.json": MatchDossier(
        match_name="Bielorussia vs Finlandia",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=0.90,
        xg_away=1.45,
        corners_home=3.6,
        corners_away=5.3,
        cards_home=2.7,
        cards_away=1.8
    ),
    "lussemburgo-bulgaria.json": MatchDossier(
        match_name="Lussemburgo vs Bulgaria",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=1.35,
        xg_away=1.05,
        corners_home=5.4,
        corners_away=4.1,
        cards_home=2.3,
        cards_away=2.5
    ),
    "scozia-slovenia.json": MatchDossier(
        match_name="Scozia vs Slovenia",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=1.55,
        xg_away=0.90,
        corners_home=6.5,
        corners_away=3.4,
        cards_home=2.0,
        cards_away=2.4
    ),
    "estonia-islanda.json": MatchDossier(
        match_name="Estonia vs Islanda",
        kickoff="2026-10-06 20:45 CEST",
        xg_home=0.85,
        xg_away=1.65,
        corners_home=3.5,
        corners_away=5.8,
        cards_home=2.6,
        cards_away=2.0
    )
}


def main():
    print("==================================================================")
    print("PIPELINE OTTIMIZZAZIONE STATISTICA MULTI-MERCATO (OMNI-OPTIMIZER)")
    print("==================================================================\n")

    snai_dir = ROOT / "reports/snai"
    pricer = OmniStatisticalPricer()
    optimizer = CombinatorialPortfolioOptimizer(pricer=pricer)

    candidate_picks_by_match = {}
    dossiers_list = []

    print("[1/4] Caricamento cataloghi SNAI e pricing statistico multi-dominio...")
    for filename, dossier in STATISTICAL_DOSSIERS.items():
        file_path = snai_dir / filename
        if not file_path.exists():
            continue
        with open(file_path, encoding="utf-8") as f:
            catalog_data = json.load(f)
        
        markets = catalog_data.get("markets", [])
        picks = optimizer.generate_candidate_picks(dossier, markets)
        candidate_picks_by_match[dossier.match_name] = picks
        dossiers_list.append(dossier)
        print(f"  - {dossier.match_name}: {len(picks)} mercati legali prezzati con lo Sweet-Spot")

    print(f"\n[2/4] Costruzione del portafoglio di 5 ticket diversificati (max 4 leg)...")
    portfolio = optimizer.build_diversified_portfolio(
        dossiers_list,
        candidate_picks_by_match,
        num_tickets=5,
        ticket_size=4,
        stake_per_ticket=2.50,
        bankroll_reference=100.0
    )

    print("\n[3/4] Esecuzione Audit di Seconda AI (Groq Cloud con policy EV warning)...")
    auditor = GroqAuditor()
    if auditor.is_configured():
        for i, ticket in enumerate(portfolio["tickets"], 1):
            t_name = ticket["name"]
            print(f"  - Audit Ticket {i}: {t_name} (Quota {ticket['total_odds']})...")
            audit_legs = []
            for leg in ticket["legs"]:
                audit_legs.append({
                    "match_name": leg["match"],
                    "tournament": "UEFA Nations League",
                    "market": leg["market"],
                    "book_odd": float(leg["odds"]),
                    "fair_odd": float(leg["fair_odd"]),
                    "probability": float(leg["probability"]),
                    "edge": float(leg["edge"]),
                    "notes": f"Famiglia: {leg['market_family']} | Score Gaussiano: {leg['score']}"
                })
            
            audit_res = auditor.audit_ticket(
                title=t_name,
                legs=audit_legs,
                bankroll=portfolio["bankroll_reference"]
            )
            
            # Fallback handling in caso di rate limit 429
            if not audit_res.get("success") and "429" in audit_res.get("error", ""):
                print("    Rate limit 429 incontrato, attesa 15s...")
                time.sleep(15)
                audit_res = auditor.audit_ticket(
                    title=t_name,
                    legs=audit_legs,
                    bankroll=portfolio["bankroll_reference"],
                    model="llama-3.3-70b-versatile"
                )

            ticket["groq"] = audit_res
            appr = audit_res.get("approved")
            warn = audit_res.get("ev_warning")
            print(f"    Esito: {'APPROVATA' if appr else 'NON APPROVATA'} | Avviso: {warn or 'Nessun vincolo'}")
            time.sleep(3)
        portfolio["groq_audit"] = "ESEGUITO_CON_SUCCESSO_CON_NUOVA_POLICY"
    else:
        print("  - Groq Cloud non configurato, audit saltato.")

    # Salva il portafoglio
    out_path = ROOT / "reports/tickets/ticket_snai_nl_5tickets_portfolio.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)
    print(f"\n[4/4] Portafoglio salvato con successo in {out_path}!")

    # Stampa riassunto a terminale
    print("\n================== RIEPILOGO PORTAFOGLIO OTTIMIZZATO ==================")
    for i, t in enumerate(portfolio["tickets"], 1):
        print(f"\n--- {t['name']} ---")
        print(f"Quota: {t['total_odds']} | Prob: {t['probability']*100:.1f}% | Edge: {t['edge']*100:+.1f}% | Ritorno: {t['potential_payout']} EUR")
        for leg in t["legs"]:
            print(f"  * [{leg['market_family']}] {leg['match']} -> {leg['market']} @ {leg['odds']} (P: {leg['probability']*100:.1f}%, Score: {leg['score']}, Segnale: {leg['verdict']})")


if __name__ == "__main__":
    main()

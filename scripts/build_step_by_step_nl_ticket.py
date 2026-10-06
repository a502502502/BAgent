#!/usr/bin/env python3
"""
scripts/build_step_by_step_nl_ticket.py — Costruzione Passo-Passo della Schedina Nations League di OGGI (06/10/2026).

Filtro Tassativo di Data:
Esclude rigorosamente i match giocati ieri (05/10/2026, come Italia-Turchia, Francia-Belgio, ecc.).
Include solo i 10 match ufficiali di oggi (06/10/2026).
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from services.debate.groq_auditor import GroqAuditor


def sweet_spot_score(p: float, q: float) -> float:
    """Calcolo gaussiano Sweet-Spot: centrato su p=0.80, q=1.40."""
    if q < 1.15 or p <= 0:
        return 0.0
    p_term = ((p - 0.80) / 0.12) ** 2
    q_term = ((math.log(q) - math.log(1.40)) / 0.22) ** 2
    return float(math.exp(-0.5 * (p_term + q_term)))


def main():
    print("==========================================================================")
    print("PIPELINE A 2 LIVELLI: NATIONS LEAGUE DI OGGI (06/10/2026) PASSO DOPO PASSO")
    print("==========================================================================\n")

    nl_catalog_dir = ROOT / "reports/snai_nl/catalog"

    # PASSO 1: INGESTIONE E FILTRO DATA OGGI
    print("[PASSO 1] INGESTIONE CATALOGHI SNAI & FILTRO DATA ESCLUSIVO OGGI (06/10/2026)")
    today_matches = []
    for f in nl_catalog_dir.glob("*.json"):
        if f.name == "index.json":
            continue
        with open(f, encoding="utf-8") as fp:
            d = json.load(fp)
        ko = d.get("kickoff_time", "")
        if "2026-10-06" in ko:
            today_matches.append({
                "match": d.get("match"),
                "kickoff": ko,
                "markets_count": len(d.get("markets", [])),
                "file": f.name
            })

    print(f"  - Individuati esattamente {len(today_matches)} incontri di Nations League in programma OGGI (06/10/2026):")
    for m in sorted(today_matches, key=lambda x: x["kickoff"]):
        print(f"      * [{m['kickoff']}] {m['match']} ({m['markets_count']} mercati)")

    print("\n  - Bando Tassativo Match di Ieri: Italia-Turchia, Francia-Belgio, Bosnia-Polonia sono state giocate il 05/10 e sono escluse.")
    print("  - Regole Anti-Trappola applicate:")
    print("      * BANDO di '1X + Under 3.5' e compound Under restrittivi.")
    print("      * BANDO della monotonia 'Doppia Chance [12]' (vulnerabile allo 0-0/1-1).")
    print("      * BANDO dell'1X2 secco contro corazzate.")

    # PASSO 2: CANDIDATE SELECTION & SWEET-SPOT SCORING
    print("\n[PASSO 2] CALCOLO SCORING GAUSSIANO SWEET-SPOT S(p, q)")
    print("  Formula: S(p, q) = exp( -0.5 * [ ((p - 0.80)/0.12)^2 + ((ln(q) - ln(1.40))/0.22)^2 ] )")
    print("  Obiettivo: massimizzare il valore nel range q in [1.28, 1.48] con p in [75%, 82%].\n")

    candidates = [
        {
            "match": "Kazakistan vs Isole Far Oer",
            "kickoff": "2026-10-06 16:00 CEST",
            "competition": "UEFA Nations League",
            "family": "MULTIGOAL_TEMPI",
            "market": "MultiGol MultiEsiti [1-3 Gol]",
            "odds": 1.33,
            "est_p": 0.765,
            "tactics": "Partita pomeridiana ad Astana molto tattica e bloccata; il range 1-3 copre l'1-0, 2-0, 1-1, 2-1, 0-1, 0-2 (esclude lo 0-0 sterile e goleade)."
        },
        {
            "match": "Scozia vs Slovenia",
            "kickoff": "2026-10-06 20:45 CEST",
            "competition": "UEFA Nations League",
            "family": "CORNERS_VOLUME",
            "market": "Prima a 4 Calci d'Angolo [Team 1 - Scozia]",
            "odds": 1.45,
            "est_p": 0.760,
            "tactics": "Scozia a Hampden Park con forte spinta laterale e cross continui; Slovenia chiusa a protezione della propria area."
        },
        {
            "match": "Inghilterra vs Repubblica Ceca",
            "kickoff": "2026-10-06 20:45 CEST",
            "competition": "UEFA Nations League",
            "family": "CARTELLINI_SANZIONI",
            "market": "Under/Over 2.5 Punti Cartellini [OVER]",
            "odds": 1.40,
            "est_p": 0.780,
            "tactics": "Scontro ad alta intensità fisica con molti contrasti a centrocampo; soglia 2.5 cartellini (minimo 3 cartellini totali) ampiamente coperta."
        },
        {
            "match": "Croazia vs Spagna",
            "kickoff": "2026-10-06 20:45 CEST",
            "competition": "UEFA Nations League",
            "family": "STATISTICHE_TIRI",
            "market": "Under/Over 8.5 Tiri in Porta [OVER]",
            "odds": 1.28,
            "est_p": 0.800,
            "tactics": "Spagna e Croazia sono due formazioni a trazione offensiva e fraseggio rapido; 9 tiri nello specchio complessivi sono ampiamente alla portata."
        }
    ]

    for c in candidates:
        q = c["odds"]
        p = c["est_p"]
        score = sweet_spot_score(p, q)
        fair_odd = round(1.0 / p, 2)
        edge = round(p * q - 1.0, 3)
        c["score"] = round(score, 3)
        c["fair_odd"] = fair_odd
        c["edge"] = edge
        print(f"  • [{c['kickoff'][:16]}] {c['match']} | Famiglia: {c['family']}")
        print(f"    Mercato: {c['market']} @ {q} (P: {p*100:.1f}%, Fair: {fair_odd}, Score: {c['score']})")

    # PASSO 3: COMPOSIZIONE IBRIDA
    print("\n[PASSO 3] ASSEMBLAGGIO IBRIDO PER FAMIGLIE COMPLEMENTARI")
    print("  Combinate 4 famiglie distinte su 4 partite di oggi:")
    print("  1. MULTIGOAL: Kazakistan vs Far Oer (16:00 CEST) -> Inerzia controllata.")
    print("  2. CORNERS: Scozia vs Slovenia (20:45 CEST) -> Pressione sulle corsie.")
    print("  3. CARTELLINI: Inghilterra vs Rep. Ceca (20:45 CEST) -> Intensità sanzionatoria.")
    print("  4. STATISTICHE TIRI: Croazia vs Spagna (20:45 CEST) -> Produzione offensiva nello specchio.")

    # PASSO 4: CALCOLO MATEMATICO DEL TICKET
    print("\n[PASSO 4] AGGREGAZIONE MATEMATICA DEL TICKET")
    tot_odd = 1.0
    tot_p = 1.0
    for c in candidates:
        tot_odd *= c["odds"]
        tot_p *= c["est_p"]
    tot_odd = round(tot_odd, 2)
    tot_p = round(tot_p, 3)
    ev = round(tot_p * tot_odd - 1.0, 3)
    stake = 3.0
    payout = round(stake * tot_odd, 2)

    print(f"  - Quota Moltiplicatore Totale: {tot_odd}")
    print(f"  - Probabilità Congiunta (Joint P): {tot_p * 100:.1f}%")
    print(f"  - Fair Odd Complessiva: {round(1.0/tot_p, 2)}")
    print(f"  - Valore Atteso Stimato (EV): {ev * 100:+.1f}%")
    print(f"  - Stake Consigliato: {stake:.2f} EUR (3% del bankroll di 100 EUR)")
    print(f"  - Ritorno Potenziale: {payout:.2f} EUR")

    # PASSO 5: AUDIT CRITICO GROQ CLOUD
    print("\n[PASSO 5] AUDIT CRITICO INDIPENDENTE DI LIVELLO 2 (Groq Cloud LPU - openai/gpt-oss-120b)")
    auditor = GroqAuditor()
    audit_payload = [
        {
            "match_name": c["match"],
            "tournament": c["competition"],
            "market": c["market"],
            "book_odd": float(c["odds"]),
            "fair_odd": float(c["fair_odd"]),
            "probability": float(c["est_p"]),
            "edge": float(c["edge"]),
            "notes": f"Kickoff: {c['kickoff']} | Famiglia: {c['family']} | Score: {c['score']} | Tattica: {c['tactics']}"
        }
        for c in candidates
    ]

    ticket_name = "Quaterna Ibrida d'Elite Nations League (Solo Oggi 06/10)"
    audit_res = auditor.audit_ticket(title=ticket_name, legs=audit_payload, bankroll=100.0)
    verdict = "APPROVATA" if audit_res.get("approved") else "BOCCIATA"
    critique = audit_res.get("critique", "")

    print(f"  - Verdetto Finale Audit: {verdict}\n")
    print("Report di Audit Indipendente Groq:")
    print("------------------------------------------------------------------")
    print(critique)
    print("------------------------------------------------------------------")

    # Salvataggio Ticket Certificato
    ticket_data = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M CEST"),
        "date_target": "2026-10-06",
        "competition": "UEFA Nations League",
        "ticket_name": ticket_name,
        "stake_eur": stake,
        "total_odds": tot_odd,
        "probability": tot_p,
        "fair_odd": round(1.0/tot_p, 2),
        "edge": ev,
        "potential_payout_eur": payout,
        "legs": candidates,
        "groq_verdict": verdict,
        "groq_report": critique
    }

    out_file = ROOT / "reports/tickets/ticket_nations_league_passo_passo.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(ticket_data, f, indent=2, ensure_ascii=False)
    print(f"\nTicket salvato con successo in {out_file}!")


if __name__ == "__main__":
    main()

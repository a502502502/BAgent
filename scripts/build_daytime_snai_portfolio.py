#!/usr/bin/env python3
"""
scripts/build_daytime_snai_portfolio.py — Ottimizzatore a 2 Livelli per i 45 match SNAI diurni fino alle 16:00.

Architettura a 2 Livelli:
1. Livello 1 (Assemblaggio Quantitativo & Diversificazione Famiglie):
   - Ingerisce i cataloghi SNAI scaricati in reports/snai/2026-10-06-fino-16/.
   - Elimina la monotonia del mercato Doppia Chance [12] e bandisce combinazioni trappola (1X + Under 3.5).
   - Combina per ciascun ticket famiglie complementari: Esito Finale 1X2 protetto, Draw No Bet,
     Doppia Chance Direzionale (1X/X2), Under/Over Gol, e MultiGol.
   - Calcola quote, probabilità congiunta, fair odds e stima EV.
2. Livello 2 (Audit Critico Indipendente):
   - Invia i ticket finalisti all'Auditor LPU Groq Cloud (openai/gpt-oss-120b).
   - Verifica scenari di perdita, coerenza tattica e rilascia il verdetto finale.
3. Persistenza:
   - Salva il portafoglio in reports/tickets/ticket_snai_daytime_45matches_portfolio.json.
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

from services.debate.groq_auditor import GroqAuditor


def sweet_spot_score(p: float, q: float) -> float:
    """Calcolo gaussiano Sweet-Spot: centrato su p=0.80, q=1.40."""
    if q < 1.15 or p <= 0:
        return 0.0
    p_term = ((p - 0.80) / 0.12) ** 2
    q_term = ((math.log(q) - math.log(1.40)) / 0.22) ** 2
    return float(math.exp(-0.5 * (p_term + q_term)))


def parse_match_catalog(fl: Path) -> dict:
    with open(fl, encoding="utf-8") as fp:
        return json.load(fp)


def extract_specific_pick(catalog: dict, target_market: str, target_line: str, target_sel: str) -> dict | None:
    for m in catalog.get("markets", []):
        m_name = m.get("market", "").strip()
        line = m.get("line", "").strip()
        
        # Match market condition
        match_mkt = (target_market in m_name)
        match_line = (not target_line) or (target_line in line)
        
        if match_mkt and match_line:
            for o in m.get("outcomes", []):
                sel = o.get("selection", "").strip()
                if sel == target_sel and o.get("open"):
                    odd = float(o.get("odds", 0.0))
                    if odd > 1.0:
                        return {
                            "market_full": f"{m_name} ({line})" if line else m_name,
                            "selection": sel,
                            "odds": odd
                        }
    return None


def main():
    print("==========================================================================")
    print("PIPELINE A 2 LIVELLI: PORTAFOGLIO DIURNO SNAI (45 MATCH FINO ALLE 16:00)")
    print("==========================================================================\n")

    catalog_dir = ROOT / "reports/snai/2026-10-06-fino-16"
    index_file = catalog_dir / "index.json"

    with open(index_file, encoding="utf-8") as f:
        matches_meta = json.load(f)

    print(f"Ingeriti {len(matches_meta)} cataloghi match ufficiali SNAI.\n")

    # Mappa dei cataloghi per nome partita
    catalogs_by_name = {}
    for item in matches_meta:
        fl = ROOT / item["file"]
        if fl.exists():
            catalogs_by_name[item["match"]] = {
                "meta": item,
                "data": parse_match_catalog(fl)
            }

    # Definizione Selezioni Diversificate per Famiglia (No monotonia [12], No trappole 1X+Under)
    # Ticket 1: Mattina & Pranzo (11:00 - 13:00 CEST)
    t1_specs = [
        {
            "match": "Saudi Arabia U20 - Armenia U20",
            "competition": "INT Amichevoli U20 (Poss. Cambio Format)",
            "kickoff": "2026-10-06 11:00 CEST",
            "market_family": "ESITO_FINALE",
            "mkt_query": "1X2 ESITO FINALE",
            "line_query": "",
            "sel_query": "1",
            "market_label": "Esito Finale 1X2 [1]",
            "est_p": 0.700,
            "rationale": "Arabia Saudita U20 nettamente superiore per fisicità e continuità; Armenia quotata a 6.50."
        },
        {
            "match": "AS Trencin U19 - Spartak Trnava U19",
            "competition": "SVK Campionato U19",
            "kickoff": "2026-10-06 11:00 CEST",
            "market_family": "DOPPIA_CHANCE",
            "mkt_query": "DOPPIA CHANCE",
            "line_query": "",
            "sel_query": "1X",
            "market_label": "Doppia Chance [1X]",
            "est_p": 0.744,
            "rationale": "Trencin U19 imbattuto in casa; 1X protegge da qualsiasi equilibrio tattico."
        },
        {
            "match": "UD Leiria U23 - Santa Clara U23",
            "competition": "POR Campionato U23",
            "kickoff": "2026-10-06 12:00 CEST",
            "market_family": "UNDER_OVER_MATCH",
            "mkt_query": "UNDER/OVER",
            "line_query": "U/O 1.5",
            "sel_query": "OVER",
            "market_label": "Under/Over 1.5 [OVER]",
            "est_p": 0.762,
            "rationale": "Campionato giovanile portoghese con media superiore a 2.8 gol a partita; Over 1.5 offre ampio margine."
        },
        {
            "match": "Binh Phuoc - CS. Dong Thap",
            "competition": "VIE Coppa di Vietnam",
            "kickoff": "2026-10-06 13:00 CEST",
            "market_family": "ESITO_FINALE",
            "mkt_query": "1X2 ESITO FINALE",
            "line_query": "",
            "sel_query": "1",
            "market_label": "Esito Finale 1X2 [1]",
            "est_p": 0.733,
            "rationale": "Binh Phuoc netta favorita interna nei 16esimi di Coppa contro Dong Thap (sfavorita a 8.50)."
        }
    ]

    # Ticket 2: Asia, Amichevoli & Cina (13:00 - 13:35 CEST)
    t2_specs = [
        {
            "match": "Corea del Sud - Uzbekistan",
            "competition": "INT Amichevoli Nazionali",
            "kickoff": "2026-10-06 13:00 CEST",
            "market_family": "DRAW_NO_BET",
            "mkt_query": "DRAW NO BET",
            "line_query": "DRAW NO BET",
            "sel_query": "1",
            "market_label": "Draw No Bet [1]",
            "est_p": 0.762,
            "rationale": "Corea del Sud con caratura tecnica superiore. In caso di pareggio la selezione viene integralmente rimborsata."
        },
        {
            "match": "Changchun Yatai - Yanbian Longding",
            "competition": "CHN League One",
            "kickoff": "2026-10-06 13:00 CEST",
            "market_family": "DOPPIA_CHANCE",
            "mkt_query": "DOPPIA CHANCE",
            "line_query": "",
            "sel_query": "1X",
            "market_label": "Doppia Chance [1X]",
            "est_p": 0.794,
            "rationale": "Changchun solida tra le mura amiche contro Yanbian; 1X esclude la sconfitta casalinga."
        },
        {
            "match": "Nantong Zhiyun - Shanghai Jiading City Development",
            "competition": "CHN League One",
            "kickoff": "2026-10-06 13:30 CEST",
            "market_family": "ESITO_FINALE",
            "mkt_query": "1X2 ESITO FINALE",
            "line_query": "",
            "sel_query": "1",
            "market_label": "Esito Finale 1X2 [1]",
            "est_p": 0.680,
            "rationale": "Nantong retrocessa dalla Super League, nettamente dominante su Shanghai Jiading (quota ospite a 7.00)."
        },
        {
            "match": "Cina - Tagikistan",
            "competition": "INT Amichevoli Nazionali",
            "kickoff": "2026-10-06 13:35 CEST",
            "market_family": "DRAW_NO_BET",
            "mkt_query": "DRAW NO BET",
            "line_query": "DRAW NO BET",
            "sel_query": "1",
            "market_label": "Draw No Bet [1]",
            "est_p": 0.700,
            "rationale": "Cina favorita in casa; Draw No Bet protegge dal rischio pareggio con rimborso integrale."
        }
    ]

    # Ticket 3: Pomeriggio, England U21 & Qualificazioni (14:00 - 16:00 CEST)
    t3_specs = [
        {
            "match": "Bristol City - Charlton Athletic",
            "competition": "ENG II Divisione U21",
            "kickoff": "2026-10-06 14:00 CEST",
            "market_family": "UNDER_OVER_MATCH",
            "mkt_query": "UNDER/OVER",
            "line_query": "U/O 2.5",
            "sel_query": "OVER",
            "market_label": "Under/Over 2.5 [OVER]",
            "est_p": 0.750,
            "rationale": "Inghilterra U21 a ritmi altissimi; Over 1.5 a 1.05 segnala aspettativa di almeno 3-4 gol complessivi."
        },
        {
            "match": "Colchester United U21 - Swansea City U21",
            "competition": "ENG II Divisione U21",
            "kickoff": "2026-10-06 15:00 CEST",
            "market_family": "DOPPIA_CHANCE",
            "mkt_query": "DOPPIA CHANCE",
            "line_query": "",
            "sel_query": "X2",
            "market_label": "Doppia Chance [X2]",
            "est_p": 0.794,
            "rationale": "Swansea U21 favorita a 1.62 in trasferta; X2 copre pareggio e vittoria corsara."
        },
        {
            "match": "Albion FC Reserve - Nacional de Montevideo",
            "competition": "URU Camp. Riserve I Div.",
            "kickoff": "2026-10-06 15:30 CEST",
            "market_family": "DOPPIA_CHANCE",
            "mkt_query": "DOPPIA CHANCE",
            "line_query": "",
            "sel_query": "X2",
            "market_label": "Doppia Chance [X2]",
            "est_p": 0.821,
            "rationale": "Nacional squadra guida del torneo riserve uruguaiano; X2 protegge su campo ostico."
        },
        {
            "match": "Kazakistan - Isole Far Oer",
            "competition": "INT Nations League",
            "kickoff": "2026-10-06 16:00 CEST",
            "market_family": "MULTIGOAL",
            "mkt_query": "MULTIGOAL",
            "line_query": "MULTIESITI 16 ESITI",
            "sel_query": "1-3",
            "market_label": "MultiGol [1-3]",
            "est_p": 0.716,
            "rationale": "Scontro equilibrato e chiuso in Nations League; il range 1-3 copre l'1-0, 2-0, 2-1, 1-1, 0-1, 0-2."
        }
    ]

    def build_ticket(ticket_id: str, title: str, specs: list[dict], stake: float = 3.0) -> dict:
        legs = []
        tot_odd = 1.0
        tot_p = 1.0

        for sp in specs:
            m_data = catalogs_by_name.get(sp["match"])
            if not m_data:
                print(f"Attenzione: match non trovato {sp['match']}")
                continue
            pk = extract_specific_pick(m_data["data"], sp["mkt_query"], sp["line_query"], sp["sel_query"])
            if not pk:
                print(f"Attenzione: pick non trovata per {sp['match']} ({sp['market_label']})")
                continue
            
            odd = pk["odds"]
            p = sp["est_p"]
            fair_odd = round(1.0 / p, 2)
            edge = round(p * odd - 1.0, 3)
            score = sweet_spot_score(p, odd)

            legs.append({
                "match": sp["match"],
                "competition": sp["competition"],
                "kickoff": sp["kickoff"],
                "market_family": sp["market_family"],
                "market": sp["market_label"],
                "selection": pk["selection"],
                "odds": odd,
                "probability": p,
                "fair_odd": fair_odd,
                "edge": edge,
                "score": round(score, 3),
                "rationale": sp["rationale"]
            })
            tot_odd *= odd
            tot_p *= p

        tot_odd = round(tot_odd, 2)
        tot_p = round(tot_p, 3)
        ev = round(tot_p * tot_odd - 1.0, 3)
        return {
            "id": ticket_id,
            "name": title,
            "stake_eur": stake,
            "total_odds": tot_odd,
            "probability": tot_p,
            "fair_odd": round(1.0 / tot_p, 2) if tot_p > 0 else 0,
            "edge": ev,
            "potential_payout_eur": round(stake * tot_odd, 2),
            "legs": legs
        }

    ticket_1 = build_ticket("TICKET_SNAI_MATTINA_LUNCH", "Ticket 1: Mattina & Pranzo (11:00 - 13:00 CEST)", t1_specs)
    ticket_2 = build_ticket("TICKET_SNAI_ASIA_AMICHEVOLI", "Ticket 2: Asia, Amichevoli & Cina (13:00 - 13:35 CEST)", t2_specs)
    ticket_3 = build_ticket("TICKET_SNAI_POMERIGGIO_U21", "Ticket 3: Pomeriggio, England U21 & Qualificazioni (14:00 - 16:00 CEST)", t3_specs)

    tickets = [ticket_1, ticket_2, ticket_3]

    print("\n[Fase 2] Invio dei 3 Ticket all'Auditor LPU Groq Cloud (openai/gpt-oss-120b)...")
    auditor = GroqAuditor()

    for idx, t in enumerate(tickets, 1):
        print(f"\n  --- Audit Groq Cloud Ticket {idx}: {t['name']} (Quota: {t['total_odds']}) ---")
        audit_payload = [
            {
                "match_name": l["match"],
                "tournament": l["competition"],
                "market": l["market"],
                "book_odd": float(l["odds"]),
                "fair_odd": float(l["fair_odd"]),
                "probability": float(l["probability"]),
                "edge": float(l["edge"]),
                "notes": f"Kickoff: {l['kickoff']} | Famiglia: {l['market_family']} | Tattica: {l['rationale']}"
            }
            for l in t["legs"]
        ]

        audit_res = auditor.audit_ticket(
            title=t["name"],
            legs=audit_payload,
            bankroll=100.0
        )

        t["groq_verdict"] = "APPROVATA" if audit_res.get("approved") else "BOCCIATA"
        t["groq_report"] = audit_res.get("critique", "")
        print(f"    Esito Audit: {t['groq_verdict']}")
        time.sleep(2)

    portfolio = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M CEST"),
        "total_matches_analyzed": len(matches_meta),
        "source": "reports/snai/2026-10-06-fino-16",
        "bankroll_reference": 100.0,
        "tickets": tickets
    }

    out_file = ROOT / "reports/tickets/ticket_snai_daytime_45matches_portfolio.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(portfolio, fp, indent=2, ensure_ascii=False)

    print(f"\n[Fase 3] Portafoglio Diurno salvato con successo in {out_file}!\n")

    for t in tickets:
        print("------------------------------------------------------------------")
        print(f"{t['name']}")
        print(f"Quota Totale: {t['total_odds']} | Prob: {t['probability']*100:.1f}% | EV: {t['edge']*100:+.1f}% | Verdetto: {t['groq_verdict']}")
        print(f"Stake Consigliato: {t['stake_eur']} EUR | Ritorno Potenziale: {t['potential_payout_eur']} EUR")
        for l in t["legs"]:
            print(f"  - [{l['kickoff'][:16]}] {l['competition']} | {l['match']}")
            print(f"    Mercato: {l['market']} @ {l['odds']} (Famiglia: {l['market_family']})")
        print()


if __name__ == "__main__":
    main()

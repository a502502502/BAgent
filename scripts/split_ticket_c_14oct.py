#!/usr/bin/env python3
"""
scripts/split_ticket_c_14oct.py — Split del Ticket C da 9 eventi in due blocchi OFP da 4 eventi:
- Ticket C1: Blocco Alta Probabilità UCL (Quadrupla OFP) (@ 2.84, Stake 5.00 EUR, Pot. 14.20 EUR)
- Ticket C2: Blocco High Edge UCL (Quadrupla OFP) (@ 4.33, Stake 5.00 EUR, Pot. 21.65 EUR)
"""

import sys
import json
import re
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path("C:/Project/BAgent")
MIRROR = Path("C:/Project/bagent-schedine")

OLD_ID = "TICKET_C_MULTIPLA9_INTEGRALE_UCL_5EUR_14OTT"

ticket_c1 = {
    'id': 'TICKET_C1_QUADRUPLA_ALTA_PROB_UCL_5EUR_14OTT',
    'title': 'Ticket C1: Blocco Alta Probabilità UCL (Quadrupla OFP) (@ 2.84)',
    'label': 'In Corso (Stasera)',
    'stake': '5.00 €',
    'odds': '2.84×',
    'potential_win': '14.20 €',
    'booking_code': None,
    'legs': [
        {
            'when': '2026-10-14 18:45 CEST',
            'match': 'LASK vs Liverpool',
            'pick': 'Over 0.5 1°T + Over 0.5 2°T',
            'odd': '1.42',
            'result': 'PENDING',
            'score': 'OFP: AAA | Prob: 75.4% | Edge: +7.07% [STAR]'
        },
        {
            'when': '2026-10-14 18:45 CEST',
            'match': 'Feyenoord vs Como',
            'pick': 'Chance Mix: 1X o Over 1.5',
            'odd': '1.25',
            'result': 'PENDING',
            'score': 'OFP: AAA | Prob: 86.2% | Edge: +7.75% [STAR]'
        },
        {
            'when': '2026-10-14 21:00 CEST',
            'match': 'Aston Villa vs Fenerbahçe',
            'pick': 'MultiGol 1-3 2°Tempo',
            'odd': '1.30',
            'result': 'PENDING',
            'score': 'OFP: AAA | Prob: 80.4% | Edge: +4.52% [STAR]'
        },
        {
            'when': '2026-10-14 21:00 CEST',
            'match': 'Roma vs Real Madrid',
            'pick': 'Chance Mix: X2 o Over 1.5',
            'odd': '1.23',
            'result': 'PENDING',
            'score': 'OFP: AA | Prob: 85.0% | Edge: +4.55% [OCCHIO]'
        }
    ]
}

ticket_c2 = {
    'id': 'TICKET_C2_QUADRUPLA_HIGH_EDGE_UCL_5EUR_14OTT',
    'title': 'Ticket C2: Blocco High Edge UCL (Quadrupla OFP) (@ 4.33)',
    'label': 'In Corso (Stasera ore 21:00)',
    'stake': '5.00 €',
    'odds': '4.33×',
    'potential_win': '21.65 €',
    'booking_code': None,
    'legs': [
        {
            'when': '2026-10-14 21:00 CEST',
            'match': 'Bodø/Glimt vs Borussia Dortmund',
            'pick': 'Over 0.5 1°T + Over 0.5 2°T',
            'odd': '1.44',
            'result': 'PENDING',
            'score': 'OFP: AAA | Prob: 76.8% | Edge: +10.59% [STAR]'
        },
        {
            'when': '2026-10-14 21:00 CEST',
            'match': 'Manchester City vs PSG',
            'pick': 'MultiGol 0-2 1°T + 1-3 2°T',
            'odd': '1.52',
            'result': 'PENDING',
            'score': 'OFP: AA | Prob: 71.5% | Edge: +8.68% [STAR]'
        },
        {
            'when': '2026-10-14 21:00 CEST',
            'match': 'Slovan Bratislava vs Stoccarda',
            'pick': 'X2 + MultiGol 2-5',
            'odd': '1.43',
            'result': 'PENDING',
            'score': 'OFP: AAA | Prob: 74.2% | Edge: +6.11% [STAR]'
        },
        {
            'when': '2026-10-14 21:00 CEST',
            'match': 'Real Betis vs Porto',
            'pick': 'Chance Mix: X o GG',
            'odd': '1.38',
            'result': 'PENDING',
            'score': 'OFP: AAA | Prob: 77.1% | Edge: +6.40% [STAR]'
        }
    ]
}

FULL_TICKET_C1 = {
    "ticket_id": "TICKET_C1_QUADRUPLA_ALTA_PROB_UCL_5EUR_14OTT",
    "name": "Ticket C1: Blocco Alta Probabilità UCL (Quadrupla OFP)",
    "title": "Ticket C1: Blocco Alta Probabilità UCL (Quadrupla OFP) (@ 2.84)",
    "bookmaker": "Netwin",
    "type": "Quadrupla OFP Alta Probabilità",
    "status": "PENDING",
    "placed_at": "2026-10-14 18:45 CEST",
    "created_at": "2026-10-14T17:25:00+02:00",
    "date_created": "2026-10-14 17:25:00",
    "stake": 5.0,
    "stake_eur": 5.0,
    "bonus": 0.0,
    "total_odds": 2.84,
    "potential_win": 14.20,
    "potential_payout_eur": 14.20,
    "net_profit_eur": 9.20,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "Blocco 1 split da Ticket C: 4 eventi ad altissima probabilità intrinseca (LASK, Feyenoord, Aston Villa, Roma-Real). Quota 2.84x.",
    "legs": [
        {
            "match": "LASK vs Liverpool",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 18:45 CEST",
            "market": "Over 0.5 1°T + Over 0.5 2°T",
            "selection": "SI",
            "odds": 1.42,
            "status": "PENDING",
            "score": "OFP: AAA | Prob: 75.4% | Edge: +7.07% [STAR]"
        },
        {
            "match": "Feyenoord vs Como",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 18:45 CEST",
            "market": "Chance Mix: 1X o Over 1.5",
            "selection": "SI",
            "odds": 1.25,
            "status": "PENDING",
            "score": "OFP: AAA | Prob: 86.2% | Edge: +7.75% [STAR]"
        },
        {
            "match": "Aston Villa vs Fenerbahçe",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "MultiGol 1-3 2°Tempo",
            "selection": "SI",
            "odds": 1.30,
            "status": "PENDING",
            "score": "OFP: AAA | Prob: 80.4% | Edge: +4.52% [STAR]"
        },
        {
            "match": "Roma vs Real Madrid",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "Chance Mix: X2 o Over 1.5",
            "selection": "SI",
            "odds": 1.23,
            "status": "PENDING",
            "score": "OFP: AA | Prob: 85.0% | Edge: +4.55% [OCCHIO]"
        }
    ]
}

FULL_TICKET_C2 = {
    "ticket_id": "TICKET_C2_QUADRUPLA_HIGH_EDGE_UCL_5EUR_14OTT",
    "name": "Ticket C2: Blocco High Edge UCL (Quadrupla OFP)",
    "title": "Ticket C2: Blocco High Edge UCL (Quadrupla OFP) (@ 4.33)",
    "bookmaker": "Netwin",
    "type": "Quadrupla OFP High Edge",
    "status": "PENDING",
    "placed_at": "2026-10-14 21:00 CEST",
    "created_at": "2026-10-14T17:25:00+02:00",
    "date_created": "2026-10-14 17:25:00",
    "stake": 5.0,
    "stake_eur": 5.0,
    "bonus": 0.0,
    "total_odds": 4.33,
    "potential_win": 21.65,
    "potential_payout_eur": 21.65,
    "net_profit_eur": 16.65,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "Blocco 2 split da Ticket C: 4 eventi serali 21:00 CEST a massimo edge matematico (Bodø, City-PSG, Slovan-Stuttgart, Betis-Porto). Quota 4.33x.",
    "legs": [
        {
            "match": "Bodø/Glimt vs Borussia Dortmund",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "Over 0.5 1°T + Over 0.5 2°T",
            "selection": "SI",
            "odds": 1.44,
            "status": "PENDING",
            "score": "OFP: AAA | Prob: 76.8% | Edge: +10.59% [STAR]"
        },
        {
            "match": "Manchester City vs PSG",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "MultiGol 0-2 1°T + 1-3 2°T",
            "selection": "SI",
            "odds": 1.52,
            "status": "PENDING",
            "score": "OFP: AA | Prob: 71.5% | Edge: +8.68% [STAR]"
        },
        {
            "match": "Slovan Bratislava vs Stoccarda",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "X2 + MultiGol 2-5",
            "selection": "SI",
            "odds": 1.43,
            "status": "PENDING",
            "score": "OFP: AAA | Prob: 74.2% | Edge: +6.11% [STAR]"
        },
        {
            "match": "Real Betis vs Porto",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "Chance Mix: X o GG",
            "selection": "SI",
            "odds": 1.38,
            "status": "PENDING",
            "score": "OFP: AAA | Prob: 77.1% | Edge: +6.40% [STAR]"
        }
    ]
}


def update_portal(target_dir: Path, is_mirror: bool = False):
    if is_mirror:
        sj_path = target_dir / "schedine.json"
        sh_path = target_dir / "index.html"
    else:
        sj_path = target_dir / "portal" / "schedine.json"
        sh_path = target_dir / "portal" / "schedine.html"
    
    if not sj_path.exists():
        print(f"File non trovato: {sj_path}")
        return

    sj = json.loads(sj_path.read_text(encoding="utf-8"))
    present = sj.get("present", [])
    # Filtra via il vecchio Ticket C da 9 partite
    present = [t for t in present if t.get("id") not in [OLD_ID, ticket_c1["id"], ticket_c2["id"]]]
    present.extend([ticket_c1, ticket_c2])
    sj["present"] = present
    sj["generated_at"] = datetime.now().isoformat()
    
    compact_json = json.dumps(sj, ensure_ascii=False)
    pretty_json = json.dumps(sj, indent=2, ensure_ascii=False)
    
    sj_path.write_text(pretty_json, encoding="utf-8")
    print(f"Aggiornato {sj_path} con {len(present)} ticket attivi stasera.")

    if sh_path.exists():
        html_content = sh_path.read_text(encoding="utf-8")
        html_updated = re.sub(
            r'(<script type="application/json" id="boot">)(.*?)(</script>)',
            rf'\g<1>{compact_json}\g<3>',
            html_content,
            flags=re.DOTALL
        )
        sh_path.write_text(html_updated, encoding="utf-8")
        print(f"Aggiornato {sh_path}.")


def update_active_user_tickets():
    act_path = ROOT / "data" / "active_user_tickets.json"
    if not act_path.exists():
        return
    data = json.loads(act_path.read_text(encoding="utf-8"))
    data = [t for t in data if t.get("ticket_id") not in [OLD_ID, FULL_TICKET_C1["ticket_id"], FULL_TICKET_C2["ticket_id"]]]
    data.extend([FULL_TICKET_C1, FULL_TICKET_C2])
    act_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Aggiornato {act_path} con {len(data)} ticket totali.")


def main():
    print("Aggiornamento split Ticket C -> C1 (@2.84) e C2 (@4.33)...")
    update_active_user_tickets()
    update_portal(ROOT, is_mirror=False)
    if MIRROR.exists():
        update_portal(MIRROR, is_mirror=True)
    print("Completato con successo!")


if __name__ == "__main__":
    main()

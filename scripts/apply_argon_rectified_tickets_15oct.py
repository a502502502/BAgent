#!/usr/bin/env python3
"""
scripts/apply_argon_rectified_tickets_15oct.py — Applicazione Schedine UEL & UECL Rettificate da Gemini Argon (15 Ottobre 2026).

Applica le correzioni dell'Adversarial Auditor:
1. Ticket Core Blindato (@ 2.96, Stake 20.00 EUR):
   - Salisburgo vs AC Milan: X2 + Over 1.5 @ 1.48 (18:45 CEST)
   - Atalanta vs Pafos: 1 + Over 1.5 @ 1.38 (21:00 CEST)
   - SL Benfica vs Celtic FC: 1X + Over 1.5 @ 1.45 (21:00 CEST)

2. Ticket Satellite Ortogonale (@ 4.60, Stake 5.00 EUR):
   - Hoffenheim vs Besiktas: Gol + Over 2.5 @ 1.75 (21:00 CEST)
   - Lech Poznan vs Bayer Leverkusen: Over 2.5 @ 1.62 (21:00 CEST)
   - Ajax vs Maccabi Tel Aviv: 1X + MultiGol 2-5 @ 1.62 (21:00 CEST)
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

CORE_ID = "TICKET_CORE_ROCKET_UEL_UECL_20EUR_15OTT"
SATELLITE_ID = "TICKET_SATELLITE_MOLTIPLICATORE_UEL_5EUR_15OTT"

# 1. Card per portal/schedine.json
CORE_CARD = {
    "id": CORE_ID,
    "title": "Ticket Core Blindato: La Tripla d Acciaio UEL & UECL (@ 2.96)",
    "label": "In Programma (Oggi ore 18:45)",
    "stake": "20.00 €",
    "odds": "2.96×",
    "potential_win": "59.20 €",
    "booking_code": None,
    "legs": [
        {
            "when": "2026-10-15 18:45 CEST",
            "match": "Salisburgo vs AC Milan",
            "pick": "X2 + Over 1.5",
            "odd": "1.48",
            "result": "PENDING",
            "score": "OFP: AAA | Argon Certified | Elimina ceiling 4 gol, copre pareggio e vittoria esterna"
        },
        {
            "when": "2026-10-15 21:00 CEST",
            "match": "Atalanta vs Pafos",
            "pick": "1 + Over 1.5",
            "odd": "1.38",
            "result": "PENDING",
            "score": "OFP: AAA | Argon Certified | Gewiss Stadium, Dea vince con almeno 2 gol totali"
        },
        {
            "when": "2026-10-15 21:00 CEST",
            "match": "SL Benfica vs Celtic FC",
            "pick": "1X + Over 1.5",
            "odd": "1.45",
            "result": "PENDING",
            "score": "OFP: AAA | Argon Certified | Fattore Da Luz, imbattuto in casa con almeno 2 reti"
        }
    ]
}

SATELLITE_CARD = {
    "id": SATELLITE_ID,
    "title": "Ticket Satellite Ortogonale: Tripla Alta Quota UEL & UECL (@ 4.60)",
    "label": "In Programma (Oggi ore 21:00)",
    "stake": "5.00 €",
    "odds": "4.60×",
    "potential_win": "23.00 €",
    "booking_code": None,
    "legs": [
        {
            "when": "2026-10-15 21:00 CEST",
            "match": "Hoffenheim vs Besiktas",
            "pick": "Gol + Over 2.5",
            "odd": "1.75",
            "result": "PENDING",
            "score": "OFP: AAA | Argon Certified | PreZero Arena, ritmi alti e difese scoperte"
        },
        {
            "when": "2026-10-15 21:00 CEST",
            "match": "Lech Poznan vs Bayer Leverkusen",
            "pick": "Over 2.5",
            "odd": "1.62",
            "result": "PENDING",
            "score": "OFP: AAA | Argon Certified | Leverkusen all attacco, slegato da 1X2 su campo pesante"
        },
        {
            "when": "2026-10-15 21:00 CEST",
            "match": "Ajax vs Maccabi Tel Aviv",
            "pick": "1X + MultiGol 2-5",
            "odd": "1.62",
            "result": "PENDING",
            "score": "OFP: AA | Argon Certified | 100% Ortogonale da Core, Johan Cruijff Arena dominante"
        }
    ]
}

# 2. Oggetti per data/active_user_tickets.json
FULL_CORE = {
    "ticket_id": CORE_ID,
    "name": "Ticket Core Blindato: La Tripla d Acciaio UEL & UECL (@ 2.96)",
    "title": "Ticket Core Blindato: La Tripla d Acciaio UEL & UECL (@ 2.96)",
    "bookmaker": "Netwin",
    "type": "Tripla Core Macro 70%",
    "status": "PENDING",
    "placed_at": "2026-10-15 18:45 CEST",
    "created_at": "2026-10-15T09:30:00+02:00",
    "date_created": "2026-10-15 09:30:00",
    "stake": 20.0,
    "stake_eur": 20.0,
    "bonus": 0.0,
    "total_odds": 2.96,
    "potential_win": 59.20,
    "potential_payout_eur": 59.20,
    "net_profit_eur": 39.20,
    "settled": False,
    "profit_loss_eur": 0.0,
    "notes": "Ticket Core validato da Gemini Argon: eliminati tetti gol rischiosi su Milan e convertito Pafos in 1+Over 1.5.",
    "legs": CORE_CARD["legs"]
}

FULL_SATELLITE = {
    "ticket_id": SATELLITE_ID,
    "name": "Ticket Satellite Ortogonale: Tripla Alta Quota UEL & UECL (@ 4.60)",
    "title": "Ticket Satellite Ortogonale: Tripla Alta Quota UEL & UECL (@ 4.60)",
    "bookmaker": "Netwin",
    "type": "Tripla Satellite 30%",
    "status": "PENDING",
    "placed_at": "2026-10-15 21:00 CEST",
    "created_at": "2026-10-15T09:30:00+02:00",
    "date_created": "2026-10-15 09:30:00",
    "stake": 5.0,
    "stake_eur": 5.0,
    "bonus": 0.0,
    "total_odds": 4.60,
    "potential_win": 23.00,
    "potential_payout_eur": 23.00,
    "net_profit_eur": 18.00,
    "settled": False,
    "profit_loss_eur": 0.0,
    "notes": "Ticket Satellite 100% ortogonale dal Core certificato da Gemini Argon (Regole #83 e #86). Zero partite duplicate.",
    "legs": SATELLITE_CARD["legs"]
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
    
    # Rimuovi le vecchie versioni di Core e Satellite
    present = [t for t in present if t.get("id") not in [CORE_ID, SATELLITE_ID]]
    # Inserisci le versioni rettificate in cima
    present.insert(0, SATELLITE_CARD)
    present.insert(0, CORE_CARD)
    
    sj["present"] = present
    sj["generated_at"] = datetime.now().isoformat()
    
    compact_json = json.dumps(sj, ensure_ascii=False)
    pretty_json = json.dumps(sj, indent=2, ensure_ascii=False)
    
    sj_path.write_text(pretty_json, encoding="utf-8")
    print(f"Aggiornato {sj_path} con i 2 ticket rettificati da Argon.")

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
    data = [t for t in data if t.get("ticket_id") not in [CORE_ID, SATELLITE_ID]]
    data.insert(0, FULL_SATELLITE)
    data.insert(0, FULL_CORE)
    act_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Aggiornato {act_path} con {len(data)} ticket totali.")


def main():
    print("=" * 80)
    print("APPLICAZIONE SCHEDINE RETTIFICATE DA GEMINI ARGON (15 OTTOBRE 2026)")
    print("=" * 80)
    update_active_user_tickets()
    update_portal(ROOT, is_mirror=False)
    if MIRROR.exists():
        update_portal(MIRROR, is_mirror=True)
    print("\nApplicazione completata con successo!")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scripts/register_trio_tickets_15oct.py — Registrazione Ufficiale delle 3 Schedine di Oggi (15 Ottobre 2026).

Le 3 Schedine Certificate per UEL & UECL:
1. Ticket Core Blindato: La Tripla d Acciaio UEL & UECL (@ 2.96, Stake 20.00 EUR)
2. Ticket Satellite Ortogonale: Tripla Alta Quota UEL & UECL (@ 4.60, Stake 5.00 EUR)
3. Ticket Precisione: La Tripla Chirurgica UEL & UECL (Tiri & Corner) (@ 3.09, Stake 10.00 EUR)
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

TICKET_1_CORE = {
    "ticket_id": "TICKET_CORE_ROCKET_UEL_UECL_20EUR_15OTT",
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
    "legs": [
        {
            "match": "Salisburgo vs AC Milan",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 18:45 CEST",
            "market": "X2 + U/O 1.5 : X2 + OV",
            "selection": "X2 + OV",
            "odds": 1.48,
            "status": "PENDING",
            "score": "OFP: AAA | Argon Certified | Elimina ceiling 4 gol, copre pareggio e vittoria esterna"
        },
        {
            "match": "Atalanta vs Pafos",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "1X2 + U/O 1.5 : 1 + OV",
            "selection": "1 + OV",
            "odds": 1.38,
            "status": "PENDING",
            "score": "OFP: AAA | Argon Certified | Gewiss Stadium, Dea vince con almeno 2 gol totali"
        },
        {
            "match": "SL Benfica vs Celtic FC",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "1X + U/O 1.5 : 1X + OV",
            "selection": "1X + OV",
            "odds": 1.45,
            "status": "PENDING",
            "score": "OFP: AAA | Argon Certified | Fattore Da Luz, imbattuto in casa con almeno 2 reti"
        }
    ]
}

TICKET_2_SATELLITE = {
    "ticket_id": "TICKET_SATELLITE_MOLTIPLICATORE_UEL_5EUR_15OTT",
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
    "legs": [
        {
            "match": "Hoffenheim vs Besiktas",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "GG/NG + U/O 2.5 : GG + OV",
            "selection": "GG + OV",
            "odds": 1.75,
            "status": "PENDING",
            "score": "OFP: AAA | Argon Certified | PreZero Arena, ritmi alti e difese scoperte"
        },
        {
            "match": "Lech Poznan vs Bayer Leverkusen",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 2.5 : OVER",
            "selection": "OVER",
            "odds": 1.62,
            "status": "PENDING",
            "score": "OFP: AAA | Argon Certified | Leverkusen all attacco, slegato da 1X2 su campo pesante"
        },
        {
            "match": "Ajax vs Maccabi Tel Aviv",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "1X + MultiGol 2-5 : SI",
            "selection": "SI",
            "odds": 1.62,
            "status": "PENDING",
            "score": "OFP: AA | Argon Certified | 100% Ortogonale da Core, Johan Cruijff Arena dominante"
        }
    ]
}

TICKET_3_CHIRURGICO = {
    "ticket_id": "TICKET_TRIPLA_CHIRURGICA_GEMS_10EUR_15OTT",
    "name": "Ticket Precisione: La Tripla Chirurgica UEL & UECL (Tiri & Corner) (@ 3.09)",
    "title": "Ticket Precisione: La Tripla Chirurgica UEL & UECL (Tiri & Corner) (@ 3.09)",
    "bookmaker": "Netwin",
    "type": "Tripla Chirurgica Asimmetrica (Tiri & Corner)",
    "status": "PENDING",
    "placed_at": "2026-10-15 21:00 CEST",
    "created_at": "2026-10-15T10:20:00+02:00",
    "date_created": "2026-10-15 10:20:00",
    "stake": 10.0,
    "stake_eur": 10.0,
    "bonus": 0.0,
    "total_odds": 3.09,
    "potential_win": 30.91,
    "potential_payout_eur": 30.91,
    "net_profit_eur": 20.91,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": None,
    "notes": "Schedina chirurgica di precisione validata da Gemini Argon: tiri in porta Atalanta, corner Benfica e la gemma tiri in porta Ajax ad Amsterdam. Quota 3.09x.",
    "legs": [
        {
            "match": "Atalanta vs Pafos",
            "tournament": "Club Internazionali | UEFA Conference League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 4.5 Tiri in Porta Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.40,
            "status": "PENDING",
            "score": "OFP: AAA | Volume balistico Gewiss (media 6.8 tiri nello specchio)"
        },
        {
            "match": "SL Benfica vs Celtic FC",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 4.5 Corner Squadra 1 (esc.TS) : OVER",
            "selection": "OVER",
            "odds": 1.38,
            "status": "PENDING",
            "score": "OFP: AAA | Asimmetria corsie esterne Da Luz (>5 corner nel 78% dei match europei)"
        },
        {
            "match": "Ajax vs Maccabi Tel Aviv",
            "tournament": "Club Internazionali | UEFA Europa League",
            "kickoff": "2026-10-15 21:00 CEST",
            "market": "U/O 5.5 Tiri in Porta Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.60,
            "status": "PENDING",
            "score": "OFP: AAA | Gemma Chirurgica Farioli (media 7.8 tiri in porta)"
        }
    ]
}

# Cards per il portale
PORTAL_CARDS = [
    {
        "id": TICKET_1_CORE["ticket_id"],
        "title": TICKET_1_CORE["title"],
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
    },
    {
        "id": TICKET_2_SATELLITE["ticket_id"],
        "title": TICKET_2_SATELLITE["title"],
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
    },
    {
        "id": TICKET_3_CHIRURGICO["ticket_id"],
        "title": TICKET_3_CHIRURGICO["title"],
        "label": "In Programma (Oggi ore 21:00)",
        "stake": "10.00 €",
        "odds": "3.09×",
        "potential_win": "30.91 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Atalanta vs Pafos",
                "pick": "Atalanta Over 4.5 Tiri in Porta",
                "odd": "1.40",
                "result": "PENDING",
                "score": "OFP: AAA | Volume balistico Gewiss (media 6.8 tiri nello specchio)"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "SL Benfica vs Celtic FC",
                "pick": "Benfica Over 4.5 Corner",
                "odd": "1.38",
                "result": "PENDING",
                "score": "OFP: AAA | Asimmetria corsie esterne Da Luz (>5 corner nel 78% dei match europei)"
            },
            {
                "when": "2026-10-15 21:00 CEST",
                "match": "Ajax vs Maccabi Tel Aviv",
                "pick": "Ajax Over 5.5 Tiri in Porta",
                "odd": "1.60",
                "result": "PENDING",
                "score": "OFP: AAA | Gemma Chirurgica Farioli (media 7.8 tiri in porta)"
            }
        ]
    }
]


def update_portal(target_dir: Path, is_mirror: bool = False):
    if is_mirror:
        sj_path = target_dir / "schedine.json"
        sh_path = target_dir / "index.html"
    else:
        sj_path = target_dir / "portal" / "schedine.json"
        sh_path = target_dir / "portal" / "schedine.html"

    if not sj_path.exists():
        return

    sj = json.loads(sj_path.read_text(encoding="utf-8"))
    present = sj.get("present", [])
    
    # Rimuovi eventuali istanze esistenti delle 3 schedine
    ids_to_register = [c["id"] for c in PORTAL_CARDS]
    present = [t for t in present if t.get("id") not in ids_to_register]
    
    # Inserisci le 3 schedine in cima
    for c in reversed(PORTAL_CARDS):
        present.insert(0, c)
        
    sj["present"] = present
    sj["generated_at"] = datetime.now().isoformat()
    
    compact_json = json.dumps(sj, ensure_ascii=False)
    pretty_json = json.dumps(sj, indent=2, ensure_ascii=False)
    
    sj_path.write_text(pretty_json, encoding="utf-8")
    print(f"Aggiornato {sj_path} con le 3 schedine di oggi.")

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
    ids_to_register = [TICKET_1_CORE["ticket_id"], TICKET_2_SATELLITE["ticket_id"], TICKET_3_CHIRURGICO["ticket_id"]]
    data = [t for t in data if t.get("ticket_id") not in ids_to_register]
    
    data.insert(0, TICKET_3_CHIRURGICO)
    data.insert(0, TICKET_2_SATELLITE)
    data.insert(0, TICKET_1_CORE)
    
    act_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Aggiornato {act_path} con {len(data)} ticket totali.")


def main():
    print("=" * 80)
    print("REGISTRAZIONE UFFICIALE DELLE 3 SCHEDINE UEL & UECL (15 OTTOBRE 2026)")
    print("=" * 80)
    update_active_user_tickets()
    update_portal(ROOT, is_mirror=False)
    if MIRROR.exists():
        update_portal(MIRROR, is_mirror=True)
    print("\nRegistrazione delle 3 schedine completata con successo!")


if __name__ == "__main__":
    main()

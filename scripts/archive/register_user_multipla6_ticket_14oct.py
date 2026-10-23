#!/usr/bin/env python3
"""
scripts/register_user_multipla6_ticket_14oct.py — Registrazione Ufficiale Ticket Personale Utente (Multipla 6 UCL 14 Ottobre 2026).

Ticket: La Multipla 6 UCL (@ 6.46)
- Slovan Bratislava vs Stoccarda: MultiGol 1-4 Ospite @ 1.18
- Aston Villa vs Fenerbahce: Aston Villa Over 4.5 Tiri in Porta @ 1.37
- Roma vs Real Madrid: X2 + Over 1.5 @ 1.50
- Shakhtar Donetsk vs AEK Atene: Shakhtar Over 3.5 Corner @ 1.38
- Manchester City vs PSG: Gol / Entrambe a Segno @ 1.38
- Real Betis vs Porto: Porto Over 1.5 Cartellini @ 1.40
- Quota: 6.46x | Stake: 10.00 EUR | Bonus: 3.88 EUR | Payout: 68.53 EUR | Kickoff: 21:00 CEST
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

TICKET_ID = "TICKET_USER_MULTIPLA6_UCL_10EUR_14OTT"
BOOKING_CODE = None

# 1. Oggetto completo per active_user_tickets.json
FULL_TICKET = {
    "ticket_id": TICKET_ID,
    "name": "Ticket Personale: La Multipla 6 UCL (@ 6.46)",
    "title": "Ticket Personale: La Multipla 6 UCL (6 Eventi 21:00 CEST) (@ 6.46)",
    "bookmaker": "Netwin",
    "type": "Multipla 6 UCL Valore & Macro",
    "status": "PENDING",
    "placed_at": "2026-10-14 21:00 CEST",
    "created_at": "2026-10-14T16:50:00+02:00",
    "date_created": "2026-10-14 16:50:00",
    "stake": 10.0,
    "stake_eur": 10.0,
    "bonus": 3.88,
    "total_odds": 6.46,
    "potential_win": 68.53,
    "potential_payout_eur": 68.53,
    "net_profit_eur": 58.53,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": BOOKING_CODE,
    "netwin_ticket_id": BOOKING_CODE,
    "netwin_url": "",
    "notes": "Multipla a 6 eventi giocata dall'utente: 3 gemme a forte EV+ (Porto Over 1.5 Cartellini +9.9%, Shakhtar Over 3.5 Corner +5.6%, Villa Over 4.5 Tiri Porta +2.1%) con City-PSG Gol, Slovan-Stuttgart MultiGol 1-4 Ospite e Roma-Real Madrid X2+Over 1.5.",
    "legs": [
        {
            "match": "Slovan Bratislava vs Stoccarda",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "MultiGol 1-4 Ospite : SI",
            "selection": "SI",
            "odds": 1.18,
            "status": "PENDING",
            "score": "Prob Stimata: 87.5% | Stoccarda atteso 1-3 gol"
        },
        {
            "match": "Aston Villa vs Fenerbahce",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "U/O 4.5 Tiri in Porta Squadra 1 : OVER",
            "selection": "OVER",
            "odds": 1.37,
            "status": "PENDING",
            "score": "EV: +2.1% | Media Aston Villa al Villa Park: 5.9 Tiri in Porta | Prob: 74.5%"
        },
        {
            "match": "Roma vs Real Madrid",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "X2 + U/O 1.5 : X2 + OV",
            "selection": "X2 + OV",
            "odds": 1.50,
            "status": "PENDING",
            "score": "Combo Real Madrid doppia chance + Over 1.5"
        },
        {
            "match": "Shakhtar Donetsk vs AEK Atene",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "U/O 3.5 Corner Squadra 1 (esc.TS) : OVER",
            "selection": "OVER",
            "odds": 1.38,
            "status": "PENDING",
            "score": "EV: +5.6% | Shakhtar Donetsk dominante sulle fasce, media 5.4 Corner | Prob: 76.5%"
        },
        {
            "match": "Manchester City vs PSG",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "G/NG : Gol",
            "selection": "Gol",
            "odds": 1.38,
            "status": "PENDING",
            "score": "Prob Stimata: 74.0% | Big match Etihad, potenziale offensivo d'élite"
        },
        {
            "match": "Real Betis vs Porto",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 21:00 CEST",
            "market": "U/O 1.5 Cartellini Squadra 2 : OVER",
            "selection": "OVER",
            "odds": 1.40,
            "status": "PENDING",
            "score": "EV: +9.9% | Porto media 2.75 Cartellini trasferta | Prob: 78.5% [VALORE ELEVATO]"
        }
    ]
}

# 2. Card per portal/schedine.json
PORTAL_CARD = {
    "id": TICKET_ID,
    "title": "Ticket Personale: La Multipla 6 UCL (@ 6.46)",
    "label": "In Corso (Stasera ore 21:00)",
    "stake": "10.00 €",
    "bonus": "3.88 €",
    "odds": "6.46×",
    "potential_win": "68.53 €",
    "booking_code": BOOKING_CODE,
    "legs": [
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Slovan Bratislava vs Stoccarda",
            "pick": "MultiGol 1-4 Ospite (Stoccarda)",
            "odd": "1.18",
            "result": "PENDING",
            "score": "Prob: 87.5% | Stoccarda 1-4 Gol"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Aston Villa vs Fenerbahce",
            "pick": "Aston Villa Over 4.5 Tiri in Porta",
            "odd": "1.37",
            "result": "PENDING",
            "score": "EV: +2.1% | Media Casa: 5.9 Tiri in Porta"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Roma vs Real Madrid",
            "pick": "X2 + Over 1.5",
            "odd": "1.50",
            "result": "PENDING",
            "score": "Combo Doppia Chance Real Madrid + Over 1.5"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Shakhtar Donetsk vs AEK Atene",
            "pick": "Shakhtar Over 3.5 Corner",
            "odd": "1.38",
            "result": "PENDING",
            "score": "EV: +5.6% | Media Corner Shakhtar: 5.4"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Manchester City vs PSG",
            "pick": "Goal / Entrambe Segnano",
            "odd": "1.38",
            "result": "PENDING",
            "score": "Big Match Etihad | Entrambe a Segno"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Real Betis vs Porto",
            "pick": "Porto Over 1.5 Cartellini",
            "odd": "1.40",
            "result": "PENDING",
            "score": "EV: +9.9% | Media Cartellini Porto: 2.75"
        }
    ]
}


def update_active_user_tickets():
    act_path = ROOT / "data" / "active_user_tickets.json"
    data = json.loads(act_path.read_text(encoding="utf-8")) if act_path.exists() else []
    # Rimuovi se già presente
    data = [t for t in data if t.get("ticket_id") != TICKET_ID]
    # Inserisci dopo la doppia diamante (o in cima)
    insert_idx = 1 if len(data) > 0 and data[0].get("ticket_id") == "TICKET_USER_DOPPIA_DIAMANTE_20EUR_14OTT" else 0
    data.insert(insert_idx, FULL_TICKET)
    act_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Aggiornato {act_path} con {len(data)} ticket totali.")


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
    present = [c for c in present if c.get("id") != TICKET_ID]
    insert_idx = 1 if len(present) > 0 and present[0].get("id") == "TICKET_USER_DOPPIA_DIAMANTE_20EUR_14OTT" else 0
    present.insert(insert_idx, PORTAL_CARD)
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


def main():
    print("=" * 80)
    print("BAGENT — REGISTRAZIONE TICKET PERSONALE UTENTE (MULTIPLA 6 UCL 14/10)")
    print("=" * 80)

    # 1. Update data/active_user_tickets.json
    update_active_user_tickets()

    # 2. Update portal locale
    update_portal(ROOT, is_mirror=False)

    # 3. Update mirror bagent-schedine
    if MIRROR.exists():
        update_portal(MIRROR, is_mirror=True)

    print("\nRegistrazione completata con successo!")


if __name__ == "__main__":
    main()

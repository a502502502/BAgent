#!/usr/bin/env python3
"""
scripts/register_user_diamante_ticket_14oct.py — Registrazione Ufficiale Ticket Personale Utente (14 Ottobre 2026).

Ticket: La Doppia Diamante UCL
- Feyenoord vs Como: Como Over 4.5 Corner @ 1.96 (EV +31.3%)
- LASK Linz vs Liverpool: Florian Wirtz (o Sostituto) Gol o Assist @ 1.90 (EV +21.6%)
- Quota: 3.72x | Stake: 20.00 EUR | Payout: 74.48 EUR | Netwin ID: DF07EA0A0E3260137E01
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

TICKET_ID = "TICKET_USER_DOPPIA_DIAMANTE_20EUR_14OTT"
BOOKING_CODE = "DF07EA0A0E3260137E01"

# 1. Oggetto completo per active_user_tickets.json
FULL_TICKET = {
    "ticket_id": TICKET_ID,
    "name": "Ticket Personale: La Doppia Diamante UCL (Wirtz + Como Corner)",
    "title": "Ticket Personale: La Doppia Diamante UCL (Como Corner + Wirtz Gol/Assist) (@ 3.72)",
    "bookmaker": "Netwin",
    "type": "Doppia Diamante Player Props & Flussi Asimmetrici",
    "status": "PENDING",
    "placed_at": "2026-10-14 18:45 CEST",
    "created_at": "2026-10-14T16:48:00+02:00",
    "date_created": "2026-10-14 16:48:00",
    "stake": 20.0,
    "stake_eur": 20.0,
    "bonus": 0.0,
    "total_odds": 3.72,
    "potential_win": 74.48,
    "potential_payout_eur": 74.48,
    "net_profit_eur": 54.48,
    "settled": False,
    "profit_loss_eur": 0.0,
    "booking_code": BOOKING_CODE,
    "netwin_ticket_id": BOOKING_CODE,
    "netwin_url": f"https://www.netwin.it/scommesse/loadbet?ticketId={BOOKING_CODE}",
    "notes": "Doppia Diamante a massimo EV: Como Over 4.5 Corner @ 1.96 (EV +31.3%) + Wirtz Gol o Assist @ 1.90 (EV +21.6%). EV Combinato +59.5%.",
    "legs": [
        {
            "match": "Feyenoord vs Como",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 18:45 CEST",
            "market": "U/O 4.5 Corner Squadra 2 (esc.TS) : OVER",
            "selection": "OVER",
            "odds": 1.96,
            "status": "PENDING",
            "score": "EV: +31.3% | Media Como: 7.8 Corner | Prob: 67.0% [DIAMOND]"
        },
        {
            "match": "LASK Linz vs Liverpool",
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": "2026-10-14 18:45 CEST",
            "market": "Wirtz, Florian (Liverpool) o Sostituto Segna o Fa Assist : SI",
            "selection": "SI",
            "odds": 1.90,
            "status": "PENDING",
            "score": "EV: +21.6% | Isak/Gakpo/Szoboszlai Out | Prob: 64.0% [DIAMOND]"
        }
    ]
}

# 2. Card per portal/schedine.json
PORTAL_CARD = {
    "id": TICKET_ID,
    "title": "Ticket Personale: La Doppia Diamante UCL (Como Corner + Wirtz Gol/Assist) (@ 3.72)",
    "label": "In Corso (Stasera)",
    "stake": "20.00 €",
    "odds": "3.72×",
    "potential_win": "74.48 €",
    "booking_code": BOOKING_CODE,
    "legs": [
        {
            "when": "2026-10-14 18:45 CEST",
            "match": "Feyenoord vs Como",
            "pick": "Como Over 4.5 Corner (esc.TS)",
            "odd": "1.96",
            "result": "PENDING",
            "score": "EV: +31.3% | Media Como: 7.8 Corner | Prob: 67.0% [DIAMOND]"
        },
        {
            "when": "2026-10-14 18:45 CEST",
            "match": "LASK Linz vs Liverpool",
            "pick": "Wirtz (o Sostituto) Gol o Assist",
            "odd": "1.90",
            "result": "PENDING",
            "score": "EV: +21.6% | Isak/Gakpo Out | Prob: 64.0% [DIAMOND]"
        }
    ]
}


def update_active_user_tickets():
    act_path = ROOT / "data" / "active_user_tickets.json"
    data = json.loads(act_path.read_text(encoding="utf-8")) if act_path.exists() else []
    # Rimuovi se già presente
    data = [t for t in data if t.get("ticket_id") != TICKET_ID]
    # Inserisci in cima
    data.insert(0, FULL_TICKET)
    act_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Aggiornato {act_path} con {len(data)} ticket totali.")


def update_portal(target_dir: Path):
    sj_path = target_dir / "portal" / "schedine.json"
    sh_path = target_dir / "portal" / "schedine.html"
    
    if not sj_path.exists():
        print(f"File non trovato: {sj_path}")
        return

    sj = json.loads(sj_path.read_text(encoding="utf-8"))
    present = sj.get("present", [])
    present = [c for c in present if c.get("id") != TICKET_ID]
    present.insert(0, PORTAL_CARD)
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
    print("BAGENT — REGISTRAZIONE TICKET PERSONALE UTENTE (DOPPIA DIAMANTE 14/10)")
    print("=" * 80)

    # 1. Update data/active_user_tickets.json
    update_active_user_tickets()

    # 2. Update portal locale
    update_portal(ROOT)

    # 3. Update mirror bagent-schedine
    if MIRROR.exists():
        update_portal(MIRROR)

    print("\nRegistrazione completata con successo!")


if __name__ == "__main__":
    main()

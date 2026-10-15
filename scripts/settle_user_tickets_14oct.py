#!/usr/bin/env python3
"""
scripts/settle_user_tickets_14oct.py — Refertazione e Chiusura Ufficiale Schedine 14 Ottobre 2026.

Risultati Ufficiali Champions League 14/10/2026:
- Feyenoord 3–2 Como (Corners: 4-1)
- LASK 3–6 Liverpool (HT 1-3; Wirtz assist al 37')
- Manchester City 2–4 Paris Saint-Germain (HT 0-3, Cards 1-1, Corners 11-2)
- AS Roma 3–4 Real Madrid (HT 1-1, Cards 3-1, Corners 5-9)
- Aston Villa 6–0 Fenerbahçe (HT 3-0, 2T 3-0, 11 tiri in porta Villa)
- Real Betis 3–2 FC Porto (Cards: 4-3 Porto 3 gialli)
- FK Bodø/Glimt 1–0 Borussia Dortmund (HT 0-0)
- FC Shakhtar Donetsk 3–1 AEK Athens (Corners: 5-2 Shakhtar 5 corners)
- SK Slovan Bratislava 0–3 VfB Stuttgart (HT 0-1)

Esito Ticket Utente 14/10:
- TICKET_USER_MULTIPLA6_UCL_10EUR_14OTT: VINTA (+58.53 € netti, Totale 68.53 €)
- TICKET_USER_DOPPIA_DIAMANTE_20EUR_14OTT: PERSA (-20.00 €)
Bilancio netto utente della serata: +38.53 €!
Nuovo saldo portale: +6.61 € + 38.53 € = +45.14 €!
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

def settle_active_user_tickets():
    act_path = ROOT / "data" / "active_user_tickets.json"
    if not act_path.exists():
        return
    tickets = json.loads(act_path.read_text(encoding="utf-8"))

    for t in tickets:
        tid = t.get("ticket_id")
        if tid == "TICKET_USER_MULTIPLA6_UCL_10EUR_14OTT":
            t["status"] = "WON"
            t["settled"] = True
            t["profit_loss_eur"] = 58.53
            for leg in t.get("legs", []):
                leg["status"] = "WON"
                if "Slovan" in leg["match"]:
                    leg["score"] = "0-3 (FT) | Stoccarda segna 3 gol"
                elif "Aston Villa" in leg["match"]:
                    leg["score"] = "6-0 (FT) | 11 Tiri in Porta Villa"
                elif "Roma" in leg["match"]:
                    leg["score"] = "3-4 (FT) | Real vince + 7 gol totali"
                elif "Shakhtar" in leg["match"]:
                    leg["score"] = "3-1 (FT) | 5 Corner Shakhtar"
                elif "Manchester City" in leg["match"]:
                    leg["score"] = "2-4 (FT) | Entrambe a segno"
                elif "Betis" in leg["match"]:
                    leg["score"] = "3-2 (FT) | 3 Cartellini Porto"

        elif tid == "TICKET_USER_DOPPIA_DIAMANTE_20EUR_14OTT":
            t["status"] = "LOST"
            t["settled"] = True
            t["profit_loss_eur"] = -20.0
            for leg in t.get("legs", []):
                if "Feyenoord" in leg["match"]:
                    leg["status"] = "LOST"
                    leg["score"] = "3-2 (FT) | Solo 1 Corner Como"
                elif "LASK" in leg["match"]:
                    leg["status"] = "WON"
                    leg["score"] = "3-6 (FT) | Assist Wirtz al 37' per Barcola"

    act_path.write_text(json.dumps(tickets, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Aggiornato {act_path} con la refertazione.")


def settle_portal(target_dir: Path, is_mirror: bool = False):
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
    past = sj.get("past", [])

    # IDs da refertare
    settle_ids = [
        "TICKET_USER_MULTIPLA6_UCL_10EUR_14OTT",
        "TICKET_USER_DOPPIA_DIAMANTE_20EUR_14OTT",
        "TICKET_A_CASSAFORTE_UCL_14EUR_14OTT",
        "TICKET_B_GEMME_UCL_6EUR_14OTT",
        "TICKET_C1_QUADRUPLA_ALTA_PROB_UCL_5EUR_14OTT",
        "TICKET_C2_QUADRUPLA_HIGH_EDGE_UCL_5EUR_14OTT"
    ]

    settled_cards = []
    remaining_present = []

    for t in present:
        tid = t.get("id")
        if tid not in settle_ids:
            remaining_present.append(t)
            continue

        if tid == "TICKET_USER_MULTIPLA6_UCL_10EUR_14OTT":
            t["label"] = "Vinta (+58.53 €)"
            for leg in t.get("legs", []):
                leg["result"] = "WON"
                if "Slovan" in leg["match"]:
                    leg["score"] = "0-3 (FT) - 3 Gol Stoccarda"
                elif "Aston Villa" in leg["match"]:
                    leg["score"] = "6-0 (FT) - 11 Tiri in Porta"
                elif "Roma" in leg["match"]:
                    leg["score"] = "3-4 (FT) - X2 + Over 1.5"
                elif "Shakhtar" in leg["match"]:
                    leg["score"] = "3-1 (FT) - 5 Corner Shakhtar"
                elif "Manchester City" in leg["match"]:
                    leg["score"] = "2-4 (FT) - Gol"
                elif "Betis" in leg["match"]:
                    leg["score"] = "3-2 (FT) - 3 Cartellini Porto"
            settled_cards.append(t)

        elif tid == "TICKET_USER_DOPPIA_DIAMANTE_20EUR_14OTT":
            t["label"] = "Persa"
            for leg in t.get("legs", []):
                if "Feyenoord" in leg["match"]:
                    leg["result"] = "LOST"
                    leg["score"] = "3-2 (FT) - 1 Corner Como"
                elif "LASK" in leg["match"]:
                    leg["result"] = "WON"
                    leg["score"] = "3-6 (FT) - Assist Wirtz (37')"
            settled_cards.append(t)

        elif tid == "TICKET_A_CASSAFORTE_UCL_14EUR_14OTT":
            t["label"] = "Vinta (+18.31 €)"
            for leg in t.get("legs", []):
                leg["result"] = "WON"
                if "LASK" in leg["match"]:
                    leg["score"] = "3-6 (HT 1-3) - Over 1T + 2T"
                elif "Feyenoord" in leg["match"]:
                    leg["score"] = "3-2 (FT) - Chance Mix 1X o Over 1.5"
                elif "Aston Villa" in leg["match"]:
                    leg["score"] = "6-0 (2T 3-0) - MultiGol 1-3 2°T"
            settled_cards.append(t)

        elif tid == "TICKET_C1_QUADRUPLA_ALTA_PROB_UCL_5EUR_14OTT":
            t["label"] = "Vinta (+9.20 €)"
            for leg in t.get("legs", []):
                leg["result"] = "WON"
                if "LASK" in leg["match"]:
                    leg["score"] = "3-6 (HT 1-3) - Over 1T + 2T"
                elif "Feyenoord" in leg["match"]:
                    leg["score"] = "3-2 (FT) - Chance Mix"
                elif "Aston Villa" in leg["match"]:
                    leg["score"] = "6-0 (2T 3-0) - MultiGol 2°T"
                elif "Roma" in leg["match"]:
                    leg["score"] = "3-4 (FT) - Chance Mix X2/Over"
            settled_cards.append(t)

        elif tid == "TICKET_B_GEMME_UCL_6EUR_14OTT":
            t["label"] = "Persa"
            for leg in t.get("legs", []):
                leg["result"] = "LOST"
                leg["score"] = "Terminata (Mancata combinazione 1°T)"
            settled_cards.append(t)

        elif tid == "TICKET_C2_QUADRUPLA_HIGH_EDGE_UCL_5EUR_14OTT":
            t["label"] = "Persa"
            for leg in t.get("legs", []):
                if "Bodø" in leg["match"]:
                    leg["result"] = "LOST"
                    leg["score"] = "1-0 (HT 0-0)"
                else:
                    leg["result"] = "WON"
                    leg["score"] = "Rispettata"
            settled_cards.append(t)

    # Aggiorna saldo portale
    # Saldo precedente: +6.61 €
    # Vinti Utente: Multipla6 (+58.53 €), Doppia Diamante (-20.00 €) = +38.53 € netti
    new_profit = 6.61 + 38.53
    sj["profit_label"] = f"+{new_profit:.2f} € (Saldo Netto Aggiornato)"
    sj["present"] = remaining_present
    sj["past"] = settled_cards + past
    sj["generated_at"] = datetime.now().isoformat()

    compact_json = json.dumps(sj, ensure_ascii=False)
    pretty_json = json.dumps(sj, indent=2, ensure_ascii=False)
    sj_path.write_text(pretty_json, encoding="utf-8")
    print(f"Aggiornato {sj_path} con saldo {sj['profit_label']}.")

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
    print("REFERTAZIONE E CHIUSURA SCHEDINE CHAMPIONS LEAGUE 14 OTTOBRE 2026")
    print("=" * 80)
    settle_active_user_tickets()
    settle_portal(ROOT, is_mirror=False)
    if MIRROR.exists():
        settle_portal(MIRROR, is_mirror=True)
    print("\nRefertazione completata con successo!")


if __name__ == "__main__":
    main()

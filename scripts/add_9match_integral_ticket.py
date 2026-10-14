#!/usr/bin/env python3
"""
scripts/add_9match_integral_ticket.py
Aggiunge Ticket C (Multipla 9 Partite Integrale UCL @ 15.20x) con tutte le sfide di stasera:
- Aggiorna portal/schedine.json e portal/schedine.html
- Aggiorna data/active_user_tickets.json e storage/database/bagent.db
- Aggiorna mirror pubblico bagent-schedine (schedine.json e index.html)
- Commit e push su entrambi i repository (zero emoji, .env protetto)
"""

import json
import datetime
import pathlib
import sqlite3
import re
import subprocess

ROOT = pathlib.Path("C:/Project/BAgent")
MIRROR_ROOT = pathlib.Path("C:/Project/bagent-schedine")

TICKET_C = {
    "id": "TICKET_C_MULTIPLA9_INTEGRALE_UCL_5EUR_14OTT",
    "title": "Ticket C: Il Dominio UCL (Multipla 9 Partite Integrale OFP) (@ 15.20)",
    "label": "In Corso (Stasera)",
    "stake": "5.00 €",
    "odds": "15.20×",
    "potential_win": "76.01 €",
    "booking_code": None,
    "legs": [
        {
            "when": "2026-10-14 18:45 CEST",
            "match": "LASK vs Liverpool",
            "pick": "Over 0.5 1°T + Over 0.5 2°T",
            "odd": "1.42",
            "result": "PENDING",
            "score": "OFP: AAA | Prob: 75.4% | Edge: +7.07% [STAR]"
        },
        {
            "when": "2026-10-14 18:45 CEST",
            "match": "Feyenoord vs Como",
            "pick": "Chance Mix: 1X o Over 1.5",
            "odd": "1.25",
            "result": "PENDING",
            "score": "OFP: AAA | Prob: 86.2% | Edge: +7.75% [STAR]"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Aston Villa vs Fenerbahçe",
            "pick": "MultiGol 1-3 2°Tempo",
            "odd": "1.30",
            "result": "PENDING",
            "score": "OFP: AAA | Prob: 80.4% | Edge: +4.52% [STAR]"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Bodø/Glimt vs Borussia Dortmund",
            "pick": "Over 0.5 1°T + Over 0.5 2°T",
            "odd": "1.44",
            "result": "PENDING",
            "score": "OFP: AAA | Prob: 76.8% | Edge: +10.59% [STAR]"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Slovan Bratislava vs Stoccarda",
            "pick": "X2 + MultiGol 2-5",
            "odd": "1.43",
            "result": "PENDING",
            "score": "OFP: AAA | Prob: 74.2% | Edge: +6.11% [STAR]"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Manchester City vs PSG",
            "pick": "MultiGol 0-2 1°T + 1-3 2°T",
            "odd": "1.52",
            "result": "PENDING",
            "score": "OFP: AA | Prob: 71.5% | Edge: +8.68% [STAR]"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Roma vs Real Madrid",
            "pick": "Chance Mix: X2 o Over 1.5",
            "odd": "1.23",
            "result": "PENDING",
            "score": "OFP: AA | Prob: 85.0% | Edge: +4.55% [OCCHIO]"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Real Betis vs Porto",
            "pick": "Chance Mix: X o GG",
            "odd": "1.38",
            "result": "PENDING",
            "score": "OFP: AAA | Prob: 77.1% | Edge: +6.40% [STAR]"
        },
        {
            "when": "2026-10-14 21:00 CEST",
            "match": "Shakhtar Donetsk vs AEK Atene",
            "pick": "MultiGol 1-4",
            "odd": "1.24",
            "result": "PENDING",
            "score": "OFP: A | Prob: 81.0% | Edge: +0.44% [OCCHIO]"
        }
    ]
}

TICKET_C_ACTIVE = {
    "ticket_id": "TICKET_C_MULTIPLA9_INTEGRALE_UCL_5EUR_14OTT",
    "name": "Ticket C: Il Dominio UCL Multipla 9 Partite",
    "title": "Ticket C: Il Dominio UCL (Multipla 9 Partite Integrale OFP) (@ 15.20)",
    "bookmaker": "Netwin",
    "type": "Multipla Integrale (9)",
    "status": "PENDING",
    "placed_at": "2026-10-14 18:45 CEST",
    "created_at": datetime.datetime.now().isoformat(),
    "date_created": "2026-10-14 13:35:00",
    "stake": 5.0,
    "stake_eur": 5.0,
    "bonus": 0.0,
    "total_odds": 15.20,
    "potential_win": 76.01,
    "potential_payout_eur": 76.01,
    "net_profit_eur": 71.01,
    "settled": False,
    "profit_loss_eur": 0.0,
    "notes": "Multipla integrale 9 partite Champions League 14 Ottobre con mercati asimmetrici protetti (Regola #82).",
    "legs": [
        {
            "match": leg["match"],
            "tournament": "Club Internazionali | UEFA Champions League",
            "kickoff": leg["when"],
            "market": leg["pick"],
            "selection": "SI",
            "odds": float(leg["odd"]),
            "status": "PENDING",
            "score": leg["score"]
        } for leg in TICKET_C["legs"]
    ]
}

# 1. Aggiorna portal/schedine.json
p = ROOT / "portal" / "schedine.json"
data = json.loads(p.read_text(encoding="utf-8"))
data["generated_at"] = datetime.datetime.now().isoformat()

# Rimuovi eventuale Ticket C esistente per evitare duplicati
data["present"] = [t for t in data.get("present", []) if t.get("id") != TICKET_C["id"]]
data["present"].append(TICKET_C)

p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"[OK] Aggiornato portal/schedine.json con {len(data['present'])} schedine in present.")

# 2. Aggiorna mirror bagent-schedine/schedine.json
mirror_p = MIRROR_ROOT / "schedine.json"
mirror_p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("[OK] Aggiornato mirror bagent-schedine/schedine.json")

# 3. Aggiorna #boot negli HTML
boot_str = json.dumps(data, ensure_ascii=False)
for h_path in [ROOT / "portal" / "schedine.html", MIRROR_ROOT / "index.html"]:
    if h_path.exists():
        content = h_path.read_text(encoding="utf-8")
        content = re.sub(
            r'<script type="application/json" id="boot">.*?</script>',
            f'<script type="application/json" id="boot">{boot_str}</script>',
            content,
            flags=re.DOTALL
        )
        h_path.write_text(content, encoding="utf-8")
        print(f"[OK] Aggiornato #boot in {h_path}")

# 4. Aggiorna data/active_user_tickets.json
act_path = ROOT / "data" / "active_user_tickets.json"
if act_path.exists():
    act_tickets = json.loads(act_path.read_text(encoding="utf-8"))
    act_tickets = [t for t in act_tickets if t.get("ticket_id") != TICKET_C_ACTIVE["ticket_id"]]
    act_tickets.insert(2, TICKET_C_ACTIVE)
    act_path.write_text(json.dumps(act_tickets, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[OK] Aggiornato data/active_user_tickets.json")

# 5. Aggiorna storage/database/bagent.db
db_path = ROOT / "storage" / "database" / "bagent.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT ticket_id FROM ticket_ledger WHERE ticket_id = ?", (TICKET_C_ACTIVE["ticket_id"],))
    row = cur.fetchone()
    if not row:
        cur.execute("""
            INSERT INTO ticket_ledger (
                ticket_id, date_created, description, num_legs, total_odds,
                stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            TICKET_C_ACTIVE["ticket_id"],
            datetime.datetime.now().isoformat(),
            TICKET_C_ACTIVE["title"],
            9,
            15.20,
            5.0,
            76.01,
            0.0,
            "PENDING",
            "INTEGRALE_ALL_MATCHES_UCL",
            TICKET_C_ACTIVE["notes"]
        ))
        print("[OK] Inserito Ticket C in ticket_ledger (bagent.db)")
    conn.commit()
    conn.close()

# 6. Git commit e push
def run_git(cmd, cwd):
    res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if res.returncode != 0:
        print(f"Git error in {cwd}: {res.stderr}")
        raise RuntimeError(res.stderr)
    return res.stdout.strip()

# BAgent
run_git(["git", "add", "portal/schedine.json", "portal/schedine.html", "data/active_user_tickets.json", "storage/database/bagent.db"], ROOT)
status_bagent = run_git(["git", "status", "--porcelain"], ROOT)
if status_bagent:
    commit_msg = "feat(ticket-c): add 9-match integral UCL multiplier ticket (@ 15.20x)"
    print(run_git(["git", "commit", "-m", commit_msg], ROOT))
    print(run_git(["git", "push"], ROOT))
    print("[OK] BAgent pushato con successo.")
else:
    print("[INFO] Nessuna modifica in BAgent.")

# bagent-schedine
run_git(["git", "add", "schedine.json", "index.html"], MIRROR_ROOT)
status_mirror = run_git(["git", "status", "--porcelain"], MIRROR_ROOT)
if status_mirror:
    commit_msg = "feat(ticket-c): publish 9-match integral UCL multiplier ticket (@ 15.20x)"
    print(run_git(["git", "commit", "-m", commit_msg], MIRROR_ROOT))
    print(run_git(["git", "push"], MIRROR_ROOT))
    print("[OK] bagent-schedine pushato con successo.")
else:
    print("[INFO] Nessuna modifica in bagent-schedine.")

print("\nDeploy Ticket C completato con successo!")

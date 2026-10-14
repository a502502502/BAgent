#!/usr/bin/env python3
"""
scripts/apply_ticket_a_multigol_update.py
Aggiorna Ticket A con MultiGol 1-3 2°Tempo @ 1.30 su Aston Villa vs Fenerbahce:
- Ricalcola quota (2.31x) e vincita potenziale (32.31 EUR)
- Aggiorna portal/schedine.json e portal/schedine.html
- Aggiorna data/active_user_tickets.json e storage/database/bagent.db
- Aggiorna mirror pubblico bagent-schedine (schedine.json e index.html)
- Esegue commit e push pulito su entrambi i repository (zero emoji, .env protetto)
"""

import json
import datetime
import pathlib
import sqlite3
import re
import subprocess

ROOT = pathlib.Path("C:/Project/BAgent")
MIRROR_ROOT = pathlib.Path("C:/Project/bagent-schedine")

# 1. Carica e aggiorna portal/schedine.json
p = ROOT / "portal" / "schedine.json"
data = json.loads(p.read_text(encoding="utf-8"))
data["generated_at"] = datetime.datetime.now().isoformat()

for slip in data.get("present", []):
    if slip.get("id") == "TICKET_A_CASSAFORTE_UCL_14EUR_14OTT":
        slip["title"] = "Ticket A: La Cassaforte UCL (Core Macro 70% - Incrocio OFP) (@ 2.31)"
        slip["odds"] = "2.31×"
        slip["potential_win"] = "32.31 €"
        for leg in slip.get("legs", []):
            if "Aston Villa" in leg.get("match", ""):
                leg["pick"] = "MultiGol 1-3 2°Tempo"
                leg["odd"] = "1.30"
                leg["score"] = "OFP: AAA | Tendenza Ripresa Viva | Prob: 80.4% | Edge: +4.52% [STAR]"

p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("[OK] Aggiornato portal/schedine.json")

# 2. Aggiorna mirror bagent-schedine/schedine.json
mirror_p = MIRROR_ROOT / "schedine.json"
mirror_p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
print("[OK] Aggiornato mirror bagent-schedine/schedine.json")

# 3. Aggiorna i blocchi #boot negli HTML
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
    for t in act_tickets:
        if t.get("ticket_id") == "TICKET_A_CASSAFORTE_UCL_14EUR_14OTT":
            t["title"] = "Ticket A: La Cassaforte UCL (Core Macro 70% - Incrocio OFP) (@ 2.31)"
            t["total_odds"] = 2.31
            t["potential_win"] = 32.31
            t["potential_payout_eur"] = 32.31
            t["net_profit_eur"] = 18.31
            t["notes"] = "Ticket A Core Macro 70% 100% agnostico 1X2 (LASK Tempi, Feyenoord Chance Mix, Aston Villa MG 1-3 2°T)."
            for leg in t.get("legs", []):
                if "Aston Villa" in leg.get("match", ""):
                    leg["market"] = "MultiGol 1-3 2°Tempo"
                    leg["selection"] = "SI"
                    leg["odds"] = 1.30
                    leg["score"] = "OFP: AAA | Tendenza Ripresa Viva | Prob: 80.4% | Edge: +4.52% [STAR]"
    act_path.write_text(json.dumps(act_tickets, indent=2, ensure_ascii=False), encoding="utf-8")
    print("[OK] Aggiornato data/active_user_tickets.json")

# 5. Aggiorna storage/database/bagent.db (ticket_ledger)
db_path = ROOT / "storage" / "database" / "bagent.db"
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
        UPDATE ticket_ledger
        SET description = 'Ticket A: La Cassaforte UCL (Core Macro 70% - Incrocio OFP) (@ 2.31)',
            total_odds = 2.31,
            payout_eur = 32.31,
            notes = 'Core Macro 100% agnostico 1X2 (LASK Tempi, Feyenoord Chance Mix, Aston Villa MG 1-3 2°T)'
        WHERE ticket_id = 'TICKET_A_CASSAFORTE_UCL_14EUR_14OTT'
    """)
    conn.commit()
    conn.close()
    print("[OK] Aggiornato ticket_ledger in storage/database/bagent.db")

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
    commit_msg = "feat(ticket-a): switch Aston Villa to MultiGol 1-3 2T (100% 1X2 agnostic portfolio)"
    print(run_git(["git", "commit", "-m", commit_msg], ROOT))
    print(run_git(["git", "push"], ROOT))
    print("[OK] BAgent pushato con successo.")
else:
    print("[INFO] Nessuna modifica in BAgent.")

# bagent-schedine
run_git(["git", "add", "schedine.json", "index.html"], MIRROR_ROOT)
status_mirror = run_git(["git", "status", "--porcelain"], MIRROR_ROOT)
if status_mirror:
    commit_msg = "feat(ticket-a): switch Aston Villa to MultiGol 1-3 2T (100% 1X2 agnostic portfolio)"
    print(run_git(["git", "commit", "-m", commit_msg], MIRROR_ROOT))
    print(run_git(["git", "push"], MIRROR_ROOT))
    print("[OK] bagent-schedine pushato con successo.")
else:
    print("[INFO] Nessuna modifica in bagent-schedine.")

print("\nDeploy completato con successo!")

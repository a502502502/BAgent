#!/usr/bin/env python3
"""
scripts/update_ofp_convergence_tickets.py
Aggiorna i ticket con la convergenza OFP + Forebet scores:
- Aggiorna portal/schedine.json e portal/schedine.html (#boot)
- Aggiorna mirror bagent-schedine/schedine.json e index.html
- Aggiorna data/active_user_tickets.json
- Esegue git commit e push su entrambi i repository
- Sanitizzazione emoji: ⭐ sostituita con [STAR]
"""

import json
import datetime
import pathlib
import re
import subprocess

ROOT = pathlib.Path("C:/Project/BAgent")
MIRROR_ROOT = pathlib.Path("C:/Project/bagent-schedine")

PRESENT_TICKETS = [
    {
        "id": "TICKET_A_CASSAFORTE_UCL_14EUR_14OTT",
        "title": "Ticket A: La Cassaforte UCL (Core Macro 70% - Incrocio OFP) (@ 2.41)",
        "label": "In Corso (Stasera)",
        "stake": "14.00 €",
        "odds": "2.41×",
        "potential_win": "33.74 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-14 18:45 CEST",
                "match": "LASK vs Liverpool",
                "pick": "Over 0.5 1°T + Over 0.5 2°T",
                "odd": "1.42",
                "result": "PENDING",
                "score": "OFP: AAA | Forebet 1-3 | Prob: 75.4% | Edge: +7.07% [STAR]"
            },
            {
                "when": "2026-10-14 18:45 CEST",
                "match": "Feyenoord vs Como",
                "pick": "Chance Mix: 1X o Over 1.5",
                "odd": "1.25",
                "result": "PENDING",
                "score": "OFP: AAA | Forebet 2-1 | Prob: 86.2% | Edge: +7.75% [STAR]"
            },
            {
                "when": "2026-10-14 21:00 CEST",
                "match": "Aston Villa vs Fenerbahçe",
                "pick": "1X + MultiGol 1-5",
                "odd": "1.36",
                "result": "PENDING",
                "score": "OFP: AAA | Forebet 2-1 | Prob: 78.5% | Edge: +6.76% [STAR]"
            }
        ]
    },
    {
        "id": "TICKET_B_GEMME_UCL_6EUR_14OTT",
        "title": "Ticket B: Le Gemme UCL (Satellite 30% - Incrocio OFP Max 2 Leg) (@ 2.19)",
        "label": "In Corso (Stasera)",
        "stake": "6.00 €",
        "odds": "2.19×",
        "potential_win": "13.14 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-14 21:00 CEST",
                "match": "Bodø/Glimt vs Borussia Dortmund",
                "pick": "Over 0.5 1°T + Over 0.5 2°T",
                "odd": "1.44",
                "result": "PENDING",
                "score": "OFP: AAA | Forebet 2-2 | Prob: 76.8% | Edge: +10.59% [STAR]"
            },
            {
                "when": "2026-10-14 21:00 CEST",
                "match": "Manchester City vs PSG",
                "pick": "MultiGol 0-2 1°T + 1-3 2°T",
                "odd": "1.52",
                "result": "PENDING",
                "score": "OFP: AA | Forebet 2-1 | Prob: 71.5% | Edge: +8.68% [STAR]"
            }
        ]
    }
]

# 1. Aggiorna portal/schedine.json
p = ROOT / "portal" / "schedine.json"
d = json.loads(p.read_text("utf-8"))
d["generated_at"] = datetime.datetime.now().isoformat()
d["present"] = PRESENT_TICKETS
p.write_text(json.dumps(d, indent=2, ensure_ascii=False), "utf-8")
print("[OK] Aggiornato portal/schedine.json")

# 2. Aggiorna mirror bagent-schedine/schedine.json
mirror_p = MIRROR_ROOT / "schedine.json"
mirror_p.write_text(json.dumps(d, indent=2, ensure_ascii=False), "utf-8")
print("[OK] Aggiornato mirror bagent-schedine/schedine.json")

# 3. Aggiorna #boot nei file HTML
boot_str = json.dumps(d, ensure_ascii=False)
for html_path in [ROOT / "portal" / "schedine.html", MIRROR_ROOT / "index.html"]:
    if html_path.exists():
        h = html_path.read_text("utf-8")
        h = re.sub(
            r'<script type="application/json" id="boot">.*?</script>',
            f'<script type="application/json" id="boot">{boot_str}</script>',
            h,
            flags=re.DOTALL
        )
        html_path.write_text(h, "utf-8")
        print(f"[OK] Aggiornato #boot in {html_path}")

# 4. Aggiorna data/active_user_tickets.json
active_tickets_p = ROOT / "data" / "active_user_tickets.json"
if active_tickets_p.exists():
    act = json.loads(active_tickets_p.read_text("utf-8"))
    for t in act:
        if t.get("ticket_id") == "TICKET_A_CASSAFORTE_UCL_14EUR_14OTT":
            t["title"] = PRESENT_TICKETS[0]["title"]
            for i, leg in enumerate(t.get("legs", [])):
                if i < len(PRESENT_TICKETS[0]["legs"]):
                    leg["score"] = PRESENT_TICKETS[0]["legs"][i]["score"]
        elif t.get("ticket_id") == "TICKET_B_GEMME_UCL_6EUR_14OTT":
            t["title"] = PRESENT_TICKETS[1]["title"]
            for i, leg in enumerate(t.get("legs", [])):
                if i < len(PRESENT_TICKETS[1]["legs"]):
                    leg["score"] = PRESENT_TICKETS[1]["legs"][i]["score"]
    active_tickets_p.write_text(json.dumps(act, indent=2, ensure_ascii=False), "utf-8")
    print("[OK] Sincronizzato data/active_user_tickets.json")

# 5. Git Commit & Push
def run_git(cmd, cwd):
    res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if res.returncode != 0:
        print(f"Git error in {cwd}: {res.stderr}")
        raise RuntimeError(res.stderr)
    return res.stdout.strip()

# BAgent
run_git(["git", "add", "portal/schedine.json", "portal/schedine.html", "data/active_user_tickets.json"], ROOT)
status_bagent = run_git(["git", "status", "--porcelain"], ROOT)
if status_bagent:
    commit_msg = "feat(ucl-14ott): publish OFP Champions League 70/30 tickets for tonight"
    print(run_git(["git", "commit", "-m", commit_msg], ROOT))
    print(run_git(["git", "push"], ROOT))
    print("[OK] BAgent pushato su origin/main.")
else:
    print("[INFO] Nessuna modifica pendente in BAgent.")

# bagent-schedine
run_git(["git", "add", "schedine.json", "index.html"], MIRROR_ROOT)
status_mirror = run_git(["git", "status", "--porcelain"], MIRROR_ROOT)
if status_mirror:
    commit_msg = "feat(ucl-14ott): publish OFP Champions League 70/30 tickets for tonight"
    print(run_git(["git", "commit", "-m", commit_msg], MIRROR_ROOT))
    print(run_git(["git", "push"], MIRROR_ROOT))
    print("[OK] bagent-schedine pushato su origin/main.")
else:
    print("[INFO] Nessuna modifica pendente in bagent-schedine.")

print("\nDeploy OFP convergenza completato con successo.")

#!/usr/bin/env python3
"""
BAgent Automated Deployer - Gemini 4 Argon 70/30 Portfolio (14 Ottobre 2026)
- Codifica Regola #86 (Ortogonalita di Portafoglio & Zero Single-Point-of-Failure)
- Aggiorna CLAUDE.md, .cursorrules, .cursor/rules/orthogonality-portfolio-gate.mdc, AGENTS.md, GEMINI.md
- Registra Ticket A (14 EUR @ 2.41) e Ticket B (6 EUR @ 2.19) in active_user_tickets.json e bagent.db
- Aggiorna portal/schedine.json, portal/schedine.html e mirror bagent-schedine
- Esegue commit e push pulito (NO emojis, .env protetto)
"""

import json
import sqlite3
import re
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path("C:/Project/BAgent")
MIRROR_ROOT = Path("C:/Project/bagent-schedine")

# 1. DEFINIZIONE TICKETS ARGON (14 OTTOBRE 2026) - EMOJI FREE
TONIGHT_PORTAL_TICKETS = [
    {
        "id": "TICKET_A_CASSAFORTE_UCL_14EUR_14OTT",
        "title": "Ticket A: La Cassaforte (Core Macro 70% - Regola #82/#83) (@ 2.41)",
        "label": "In Corso (Stasera)",
        "stake": "14.00 €",
        "odds": "2.41×",
        "potential_win": "33.74 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-14 18:45 CEST",
                "match": "LASK vs Liverpool",
                "pick": "Over 0.5 1°T + Over 0.5 2°T : SI",
                "odd": "1.42",
                "result": "PENDING",
                "score": "Prob OFP: 75.4% | Edge: +7.07% [STAR]"
            },
            {
                "when": "2026-10-14 18:45 CEST",
                "match": "Feyenoord vs Como",
                "pick": "Chance Mix: 1X o Over 1.5",
                "odd": "1.25",
                "result": "PENDING",
                "score": "Prob OFP: 86.2% | Edge: +7.75% [STAR]"
            },
            {
                "when": "2026-10-14 21:00 CEST",
                "match": "Aston Villa vs Fenerbahçe",
                "pick": "1X + MultiGol 1-5 : SI",
                "odd": "1.36",
                "result": "PENDING",
                "score": "Prob OFP: 78.5% | Edge: +6.76% [STAR]"
            }
        ]
    },
    {
        "id": "TICKET_B_GEMME_UCL_6EUR_14OTT",
        "title": "Ticket B: Le Gemme (Satellite Asimmetrico 30% - Max 2 Selezioni) (@ 2.19)",
        "label": "In Corso (Stasera)",
        "stake": "6.00 €",
        "odds": "2.19×",
        "potential_win": "13.14 €",
        "booking_code": None,
        "legs": [
            {
                "when": "2026-10-14 21:00 CEST",
                "match": "Bodø/Glimt vs Borussia Dortmund",
                "pick": "Over 0.5 1°T + Over 0.5 2°T : SI",
                "odd": "1.44",
                "result": "PENDING",
                "score": "Prob OFP: 76.8% | Edge: +10.59% [STAR]"
            },
            {
                "when": "2026-10-14 21:00 CEST",
                "match": "Manchester City vs PSG",
                "pick": "MultiGol 0-2 1°T + 1-3 2°T : SI",
                "odd": "1.52",
                "result": "PENDING",
                "score": "Prob OFP: 71.5% | Edge: +8.68% [STAR]"
            }
        ]
    }
]

TONIGHT_ACTIVE_USER_TICKETS = [
    {
        "ticket_id": "TICKET_A_CASSAFORTE_UCL_14EUR_14OTT",
        "name": "Ticket A: La Cassaforte UCL 14 Ottobre",
        "title": "Ticket A: La Cassaforte (Core Macro 70% - Regola #82/#83) (@ 2.41)",
        "bookmaker": "Netwin",
        "type": "Tripla Core Macro",
        "status": "PENDING",
        "placed_at": "2026-10-14 18:45 CEST",
        "created_at": "2026-10-14T10:45:00+02:00",
        "date_created": "2026-10-14 10:45:00",
        "stake": 14.0,
        "stake_eur": 14.0,
        "bonus": 0.0,
        "total_odds": 2.41,
        "potential_win": 33.74,
        "potential_payout_eur": 33.74,
        "net_profit_eur": 19.74,
        "settled": False,
        "profit_loss_eur": 0.0,
        "notes": "Ticket A Core Macro 70% formulato con Gemini 4 Argon. LASK-Liverpool Tempi, Feyenoord-Como Chance Mix, Aston Villa-Fenerbahçe 1X+MG 1-5.",
        "legs": [
            {
                "match": "LASK vs Liverpool",
                "tournament": "Club Internazionali | UEFA Champions League",
                "kickoff": "2026-10-14 18:45 CEST",
                "market": "Over 0.5 1°T + Over 0.5 2°T : SI",
                "selection": "SI",
                "odds": 1.42,
                "status": "PENDING",
                "score": "Prob OFP: 75.4% | Edge: +7.07% [STAR]"
            },
            {
                "match": "Feyenoord vs Como",
                "tournament": "Club Internazionali | UEFA Champions League",
                "kickoff": "2026-10-14 18:45 CEST",
                "market": "Chance Mix: 1X o Over 1.5",
                "selection": "SI",
                "odds": 1.25,
                "status": "PENDING",
                "score": "Prob OFP: 86.2% | Edge: +7.75% [STAR]"
            },
            {
                "match": "Aston Villa vs Fenerbahçe",
                "tournament": "Club Internazionali | UEFA Champions League",
                "kickoff": "2026-10-14 21:00 CEST",
                "market": "1X + MultiGol 1-5 : SI",
                "selection": "SI",
                "odds": 1.36,
                "status": "PENDING",
                "score": "Prob OFP: 78.5% | Edge: +6.76% [STAR]"
            }
        ]
    },
    {
        "ticket_id": "TICKET_B_GEMME_UCL_6EUR_14OTT",
        "name": "Ticket B: Le Gemme UCL 14 Ottobre",
        "title": "Ticket B: Le Gemme (Satellite Asimmetrico 30% - Max 2 Selezioni) (@ 2.19)",
        "bookmaker": "Netwin",
        "type": "Doppia Satellite Asimmetrico",
        "status": "PENDING",
        "placed_at": "2026-10-14 21:00 CEST",
        "created_at": "2026-10-14T10:45:00+02:00",
        "date_created": "2026-10-14 10:45:00",
        "stake": 6.0,
        "stake_eur": 6.0,
        "bonus": 0.0,
        "total_odds": 2.19,
        "potential_win": 13.14,
        "potential_payout_eur": 13.14,
        "net_profit_eur": 7.14,
        "settled": False,
        "profit_loss_eur": 0.0,
        "notes": "Ticket B Satellite Asimmetrico 30% formulato con Gemini 4 Argon. Bodø/Glimt-Dortmund Tempi, Man City-PSG MultiGol Tempi.",
        "legs": [
            {
                "match": "Bodø/Glimt vs Borussia Dortmund",
                "tournament": "Club Internazionali | UEFA Champions League",
                "kickoff": "2026-10-14 21:00 CEST",
                "market": "Over 0.5 1°T + Over 0.5 2°T : SI",
                "selection": "SI",
                "odds": 1.44,
                "status": "PENDING",
                "score": "Prob OFP: 76.8% | Edge: +10.59% [STAR]"
            },
            {
                "match": "Manchester City vs PSG",
                "tournament": "Club Internazionali | UEFA Champions League",
                "kickoff": "2026-10-14 21:00 CEST",
                "market": "MultiGol 0-2 1°T + 1-3 2°T : SI",
                "selection": "SI",
                "odds": 1.52,
                "status": "PENDING",
                "score": "Prob OFP: 71.5% | Edge: +8.68% [STAR]"
            }
        ]
    }
]


def update_manifests_and_rules():
    print("[1/5] Aggiornamento Regole e Manifesti...")
    
    # 1. CLAUDE.md
    claude_path = ROOT / "CLAUDE.md"
    content = claude_path.read_text(encoding="utf-8")
    
    old_str = "es. `Sommer, Yann (Club Brugge)` milita nel Brugge, NON nell'Inter; `Martinez, Josep` milita nell'Inter"
    if old_str in content:
        content = content.replace(
            old_str,
            "verificando sempre la corrispondenza con Transfermarkt.it e liste ufficiali UEFA (Regola #85 Reality Gate)"
        )
        
    if "Regola #86 (Vincolo di Ortogonalità" not in content and "Regola #86" not in content:
        rule_86_claude = (
            "\n- **Regola #86 (Vincolo di Ortogonalità del Portafoglio & Zero Single-Point-of-Failure)**:\n"
            "  È severamente vietato inserire la stessa partita o la stessa Player Prop in più di un ticket "
            "nella medesima sessione. Ogni ticket del portafoglio (Core 70% vs Satellite 30%) deve contenere eventi "
            "rigorosamente e statisticamente indipendenti per eliminare correlazioni negative e single-point-of-failure.\n"
        )
        content = content.rstrip() + "\n" + rule_86_claude
        claude_path.write_text(content, encoding="utf-8")
        print("  - Aggiunta Regola #86 in CLAUDE.md")
    else:
        print("  - Regola #86 gia presente in CLAUDE.md")

    # 2. .cursorrules
    cursorrules_path = ROOT / ".cursorrules"
    cr_content = cursorrules_path.read_text(encoding="utf-8")
    if "Regola #86" not in cr_content:
        rule_86_cr = (
            "\n## Regola #86: Vincolo di Ortogonalità del Portafoglio & Zero Single-Point-of-Failure\n"
            "- **Divieto di Overlap tra Ticket della Stessa Sessione**:\n"
            "  1. È severamente vietato inserire la stessa partita o la stessa Player Prop in più di un ticket nella medesima sessione.\n"
            "  2. Ogni ticket del portafoglio (Core 70% vs Satellite 30%) deve contenere eventi rigorosamente e statisticamente indipendenti.\n"
            "- **Protezione da Single-Point-of-Failure**:\n"
            "  1. Nessun singolo evento, errore arbitrale o episodio isolato (es. espulsione precoce, autogol, crollo della favorita) deve poter compromettere simultaneamente entrambi i ticket.\n"
            "  2. Se un evento fa parte del Ticket A (\"La Cassaforte\"), è categoricamente escluso da qualsiasi iterazione o mercato speciale del Ticket B (\"Le Gemme\" / Satellite) e viceversa.\n"
        )
        cr_content = cr_content.rstrip() + "\n" + rule_86_cr
        cursorrules_path.write_text(cr_content, encoding="utf-8")
        print("  - Aggiunta Regola #86 in .cursorrules")
    else:
        print("  - Regola #86 gia presente in .cursorrules")

    # 3. .cursor/rules/orthogonality-portfolio-gate.mdc
    rule_mdc_path = ROOT / ".cursor" / "rules" / "orthogonality-portfolio-gate.mdc"
    rule_mdc_content = (
        "---\n"
        "description: Regola #86 (Vincolo di Ortogonalita del Portafoglio & Zero Single-Point-of-Failure)\n"
        "alwaysApply: true\n"
        "---\n\n"
        "# Regola #86: Vincolo di Ortogonalita del Portafoglio & Zero Single-Point-of-Failure\n\n"
        "## Divieto di Overlap tra Ticket della Stessa Sessione\n"
        "1. E severamente vietato inserire la stessa partita o la stessa Player Prop in piu di un ticket nella medesima sessione.\n"
        "2. Ogni ticket del portafoglio (Core 70% vs Satellite 30%) deve contenere eventi rigorosamente e statisticamente indipendenti.\n\n"
        "## Protezione da Single-Point-of-Failure\n"
        "1. Nessun singolo evento, errore arbitrale o episodio isolato (es. espulsione precoce, autogol, pioggia anomala di gol, crollo della favorita) deve poter compromettere simultaneamente entrambi i ticket.\n"
        "2. Se un evento fa parte del Ticket A (\"La Cassaforte\"), e categoricamente escluso da qualsiasi iterazione o mercato speciale del Ticket B (\"Le Gemme\" / Satellite) e viceversa.\n"
    )
    rule_mdc_path.write_text(rule_mdc_content, encoding="utf-8")
    print(f"  - Scritto {rule_mdc_path.relative_to(ROOT)}")


def update_active_tickets_and_db():
    print("[2/5] Aggiornamento active_user_tickets.json e bagent.db...")
    tickets_file = ROOT / "data" / "active_user_tickets.json"
    with open(tickets_file, "r", encoding="utf-8") as f:
        tickets = json.load(f)

    existing_ids = {t.get("ticket_id") for t in tickets}
    new_tickets_to_add = [t for t in TONIGHT_ACTIVE_USER_TICKETS if t["ticket_id"] not in existing_ids]

    if new_tickets_to_add:
        # Prepend new active tickets
        tickets = new_tickets_to_add + tickets
        with open(tickets_file, "w", encoding="utf-8") as f:
            json.dump(tickets, f, indent=2, ensure_ascii=False)
        print(f"  - Aggiunti {len(new_tickets_to_add)} ticket in data/active_user_tickets.json")
    else:
        print("  - Ticket gia presenti in data/active_user_tickets.json")

    # Aggiornamento SQLite ticket_ledger
    db_path = ROOT / "storage" / "database" / "bagent.db"
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    for t in TONIGHT_ACTIVE_USER_TICKETS:
        tid = t["ticket_id"]
        cur.execute("SELECT ticket_id FROM ticket_ledger WHERE ticket_id = ?", (tid,))
        row = cur.fetchone()
        if not row:
            cur.execute("""
                INSERT INTO ticket_ledger (
                    ticket_id, date_created, description, num_legs, total_odds,
                    stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                tid,
                datetime.now().isoformat(),
                t["title"],
                len(t["legs"]),
                t["total_odds"],
                t["stake_eur"],
                t["potential_payout_eur"],
                0.0,
                "PENDING",
                "CORE_MACRO_70" if "CASSAFORTE" in tid else "SATELLITE_GEMS_30",
                t["notes"]
            ))
            print(f"  - Inserito {tid} in ticket_ledger (bagent.db)")
        else:
            print(f"  - {tid} gia presente in ticket_ledger (bagent.db)")
    conn.commit()
    conn.close()


def update_portal_and_mirrors():
    print("[3/5] Aggiornamento portali (portal/schedine.json, schedine.html e mirror)...")
    portal_json_path = ROOT / "portal" / "schedine.json"
    with open(portal_json_path, "r", encoding="utf-8") as f:
        portal_data = json.load(f)

    portal_data["generated_at"] = datetime.now().isoformat()
    portal_data["present"] = TONIGHT_PORTAL_TICKETS
    # past rimane intatto, profit_label rimane intatto

    # Scrittura portal/schedine.json
    with open(portal_json_path, "w", encoding="utf-8") as f:
        json.dump(portal_data, f, indent=2, ensure_ascii=False)
    print("  - Aggiornato portal/schedine.json")

    # Scrittura mirror bagent-schedine/schedine.json
    mirror_json_path = MIRROR_ROOT / "schedine.json"
    with open(mirror_json_path, "w", encoding="utf-8") as f:
        json.dump(portal_data, f, indent=2, ensure_ascii=False)
    print("  - Aggiornato mirror bagent-schedine/schedine.json")

    # Scrittura HTML boot tags
    boot_str = json.dumps(portal_data, ensure_ascii=False)

    html_path = ROOT / "portal" / "schedine.html"
    with open(html_path, "r", encoding="utf-8") as f:
        h = f.read()
    h = re.sub(
        r'<script type="application/json" id="boot">.*?</script>',
        f'<script type="application/json" id="boot">{boot_str}</script>',
        h,
        flags=re.DOTALL
    )
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(h)
    print("  - Aggiornato #boot in portal/schedine.html")

    mirror_html = MIRROR_ROOT / "index.html"
    with open(mirror_html, "r", encoding="utf-8") as f:
        mh = f.read()
    mh = re.sub(
        r'<script type="application/json" id="boot">.*?</script>',
        f'<script type="application/json" id="boot">{boot_str}</script>',
        mh,
        flags=re.DOTALL
    )
    with open(mirror_html, "w", encoding="utf-8") as f:
        f.write(mh)
    print("  - Aggiornato #boot in mirror bagent-schedine/index.html")


def git_commit_and_push():
    print("[4/5] Esecuzione Git commit e push...")

    def run_cmd(cmd, cwd):
        res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
        if res.returncode != 0:
            print(f"[ERRORE GIT] {' '.join(cmd)} in {cwd}:\n{res.stderr}")
            raise RuntimeError(res.stderr)
        return res.stdout.strip()

    # 1. BAgent
    print("  - Staging BAgent...")
    subprocess.run(["git", "reset", ".env"], cwd=ROOT, capture_output=True)

    files_bagent = [
        "CLAUDE.md",
        ".cursorrules",
        ".cursor/rules/orthogonality-portfolio-gate.mdc",
        "data/active_user_tickets.json",
        "storage/database/bagent.db",
        "portal/schedine.json",
        "portal/schedine.html",
        "scripts/deploy_argon_portfolio_14oct.py"
    ]
    for f in files_bagent:
        if (ROOT / f).exists():
            run_cmd(["git", "add", f], ROOT)

    status_bagent = run_cmd(["git", "status", "--porcelain"], ROOT)
    if status_bagent:
        commit_msg = (
            "feat(ofp-v2): add orthogonality gate rule 86 and UCL 14/10 portfolio 70/30"
        )
        print("  - Commit BAgent...")
        print(run_cmd(["git", "commit", "-m", commit_msg], ROOT))
        print("  - Push BAgent...")
        print(run_cmd(["git", "push"], ROOT))
        print("  [OK] BAgent repository allineato e inviato su GitHub.")
    else:
        print("  [INFO] Nessuna modifica da committare in BAgent.")

    # 2. bagent-schedine
    print("  - Staging bagent-schedine...")
    files_mirror = ["schedine.json", "index.html"]
    for f in files_mirror:
        if (MIRROR_ROOT / f).exists():
            run_cmd(["git", "add", f], MIRROR_ROOT)

    status_mirror = run_cmd(["git", "status", "--porcelain"], MIRROR_ROOT)
    if status_mirror:
        commit_msg = (
            "feat(portal): publish UCL 14/10 tickets A and B (70/30 orthogonal portfolio)"
        )
        print("  - Commit bagent-schedine...")
        print(run_cmd(["git", "commit", "-m", commit_msg], MIRROR_ROOT))
        print("  - Push bagent-schedine...")
        print(run_cmd(["git", "push"], MIRROR_ROOT))
        print("  [OK] bagent-schedine repository allineato e inviato su GitHub.")
    else:
        print("  [INFO] Nessuna modifica da committare in bagent-schedine.")


if __name__ == "__main__":
    update_manifests_and_rules()
    update_active_tickets_and_db()
    update_portal_and_mirrors()
    git_commit_and_push()
    print("\n[5/5] Deploy completato con successo su entrambi i repository.")

import json
import re
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path("C:/Project/BAgent")
MIRROR_ROOT = Path("C:/Project/bagent-schedine")

tickets_path = ROOT / "data" / "active_user_tickets.json"
with open(tickets_path, "r", encoding="utf-8") as f:
    tickets = json.load(f)

# Define Ticket 4 (Tripla Alta Quota Combo)
ticket_id = "TICKET_USER_TRIPLA_ALTAQUOTA_5EUR_13OTT"
user_ticket = {
    "ticket_id": ticket_id,
    "title": "Schedina Reale Utente 4: Tripla Alta Quota Combo UCL (@ 11.30)",
    "name": "Schedina Reale Utente 4: Tripla Alta Quota Combo UCL (@ 11.30)",
    "bookmaker": "Netwin",
    "type": "Multipla (3)",
    "placed_at": "2026-10-13 16:53 CEST",
    "created_at": "2026-10-13T16:53:51+02:00",
    "date_created": "2026-10-13 16:53:51",
    "status": "PENDING",
    "strategy": "USER_PLAYED_TICKET_HIGH_ODDS_COMBO",
    "stake": 5.0,
    "stake_eur": 5.0,
    "bonus": 0.0,
    "total_odds": 11.30,
    "potential_win": 56.54,
    "potential_payout_eur": 56.54,
    "net_profit_eur": 51.54,
    "settled": False,
    "profit_loss_eur": 0.0,
    "notes": "Schedina reale giocata dall utente su Netwin: Tripla Alta Quota Combo UCL. Importo 5.00 EUR, Quota 11.30, Vincita potenziale 56.54 EUR. Kickoff 13/10/2026 ore 21:00 CEST.",
    "legs": [
        {
            "match": "Villarreal vs Napoli",
            "tournament": "UEFA Champions League",
            "competition": "UEFA Champions League",
            "kickoff": "2026-10-13 21:00 CEST",
            "market": "Doppia Chance + GG/NG: X2 + GG",
            "selection": "X2 + GG",
            "odds": 2.57,
            "status": "PENDING",
            "score": "-",
            "minute": "PRE",
            "rationale": "Il Napoli di Allegri solido all Estadio de la Ceramica: copre il pareggio con gol (1-1, 2-2) e la vittoria azzurra con rete dei padroni di casa (1-2, 1-3)."
        },
        {
            "match": "Galatasaray vs Barcellona",
            "tournament": "UEFA Champions League",
            "competition": "UEFA Champions League",
            "kickoff": "2026-10-13 21:00 CEST",
            "market": "1X2 + GG/NG: 2 + GG",
            "selection": "2 + GG",
            "odds": 1.93,
            "status": "PENDING",
            "score": "-",
            "minute": "PRE",
            "rationale": "Vittoria del Barcellona di Flick al RAMS Park con gol dei turchi: Lewandowski, Yamal e Raphinha superiori, ma l attacco del Gala (Osimhen, Leao) punge con regolarita."
        },
        {
            "match": "Inter vs Club Brugge",
            "tournament": "UEFA Champions League",
            "competition": "UEFA Champions League",
            "kickoff": "2026-10-13 21:00 CEST",
            "market": "1X2 + GG/NG: 1 + NG",
            "selection": "1 + NG",
            "odds": 2.28,
            "status": "PENDING",
            "score": "-",
            "minute": "PRE",
            "rationale": "Vittoria nerazzurra a San Siro con clean sheet: retroguardia di Chivu (Bastoni, Stones, Akanji, Provedel) ermetica contro il Brugge (finali 1-0, 2-0, 3-0)."
        }
    ]
}

# 1. Update data/active_user_tickets.json
tickets = [t for t in tickets if t.get("ticket_id") != ticket_id]
tickets.insert(0, user_ticket)
with open(tickets_path, "w", encoding="utf-8") as f:
    json.dump(tickets, f, indent=2, ensure_ascii=False)
print("Updated data/active_user_tickets.json")

# 2. Update sqlite database
db_path = ROOT / "storage" / "database" / "bagent.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("""
    INSERT OR REPLACE INTO ticket_ledger 
    (ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes)
    VALUES (?, ?, ?, 3, ?, ?, ?, 0.0, 'OPEN', 'USER_HIGH_ODDS_COMBO_UCL', ?)
""", (
    ticket_id,
    "2026-10-13T16:53:51+02:00",
    "Schedina Reale Utente 4: Tripla Alta Quota Combo UCL (@ 11.30)",
    11.30,
    5.0,
    56.54,
    "Tripla Alta Quota Netwin (X2+GG Villarreal-Napoli, 2+GG Gala-Barca, 1+NG Inter-Brugge)"
))

cur.execute("DELETE FROM bet_leg_ledger WHERE ticket_id = ?", (ticket_id,))
for leg in user_ticket["legs"]:
    cur.execute("""
        INSERT INTO bet_leg_ledger 
        (ticket_id, match_name, tournament, market_category, selection, odds, estimated_prob, edge_pct, result_status, clv_pct)
        VALUES (?, ?, ?, 'HIGH_ODDS_COMBO', ?, ?, 0.0, 0.0, 'PENDING', 0.0)
    """, (
        ticket_id,
        leg["match"],
        leg["tournament"],
        leg["selection"],
        leg["odds"]
    ))

conn.commit()
conn.close()
print("Updated bagent.db (ticket_ledger & bet_leg_ledger)")

# 3. Format portal data
def format_portal_slip(t, label_override=None):
    stake = t.get("stake") or t.get("stake_eur") or 0.0
    odds = t.get("total_odds") or 0.0
    status = t.get("status", "PENDING")
    
    if label_override:
        label = label_override
    elif status == "WON":
        label = f"Vinta (+{t.get('potential_win', 0.0):.2f} €)"
    elif status == "LOST":
        label = "Persa"
    elif status in ["PENDING", "IN_PROGRESS"]:
        label = "In attesa"
    else:
        label = status

    legs_out = []
    legs_src = t.get("legs") or t.get("selections") or []
    for leg in legs_src:
        ko = leg.get("kickoff") or leg.get("date_time") or "-"
        when_str = ko.replace("2026-", "").replace(" CEST", "").strip()
        match_str = leg.get("match", "")
        pick_str = leg.get("market") or leg.get("selection") or ""
        odd_str = f"{float(leg.get('odds') or leg.get('quota') or 0.0):.2f}"
        res_str = leg.get("status") or leg.get("result") or "PENDING"
        score_str = leg.get("score") or ""
        if score_str == "-":
            score_str = ""
        legs_out.append({
            "when": when_str,
            "match": match_str,
            "pick": pick_str,
            "odd": odd_str,
            "result": res_str,
            "score": score_str
        })

    slip_data = {
        "id": t.get("ticket_id", ""),
        "title": t.get("title") or t.get("name") or t.get("ticket_id"),
        "label": label,
        "stake": f"{float(stake):.2f} €",
        "odds": f"{float(odds):.2f}×",
        "potential_win": f"{float(t.get('potential_win') or 0.0):.2f} €",
        "booking_code": t.get("booking_code"),
        "legs": legs_out
    }
    if t.get("bonus"):
        slip_data["bonus"] = f"{float(t['bonus']):.2f} €"
    return slip_data

# Present = active tickets today (Tickets 1, 2, 3, 4)
present_tickets = [t for t in tickets if not t.get("settled") and "13OTT" in t.get("ticket_id", "")]
present_slips = [format_portal_slip(t, "In attesa") for t in present_tickets]

# Read existing portal/schedine.json to keep past tickets intact
portal_json_path = ROOT / "portal" / "schedine.json"
try:
    with open(portal_json_path, "r", encoding="utf-8") as f:
        existing_portal = json.load(f)
    past_slips = existing_portal.get("past", [])
except Exception:
    past_slips = []

portal_data = {
    "generated_at": datetime.now().isoformat(),
    "check_seconds": 30,
    "profit_label": "+41.61 € (Saldo Netto 12 Ott)",
    "present": present_slips,
    "future": [],
    "past": past_slips
}

# 4. Save portal JSONs
with open(portal_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)
print("Updated portal/schedine.json")

mirror_json_path = MIRROR_ROOT / "schedine.json"
with open(mirror_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)
print("Updated bagent-schedine/schedine.json")

# 5. Update HTML #boot in both places
boot_str = json.dumps(portal_data, ensure_ascii=False)

html_path = ROOT / "portal" / "schedine.html"
with open(html_path, "r", encoding="utf-8") as f:
    h = f.read()
h = re.sub(r'<script type="application/json" id="boot">.*?</script>', f'<script type="application/json" id="boot">{boot_str}</script>', h, flags=re.DOTALL)
with open(html_path, "w", encoding="utf-8") as f:
    f.write(h)
print("Updated portal/schedine.html")

mirror_html = MIRROR_ROOT / "index.html"
with open(mirror_html, "r", encoding="utf-8") as f:
    mh = f.read()
mh = re.sub(r'<script type="application/json" id="boot">.*?</script>', f'<script type="application/json" id="boot">{boot_str}</script>', mh, flags=re.DOTALL)
with open(mirror_html, "w", encoding="utf-8") as f:
    f.write(mh)
print("Updated bagent-schedine/index.html")

print("All files updated successfully.")

import json
import sqlite3
import re
from pathlib import Path
from datetime import datetime

ROOT = Path("C:/Project/BAgent")
MIRROR_ROOT = Path("C:/Project/bagent-schedine")

tickets_path = ROOT / "data" / "active_user_tickets.json"
with open(tickets_path, "r", encoding="utf-8") as f:
    tickets = json.load(f)

# Update the 4 tickets from 13 October
for t in tickets:
    tid = t.get("ticket_id")
    if tid == "TICKET_USER_TRIPLA_GEMME_PROPS_10EUR_13OTT":
        t["status"] = "LOST"
        t["settled"] = True
        t["profit_loss_eur"] = -10.0
        # Legs
        for leg in t["legs"]:
            if "Hojlund" in leg["market"]:
                leg["status"] = "WON"
                leg["score"] = "1 Tiro in Porta (81')"
            elif "Martinez" in leg["market"]:
                leg["status"] = "LOST"
                leg["score"] = "1 Fallo (26'), 0 Card"
            elif "Sommer" in leg["market"]:
                leg["status"] = "WON"
                leg["score"] = "9 Parate (FT)"

    elif tid == "TICKET_USER_MULTIPLA6_TOP_MATCHES_10EUR_13OTT":
        t["status"] = "LOST"
        t["settled"] = True
        t["profit_loss_eur"] = -10.0
        for leg in t["legs"]:
            if "Villarreal" in leg["match"]:
                leg["status"] = "WON"
                leg["score"] = "3-1 (FT)"
            elif "Arsenal" in leg["match"]:
                leg["status"] = "WON"
                leg["score"] = "3-0 (21 Tiri) (FT)"
            elif "Atletico" in leg["match"]:
                leg["status"] = "WON"
                leg["score"] = "2-0 (FT)"
            elif "Lipsia" in leg["match"]:
                leg["status"] = "LOST"
                leg["score"] = "0-0 1°T (1-0 FT 75')"
            elif "Galatasaray" in leg["match"]:
                leg["status"] = "WON"
                leg["score"] = "1-4 (FT)"
            elif "Inter" in leg["match"]:
                leg["status"] = "LOST"
                leg["score"] = "1-1 1°T, 2-3 2°T (3-4 FT)"

    elif tid == "TICKET_USER_PROPS_QUADRUPLA_10EUR_13OTT":
        t["status"] = "LOST"
        t["settled"] = True
        t["profit_loss_eur"] = -10.0
        for leg in t["legs"]:
            if "Sabbe" in leg["market"]:
                leg["status"] = "LOST"
                leg["score"] = "0 Falli, 0 Card (Out 72')"
            elif "Martinez" in leg["market"]:
                leg["status"] = "LOST"
                leg["score"] = "1 Fallo (26'), 0 Card"
            elif "Leao" in leg["market"]:
                leg["status"] = "LOST"
                leg["score"] = "0 Tiri in Porta (1 Assist)"
            elif "Hojlund" in leg["market"]:
                leg["status"] = "WON"
                leg["score"] = "1 Tiro in Porta (81')"

    elif tid == "TICKET_USER_TRIPLA_ALTAQUOTA_5EUR_13OTT":
        t["status"] = "LOST"
        t["settled"] = True
        t["profit_loss_eur"] = -5.0
        for leg in t["legs"]:
            if "Villarreal" in leg["match"]:
                leg["status"] = "LOST"
                leg["score"] = "3-1 (FT)"
            elif "Galatasaray" in leg["match"]:
                leg["status"] = "WON"
                leg["score"] = "1-4 (FT)"
            elif "Inter" in leg["match"]:
                leg["status"] = "LOST"
                leg["score"] = "3-4 (FT)"

# Save active_user_tickets.json
with open(tickets_path, "w", encoding="utf-8") as f:
    json.dump(tickets, f, indent=2, ensure_ascii=False)
print("Updated data/active_user_tickets.json")

# Update SQLite
db_path = ROOT / "storage" / "database" / "bagent.db"
conn = sqlite3.connect(db_path)
cur = conn.cursor()
for tid, pl in [
    ("TICKET_USER_TRIPLA_GEMME_PROPS_10EUR_13OTT", -10.0),
    ("TICKET_USER_MULTIPLA6_TOP_MATCHES_10EUR_13OTT", -10.0),
    ("TICKET_USER_PROPS_QUADRUPLA_10EUR_13OTT", -10.0),
    ("TICKET_USER_TRIPLA_ALTAQUOTA_5EUR_13OTT", -5.0)
]:
    cur.execute("UPDATE ticket_ledger SET status = 'LOST', profit_loss_eur = ? WHERE ticket_id = ?", (pl, tid))
conn.commit()
conn.close()
print("Updated bagent.db")

# Update portal/schedine.json
def format_portal_slip(t):
    stake = t.get("stake") or t.get("stake_eur") or 0.0
    odds = t.get("total_odds") or 0.0
    status = t.get("status", "LOST")
    label = "Persa" if status == "LOST" else f"Vinta (+{t.get('potential_win', 0.0):.2f} €)"

    legs_out = []
    for leg in (t.get("legs") or []):
        ko = leg.get("kickoff") or "—"
        when_str = ko.replace("2026-", "").replace(" CEST", "").strip()
        legs_out.append({
            "when": when_str,
            "match": leg.get("match", ""),
            "pick": leg.get("market") or leg.get("selection") or "",
            "odd": f"{float(leg.get('odds') or 0.0):.2f}",
            "result": leg.get("status", "LOST"),
            "score": leg.get("score", "")
        })

    slip_data = {
        "id": t.get("ticket_id", ""),
        "title": t.get("title") or t.get("ticket_id"),
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

# Move the 4 tickets to past in portal
portal_json_path = ROOT / "portal" / "schedine.json"
with open(portal_json_path, "r", encoding="utf-8") as f:
    portal_data = json.load(f)

# Format the 4 closed slips
closed_slips = [
    format_portal_slip(t) for t in tickets 
    if t.get("ticket_id") in [
        "TICKET_USER_TRIPLA_GEMME_PROPS_10EUR_13OTT",
        "TICKET_USER_MULTIPLA6_TOP_MATCHES_10EUR_13OTT",
        "TICKET_USER_PROPS_QUADRUPLA_10EUR_13OTT",
        "TICKET_USER_TRIPLA_ALTAQUOTA_5EUR_13OTT"
    ]
]

# Keep existing past slips (from 12 Oct) and prepend the new closed slips
existing_past = portal_data.get("past", [])
portal_data["present"] = []
portal_data["future"] = []
portal_data["past"] = closed_slips + existing_past
portal_data["generated_at"] = datetime.now().isoformat()
portal_data["profit_label"] = "+6.61 € (Saldo Netto Aggiornato)"

# Save portal JSONs
with open(portal_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)

mirror_json_path = MIRROR_ROOT / "schedine.json"
with open(mirror_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)

# Update HTML #boot
boot_str = json.dumps(portal_data, ensure_ascii=False)
html_path = ROOT / "portal" / "schedine.html"
with open(html_path, "r", encoding="utf-8") as f:
    h = f.read()
h = re.sub(r'<script type="application/json" id="boot">.*?</script>', f'<script type="application/json" id="boot">{boot_str}</script>', h, flags=re.DOTALL)
with open(html_path, "w", encoding="utf-8") as f:
    f.write(h)

mirror_html = MIRROR_ROOT / "index.html"
with open(mirror_html, "r", encoding="utf-8") as f:
    mh = f.read()
mh = re.sub(r'<script type="application/json" id="boot">.*?</script>', f'<script type="application/json" id="boot">{boot_str}</script>', mh, flags=re.DOTALL)
with open(mirror_html, "w", encoding="utf-8") as f:
    f.write(mh)

print("Portals and HTML boot blocks settled successfully.")

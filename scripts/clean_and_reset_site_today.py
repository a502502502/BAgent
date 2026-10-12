import json
import re
from pathlib import Path
from datetime import datetime

# 1. Update active_user_tickets.json
tickets_path = Path("data/active_user_tickets.json")
with open(tickets_path, "r", encoding="utf-8") as f:
    tickets = json.load(f)

for t in tickets:
    # Fix Torino vs Udinese market label in CORE ROCKET
    if t.get("ticket_id") == "TICKET_12OTT_CORE_ROCKET":
        for leg in t.get("legs", []):
            if "Torino" in leg.get("match", ""):
                leg["market"] = "MultiGol Tempi: 0-2 1°T + 1-3 2°T"
                leg["selection"] = "MultiGol 0-2 1°T + 1-3 2°T (SI)"
    
    # Fix Hougang in User ticket to have clear line
    if t.get("ticket_id") == "TICKET_USER_MULTIPLA5_MATTINA_10EUR_12OTT":
        for leg in t.get("legs", []):
            if "Hougang" in leg.get("match", ""):
                leg["market"] = "Totale Gol: Over 2.5"
                leg["selection"] = "Over 2.5"

with open(tickets_path, "w", encoding="utf-8") as f:
    json.dump(tickets, f, indent=2, ensure_ascii=False)

print("Updated active_user_tickets.json with descriptive labels.")

# 2. Build the CLEAN portal presentation
# Helper to format clean slip
def clean_pick_label(leg):
    market = (leg.get("market") or "").strip()
    selection = (leg.get("selection") or "").strip()
    
    # Specific mappings
    if "Torino" in leg.get("match", ""):
        return "MultiGol Tempi: 0-2 1°T + 1-3 2°T"
    if selection.upper() in ["SI", "NO"]:
        return market if market else selection
    if "1X2" in market and selection in ["1", "X", "2"]:
        return f"1X2: {selection}"
    if "Chance Mix" in market and "X o Gol" in selection:
        return "Chance Mix: X o Gol"
    if "Hougang" in leg.get("match", ""):
        return "Over 2.5"
    if "Panionios" in leg.get("match", ""):
        return "1X + Under 3.5"
    if "Livyi" in leg.get("match", ""):
        return "X2 + Under 3.5"
    if selection == "X2 + UN":
        return "X2 + Under 3.5"
    if selection == "1X + UN":
        return "1X + Under 3.5"
    if market and selection:
        if market == selection or selection in market:
            return market
        if market in selection:
            return selection
        return f"{market}: {selection}"
    return selection or market

def format_portal_slip(t, label_override="In corso"):
    stake = t.get("stake") or t.get("stake_eur") or 0.0
    odds = t.get("total_odds") or 0.0
    
    legs_out = []
    legs_src = t.get("legs") or t.get("selections") or []
    for leg in legs_src:
        ko = leg.get("kickoff") or leg.get("date_time") or "—"
        when_str = ko.replace("2026-", "").replace(" CEST", "").strip()
        match_str = leg.get("match", "")
        pick_str = clean_pick_label(leg)
        odd_str = str(leg.get("odds") or leg.get("quota") or "")
        res_str = leg.get("status") or leg.get("result") or "PENDING"
        score_str = leg.get("score") or ""
        legs_out.append({
            "when": when_str,
            "match": match_str,
            "pick": pick_str,
            "odd": odd_str,
            "result": res_str,
            "score": score_str
        })

    return {
        "id": t.get("ticket_id", ""),
        "title": t.get("title") or t.get("name") or t.get("ticket_id"),
        "label": label_override,
        "stake": f"{float(stake):.2f} €",
        "odds": f"{float(odds):.2f}×",
        "booking_code": t.get("booking_code"),
        "legs": legs_out
    }

# Active tickets for today only
today_ticket_ids = [
    "TICKET_USER_MULTIPLA5_MATTINA_10EUR_12OTT",
    "TICKET_12OTT_CORE_ROCKET",
    "TICKET_12OTT_SATELLITE_MINORI"
]

present_slips = []
for tid in today_ticket_ids:
    matched = next((t for t in tickets if t.get("ticket_id") == tid), None)
    if matched:
        present_slips.append(format_portal_slip(matched, "In corso"))

# As explicitly requested: elimina lo storico del passato sul sito. partiamo da oggi.
# past: completely empty []
# future: []
# profit_label: "0.00 €" (fresh start from today)
portal_data = {
    "generated_at": datetime.now().isoformat(),
    "check_seconds": 30,
    "profit_label": "0.00 €",
    "present": present_slips,
    "future": [],
    "past": []
}

# 3. Write portal/schedine.json
portal_json_path = Path("portal/schedine.json")
with open(portal_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)
print("Updated portal/schedine.json with 0 past tickets and clean present.")

# 4. Write bagent-schedine/schedine.json
mirror_json_path = Path("C:/Project/bagent-schedine/schedine.json")
with open(mirror_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)
print("Updated bagent-schedine/schedine.json.")

# 5. Update HTML #boot in portal/schedine.html
boot_str = json.dumps(portal_data, ensure_ascii=False)

html_path = Path("portal/schedine.html")
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
print("Updated portal/schedine.html.")

# 6. Update HTML #boot in bagent-schedine/index.html
mirror_html_path = Path("C:/Project/bagent-schedine/index.html")
with open(mirror_html_path, "r", encoding="utf-8") as f:
    mh = f.read()
mh = re.sub(
    r'<script type="application/json" id="boot">.*?</script>',
    f'<script type="application/json" id="boot">{boot_str}</script>',
    mh,
    flags=re.DOTALL
)
with open(mirror_html_path, "w", encoding="utf-8") as f:
    f.write(mh)
print("Updated bagent-schedine/index.html.")


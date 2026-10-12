import json
import re
from pathlib import Path
from datetime import datetime

# Path definition
tickets_path = Path("data/active_user_tickets.json")
with open(tickets_path, "r", encoding="utf-8") as f:
    tickets = json.load(f)

# Define the user's played ticket
user_ticket = {
    "ticket_id": "TICKET_USER_MULTIPLA5_MATTINA_10EUR_12OTT",
    "title": "Schedina Reale Utente: Multipla (5) Primo Pomeriggio (@ 6.66)",
    "name": "Schedina Reale Utente: Multipla (5) Primo Pomeriggio (@ 6.66)",
    "bookmaker": "Netwin",
    "type": "Multipla (5)",
    "placed_at": "2026-10-12 10:33 CEST",
    "created_at": "2026-10-12T10:33:00+02:00",
    "date_created": "2026-10-12 10:33:00",
    "status": "IN_PROGRESS",
    "strategy": "USER_PLAYED_TICKET_ASIAN_EASTERN_MIX",
    "stake": 10.0,
    "stake_eur": 10.0,
    "bonus": 4.0,
    "total_odds": 6.66,
    "potential_win": 70.67,
    "potential_payout_eur": 70.67,
    "net_profit_eur": 60.67,
    "settled": False,
    "profit_loss_eur": 0.0,
    "notes": "Schedina reale giocata dall'utente su Netwin. Importo 10 EUR, bonus 4.00 EUR, vincita potenziale 70.67 EUR.",
    "legs": [
        {
            "match": "Fardu Ferghana vs FC Kattaqorgon",
            "tournament": "Uzbekistan Pro Liga",
            "competition": "Uzbekistan Pro Liga",
            "kickoff": "2026-10-12 12:00 CEST",
            "market": "1X2: 1",
            "selection": "1",
            "odds": 1.44,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE",
            "rationale": "Fardu solida tra le mura amiche a Ferghana contro Kattaqorgon in difficolta di classifica."
        },
        {
            "match": "FC Livyi Bereh Kyiv vs Zorya Luhansk",
            "tournament": "Ucraina Premier League",
            "competition": "Ucraina Premier League",
            "kickoff": "2026-10-12 12:00 CEST",
            "market": "X2 + U/O 3.5: X2 + UN",
            "selection": "X2 + Under 3.5",
            "odds": 1.90,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE",
            "rationale": "Zorya esperto contro neopromossa da catenaccio (< 0.8 gol p90). Quota top @ 1.90 su Netwin con piena copertura Forebet 1-1."
        },
        {
            "match": "FK Vojvodina Novi Sad vs FK Jedinstvo Ub",
            "tournament": "Serbia U19 League",
            "competition": "Serbia U19 League",
            "kickoff": "2026-10-12 13:00 CEST",
            "market": "1X2: 1",
            "selection": "1",
            "odds": 1.31,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE",
            "rationale": "Vojvodina U19 dominante a Novi Sad; Jedinstvo Ub U19 fragile in trasferta (reduce da 0-4)."
        },
        {
            "match": "Hougang United FC vs Balestier Khalsa FC",
            "tournament": "Singapore Premier League",
            "competition": "Singapore Premier League",
            "kickoff": "2026-10-12 13:30 CEST",
            "market": "U/O 2.5: Over",
            "selection": "Over 2.5",
            "odds": 1.31,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE",
            "rationale": "Singapore macchina da gol (4.1 reti medie p90). Forebet 2-1 (avg 3.53 gol)."
        },
        {
            "match": "Panionios vs PAOK Thessaloniki B",
            "tournament": "Grecia Super League 2",
            "competition": "Grecia Super League 2",
            "kickoff": "2026-10-12 13:45 CEST",
            "market": "1X + U/O 3.5: 1X + UN",
            "selection": "1X + Under 3.5",
            "odds": 1.42,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE",
            "rationale": "Panionios ermetico ad Atene (0.4 gol concessi p90). Copre l'1-0 esatto e pareggi 0-0/1-1."
        }
    ],
    "selections": [
        {
            "match": "Fardu Ferghana vs FC Kattaqorgon",
            "tournament": "Uzbekistan Pro Liga",
            "kickoff": "2026-10-12 12:00 CEST",
            "market": "1X2: 1",
            "selection": "1",
            "quota": 1.44,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE"
        },
        {
            "match": "FC Livyi Bereh Kyiv vs Zorya Luhansk",
            "tournament": "Ucraina Premier League",
            "kickoff": "2026-10-12 12:00 CEST",
            "market": "X2 + U/O 3.5: X2 + UN",
            "selection": "X2 + UN",
            "quota": 1.90,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE"
        },
        {
            "match": "FK Vojvodina Novi Sad vs FK Jedinstvo Ub",
            "tournament": "Serbia U19 League",
            "kickoff": "2026-10-12 13:00 CEST",
            "market": "1X2: 1",
            "selection": "1",
            "quota": 1.31,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE"
        },
        {
            "match": "Hougang United FC vs Balestier Khalsa FC",
            "tournament": "Singapore Premier League",
            "kickoff": "2026-10-12 13:30 CEST",
            "market": "U/O 2.5: Over",
            "selection": "Over",
            "quota": 1.31,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE"
        },
        {
            "match": "Panionios vs PAOK Thessaloniki B",
            "tournament": "Grecia Super League 2",
            "kickoff": "2026-10-12 13:45 CEST",
            "market": "1X + U/O 3.5: 1X + UN",
            "selection": "1X + UN",
            "quota": 1.42,
            "status": "PENDING",
            "score": "0-0",
            "minute": "PRE"
        }
    ]
}

# Remove if already in list and insert at index 0 (top active)
tickets = [t for t in tickets if t.get("ticket_id") != user_ticket["ticket_id"]]
tickets.insert(0, user_ticket)

# Save active_user_tickets.json
with open(tickets_path, "w", encoding="utf-8") as f:
    json.dump(tickets, f, indent=2, ensure_ascii=False)

print("Saved user ticket to active_user_tickets.json")

# Update portals
def format_portal_slip(t, label_override=None):
    stake = t.get("stake") or t.get("stake_eur") or 0.0
    odds = t.get("total_odds") or 0.0
    status = t.get("status", "PENDING")
    
    if label_override:
        label = label_override
    elif status == "WON":
        label = "Vinta"
    elif status == "LOST":
        label = "Persa"
    elif status in ["PENDING", "IN_PROGRESS"]:
        label = "In corso"
    else:
        label = status

    legs_out = []
    legs_src = t.get("legs") or t.get("selections") or []
    for leg in legs_src:
        ko = leg.get("kickoff") or leg.get("date_time") or "—"
        when_str = ko.replace("2026-", "").replace(" CEST", "").strip()
        match_str = leg.get("match", "")
        pick_str = leg.get("selection") or leg.get("market") or ""
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
        "label": label,
        "stake": f"{float(stake):.2f} €",
        "odds": f"{float(odds):.2f}×",
        "booking_code": t.get("booking_code"),
        "legs": legs_out
    }

# All active tickets for today in present
present_tickets = [t for t in tickets if not t.get("settled")]
present_slips = [format_portal_slip(t, "In corso") for t in present_tickets]

past_tickets = [t for t in tickets if t.get("settled")]
past_slips = [format_portal_slip(t) for t in past_tickets]

total_pnl = sum(float(t.get("profit_loss_eur") or 0.0) for t in past_tickets)
pnl_label = f"{total_pnl:+.2f} €"

portal_data = {
    "generated_at": datetime.now().isoformat(),
    "check_seconds": 30,
    "profit_label": pnl_label,
    "present": present_slips,
    "future": [],
    "past": past_slips
}

# Save portal JSONs
portal_json_path = Path("portal/schedine.json")
with open(portal_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)

mirror_json_path = Path("C:/Project/bagent-schedine/schedine.json")
with open(mirror_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)

# Update HTML #boot
boot_str = json.dumps(portal_data, ensure_ascii=False)

html_path = Path("portal/schedine.html")
with open(html_path, "r", encoding="utf-8") as f:
    h = f.read()
h = re.sub(r'<script type="application/json" id="boot">.*?</script>', f'<script type="application/json" id="boot">{boot_str}</script>', h, flags=re.DOTALL)
with open(html_path, "w", encoding="utf-8") as f:
    f.write(h)

mirror_html = Path("C:/Project/bagent-schedine/index.html")
with open(mirror_html, "r", encoding="utf-8") as f:
    mh = f.read()
mh = re.sub(r'<script type="application/json" id="boot">.*?</script>', f'<script type="application/json" id="boot">{boot_str}</script>', mh, flags=re.DOTALL)
with open(mirror_html, "w", encoding="utf-8") as f:
    f.write(mh)

print("Updated portal/schedine.html and bagent-schedine/index.html")

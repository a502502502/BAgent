import json
import re
from pathlib import Path
from datetime import datetime

# 1. Load active_user_tickets.json
tickets_path = Path("data/active_user_tickets.json")
with open(tickets_path, "r", encoding="utf-8") as f:
    tickets = json.load(f)

print(f"Loaded {len(tickets)} tickets from active_user_tickets.json")

# 2. Settle any unfinished tickets older than today (12 Ottobre)
for t in tickets:
    tid = t.get("ticket_id", "")
    if not t.get("settled"):
        # If it belongs to 10 or 11 October, mark settled
        if any(k in tid for k in ["10OTT", "11OTT", "WEEKEND_TIPSTER"]):
            t["settled"] = True
            if t.get("status") in ["PENDING", "IN_PROGRESS"]:
                t["status"] = "LOST"
                stake = float(t.get("stake") or t.get("stake_eur") or 0.0)
                t["profit_loss_eur"] = -stake
            print(f"Archived past ticket: {tid} -> {t['status']}")

# 3. Create today's 3 new tickets (12 Ottobre 2026)
ticket_core_12oct = {
    "ticket_id": "TICKET_12OTT_CORE_ROCKET",
    "title": "Schedina 1: Il Core Rocket (Lunedì 12 Ottobre)",
    "name": "Schedina 1: Il Core Rocket (Lunedì 12 Ottobre)",
    "created_at": "2026-10-12T09:40:00+02:00",
    "date_created": "2026-10-12 09:40:00",
    "status": "PENDING",
    "strategy": "CORE_ROCKET_POWER_GROWTH",
    "stake_eur": 25.0,
    "total_odds": 2.58,
    "potential_payout_eur": 64.50,
    "potential_win": 64.50,
    "net_profit_eur": 39.50,
    "settled": False,
    "profit_loss_eur": 0.0,
    "notes": "Asse portante del piano a medio rischio (8.3% del budget 300 EUR). Tripla asimmetrica a protezione rinforzata su Serie A e Allsvenskan.",
    "legs": [
        {
            "match": "Atalanta vs Venezia",
            "tournament": "Italia Serie A",
            "competition": "Italia Serie A",
            "market": "Combo: 1X + Under 4.5",
            "selection": "1X + Under 4.5",
            "odds": 1.36,
            "kickoff": "2026-10-12 18:30 CEST",
            "status": "PENDING",
            "rationale": "Dea superiore al Gewiss Stadium. Copre tutte le vittorie standard (1-0, 2-0, 2-1, 3-0, 3-1) e pareggio 1-1/0-0. Consenso Oddspedia Under 3.5 e Forebet 2-0."
        },
        {
            "match": "Malmo FF vs Kalmar",
            "tournament": "Svezia Allsvenskan",
            "competition": "Svezia Allsvenskan",
            "market": "Combo: 1X + MultiGol 1-5",
            "selection": "1X + MultiGol 1-5",
            "odds": 1.32,
            "kickoff": "2026-10-12 19:00 CEST",
            "status": "PENDING",
            "rationale": "Malmo in volata vertice contro il fanalino Kalmar. La protezione MultiGol 1-5 assorbe la vittoria con qualsiasi scarto ed evita la trappola dell'Over 1.5 in caso di 1-0 stretto."
        },
        {
            "match": "Torino vs Udinese",
            "tournament": "Italia Serie A",
            "competition": "Italia Serie A",
            "market": "MultiGol Tempi: 0-2 1°T + 1-3 2°T",
            "selection": "SI",
            "odds": 1.44,
            "kickoff": "2026-10-12 20:45 CEST",
            "status": "PENDING",
            "rationale": "Posticipo tattico Vanoli vs Runjaic. Primo tempo guardingo (0-2 gol) e ripresa aperta con concessione (1-3 gol). Intercetta l'1-2 di Forebet e il Gol di Oddspedia."
        }
    ]
}

ticket_sat_minori_12oct = {
    "ticket_id": "TICKET_12OTT_SATELLITE_MINORI",
    "title": "Schedina 2: Il Satellite Moltiplicatore Minori (Lunedì 12 Ottobre)",
    "name": "Schedina 2: Il Satellite Moltiplicatore Minori (Lunedì 12 Ottobre)",
    "created_at": "2026-10-12T09:40:00+02:00",
    "date_created": "2026-10-12 09:40:00",
    "status": "PENDING",
    "strategy": "SATELLITE_MULTIPLIER_MINOR_LEAGUES",
    "stake_eur": 7.0,
    "total_odds": 6.06,
    "potential_payout_eur": 42.42,
    "potential_win": 42.42,
    "net_profit_eur": 35.42,
    "settled": False,
    "profit_loss_eur": 0.0,
    "notes": "Leva asimmetrica a micro-stake (2.3% del budget 300 EUR). Pentaleg su campionati minori e coppe internazionali con quote di valore protette.",
    "legs": [
        {
            "match": "Real Valladolid vs Albacete",
            "tournament": "Spagna LaLiga 2",
            "competition": "Spagna LaLiga 2",
            "market": "Combo: 1X + Under 3.5",
            "selection": "1X + Under 3.5",
            "odds": 1.48,
            "kickoff": "2026-10-12 14:00 CEST",
            "status": "PENDING",
            "rationale": "Valladolid solidissimo al José Zorrilla (< 0.9 xG concessi p90). Forebet 2-1 (82% 1X)."
        },
        {
            "match": "Al Wasl vs Al Ahli SC",
            "tournament": "AFC Champions League",
            "competition": "AFC Champions League",
            "market": "Combo: X2 + Over 1.5",
            "selection": "X2 + Over 1.5",
            "odds": 1.45,
            "kickoff": "2026-10-12 18:00 CEST",
            "status": "PENDING",
            "rationale": "Superiorità tecnica netta dei sauditi (Mahrez, Firmino, Toney) contro la difesa vulnerabile dell'Al Wasl."
        },
        {
            "match": "Universitatea Cluj vs Rapid Bucuresti",
            "tournament": "Romania Superliga",
            "competition": "Romania Superliga",
            "market": "Chance Mix: X o Gol",
            "selection": "X o Gol",
            "odds": 1.44,
            "kickoff": "2026-10-12 20:00 CEST",
            "status": "PENDING",
            "rationale": "Scontro diretto di vertice romeno: alta frequenza di pareggio o reazione reciproca."
        },
        {
            "match": "Pescara vs Guidonia",
            "tournament": "Italia Serie C Girone B",
            "competition": "Italia Serie C Girone B",
            "market": "Combo: 1X + Under 3.5",
            "selection": "1X + Under 3.5",
            "odds": 1.38,
            "kickoff": "2026-10-12 20:30 CEST",
            "status": "PENDING",
            "rationale": "Pescara capolista all'Adriatico contro neopromossa organizzata. Divario di passo evidente."
        },
        {
            "match": "Coventry vs Newcastle",
            "tournament": "Inghilterra Premier League",
            "competition": "Inghilterra Premier League",
            "market": "Combo: X2 + Under 4.5",
            "selection": "X2 + Under 4.5",
            "odds": 1.42,
            "kickoff": "2026-10-12 21:00 CEST",
            "status": "PENDING",
            "rationale": "Magpies di caratura superiore ma Coventry difende a blocco basso. Protezione Under 4.5 molto profonda."
        }
    ]
}

ticket_sat_mattina_12oct = {
    "ticket_id": "TICKET_12OTT_SATELLITE_MATTINA",
    "title": "Schedina 3: Satellite Anticipi Mattutini (Lunedì 12 Ottobre)",
    "name": "Schedina 3: Satellite Anticipi Mattutini (Lunedì 12 Ottobre)",
    "created_at": "2026-10-12T09:40:00+02:00",
    "date_created": "2026-10-12 09:40:00",
    "status": "PENDING",
    "strategy": "SATELLITE_MORNING_EARLY_KICKOFF",
    "stake_eur": 5.0,
    "total_odds": 3.55,
    "potential_payout_eur": 17.75,
    "potential_win": 17.75,
    "net_profit_eur": 12.75,
    "settled": False,
    "profit_loss_eur": 0.0,
    "notes": "Micro-satellite di copertura fascia 12:00 - 14:00 (1.6% budget). Selezioni certificate da triangolazione Forebet + Oddspedia.",
    "legs": [
        {
            "match": "Livyi Bereg vs Zorya Luhansk",
            "tournament": "Ucraina Premier League",
            "competition": "Ucraina Premier League",
            "market": "Combo: X2 + Under 3.5",
            "selection": "X2 + Under 3.5",
            "odds": 1.45,
            "kickoff": "2026-10-12 12:00 CEST",
            "status": "PENDING",
            "rationale": "Zorya club esperto contro neopromossa da catenaccio (< 0.8 gol p90). Forebet ex. score 1-1, X2 all'82%."
        },
        {
            "match": "Dynamo Kyiv U21 vs Karpaty U21",
            "tournament": "Ucraina Premier League U21",
            "competition": "Ucraina Premier League U21",
            "market": "Combo: 1X + Over 1.5",
            "selection": "1X + Over 1.5",
            "odds": 1.35,
            "kickoff": "2026-10-12 12:00 CEST",
            "status": "PENDING",
            "rationale": "Primavera Dinamo Kiev imbattuta con media > 2.8 gol segnati a partita."
        },
        {
            "match": "Hougang vs Balestier Khalsa",
            "tournament": "Singapore Premier League",
            "competition": "Singapore Premier League",
            "market": "Totale Gol",
            "selection": "Over 2.5",
            "odds": 1.38,
            "kickoff": "2026-10-12 13:30 CEST",
            "status": "PENDING",
            "rationale": "Lega con la media gol più alta d'Asia (4.1 gol p90). Forebet ex. score 2-1 (avg 3.53)."
        },
        {
            "match": "Panionios vs PAOK B",
            "tournament": "Grecia Super League 2",
            "competition": "Grecia Super League 2",
            "market": "Combo: 1X + Under 3.5",
            "selection": "1X + Under 3.5",
            "odds": 1.32,
            "kickoff": "2026-10-12 13:45 CEST",
            "status": "PENDING",
            "rationale": "Panionios ermetico ad Atene (0.4 gol concessi p90). Forebet ex. score 1-0 (avg 0.63)."
        }
    ]
}

# Remove if already existing and insert at the top
existing_ids = {ticket_core_12oct["ticket_id"], ticket_sat_minori_12oct["ticket_id"], ticket_sat_mattina_12oct["ticket_id"]}
tickets = [t for t in tickets if t.get("ticket_id") not in existing_ids]

# Put new tickets at the beginning
tickets.insert(0, ticket_core_12oct)
tickets.insert(1, ticket_sat_minori_12oct)
tickets.insert(2, ticket_sat_mattina_12oct)

# Save active_user_tickets.json
with open(tickets_path, "w", encoding="utf-8") as f:
    json.dump(tickets, f, indent=2, ensure_ascii=False)

print("Saved active_user_tickets.json with today's tickets.")

# 4. Build clean portal JSON
# present: strictly tickets created today (12 Ottobre)
# future: empty
# past: all settled tickets
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

present_slips = [
    format_portal_slip(ticket_core_12oct, "In corso"),
    format_portal_slip(ticket_sat_minori_12oct, "In corso"),
    format_portal_slip(ticket_sat_mattina_12oct, "In corso")
]

past_slips = []
# All other tickets in active_user_tickets.json that are settled
for t in tickets[3:]:
    if t.get("settled"):
        past_slips.append(format_portal_slip(t))

# Calculate total profit/loss on settled tickets
settled_tickets = [t for t in tickets if t.get("settled")]
total_pnl = sum(float(t.get("profit_loss_eur") or 0.0) for t in settled_tickets)
pnl_label = f"{total_pnl:+.2f} €"

portal_data = {
    "generated_at": datetime.now().isoformat(),
    "check_seconds": 30,
    "profit_label": pnl_label,
    "present": present_slips,
    "future": [],
    "past": past_slips
}

# Write portal/schedine.json
portal_json_path = Path("portal/schedine.json")
with open(portal_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)
print("Updated portal/schedine.json")

# Write bagent-schedine/schedine.json
mirror_json_path = Path("C:/Project/bagent-schedine/schedine.json")
with open(mirror_json_path, "w", encoding="utf-8") as f:
    json.dump(portal_data, f, indent=2, ensure_ascii=False)
print("Updated bagent-schedine/schedine.json")

# Update portal/schedine.html #boot script
html_path = Path("portal/schedine.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

boot_json_str = json.dumps(portal_data, ensure_ascii=False)
html_content = re.sub(
    r'<script type="application/json" id="boot">.*?</script>',
    f'<script type="application/json" id="boot">{boot_json_str}</script>',
    html_content,
    flags=re.DOTALL
)

with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)
print("Updated portal/schedine.html")

# Update bagent-schedine/index.html
mirror_html_path = Path("C:/Project/bagent-schedine/index.html")
with open(mirror_html_path, "r", encoding="utf-8") as f:
    mirror_content = f.read()

mirror_content = re.sub(
    r'<script type="application/json" id="boot">.*?</script>',
    f'<script type="application/json" id="boot">{boot_json_str}</script>',
    mirror_content,
    flags=re.DOTALL
)

with open(mirror_html_path, "w", encoding="utf-8") as f:
    f.write(mirror_content)
print("Updated bagent-schedine/index.html")


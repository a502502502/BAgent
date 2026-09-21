import sqlite3
import json
import datetime
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
db_path = root / "storage" / "database" / "bagent.db"
tickets_file = root / "data" / "active_user_tickets.json"

now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

# 1. Update active_user_tickets.json
with open(tickets_file, "r", encoding="utf-8") as f:
    tickets = json.load(f)

new_ticket = {
    "ticket_id": "TICKET_VERE_GEMME_21SET",
    "date_created": now_iso,
    "stake_eur": 10.0,
    "total_odds": 4.74,
    "potential_payout_eur": 47.40,
    "status": "IN_PLAY",
    "strategy": "REAL_NICHE_GEMS",
    "legs": [
        {
            "id": "686",
            "match": "Mert Aysegul vs Shinikova Isabella",
            "tournament": "WTA 125K Ankara",
            "market": "Handicap -2.5 Game Shinikova",
            "odds": 1.73,
            "status": "PENDING",
            "kickoff": "16:30 CEST"
        },
        {
            "id": "4915",
            "match": "Arnaboldi Federico vs Broska Florian",
            "tournament": "Challenger Genova",
            "market": "2 Fisso Broska Florian",
            "odds": 1.66,
            "status": "PENDING",
            "kickoff": "17:30 CEST"
        },
        {
            "id": "8742",
            "match": "Trento vs Pro Vercelli",
            "tournament": "Italia Serie C Girone A",
            "market": "MultiGol 1-2 Casa Trento (Boost)",
            "odds": 1.65,
            "status": "PENDING",
            "kickoff": "20:30 CEST"
        }
    ]
}

tickets.append(new_ticket)
with open(tickets_file, "w", encoding="utf-8") as f:
    json.dump(tickets, f, indent=2, ensure_ascii=False)

# 2. Check DB columns
conn = sqlite3.connect(db_path)
cur = conn.cursor()

cur.execute("PRAGMA table_info(ticket_ledger)")
cols = [c[1] for c in cur.fetchall()]
print("ticket_ledger columns:", cols)

cur.execute("PRAGMA table_info(bet_leg_ledger)")
leg_cols = [c[1] for c in cur.fetchall()]
print("bet_leg_ledger columns:", leg_cols)

# Insert ticket matching schema
cur.execute("""
    INSERT OR REPLACE INTO ticket_ledger (ticket_id, date_created, description, num_legs, total_odds, stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
""", ("TICKET_VERE_GEMME_21SET", now_iso, "Tris Vere Gemme Tennis & Calcio (Ankara, Genova, Trento)", 3, 4.74, 10.0, 47.40, 0.0, "IN_PLAY", "REAL_NICHE_GEMS", "Netwin Verified Odds"))

# Insert legs
legs_data = [
    ("TICKET_VERE_GEMME_21SET", "Mert Aysegul vs Shinikova Isabella", "WTA 125K Ankara", "HANDICAP", "Handicap -2.5 Game Shinikova", 1.73, 0.68, 17.6, "PENDING", 0.0),
    ("TICKET_VERE_GEMME_21SET", "Arnaboldi Federico vs Broska Florian", "Challenger Genova", "1X2", "2 Fisso Broska Florian", 1.66, 0.69, 14.5, "PENDING", 0.0),
    ("TICKET_VERE_GEMME_21SET", "Trento vs Pro Vercelli", "Italia Serie C Girone A", "MULTIGOL", "MultiGol 1-2 Casa Trento (Boost)", 1.65, 0.71, 17.1, "PENDING", 0.0)
]

for row in legs_data:
    cur.execute("""
        INSERT INTO bet_leg_ledger (ticket_id, match_name, tournament, market_category, selection, odds, estimated_prob, edge_pct, result_status, clv_pct)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, row)

conn.commit()
conn.close()
print("Ticket e 3 Legs registrati con successo in SQLite!")

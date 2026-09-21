import sqlite3
import json
from pathlib import Path

root = Path("C:/Users/demarj/.gemini/antigravity/scratch/BAgent")
db_path = root / "storage" / "database" / "bagent.db"
tickets_file = root / "data" / "active_user_tickets.json"

# Remove from json
with open(tickets_file, "r", encoding="utf-8") as f:
    tickets = json.load(f)

tickets = [t for t in tickets if not (isinstance(t, dict) and t.get("ticket_id") == "TICKET_GEMME_POMERIGGIO_21SET")]

with open(tickets_file, "w", encoding="utf-8") as f:
    json.dump(tickets, f, indent=2, ensure_ascii=False)

# Remove from sqlite
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("DELETE FROM ticket_ledger WHERE ticket_id = 'TICKET_GEMME_POMERIGGIO_21SET'")
cur.execute("DELETE FROM bet_leg_ledger WHERE ticket_id = 'TICKET_GEMME_POMERIGGIO_21SET'")
conn.commit()
conn.close()

print("TICKET_GEMME_POMERIGGIO_21SET eliminato con successo dal sistema!")

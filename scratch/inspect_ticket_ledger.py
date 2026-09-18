import sqlite3

conn = sqlite3.connect("storage/database/bagent.db")
c = conn.cursor()
c.execute("PRAGMA table_info(ticket_ledger);")
print("ticket_ledger columns:", [x[1] for x in c.fetchall()])

c.execute("SELECT * FROM ticket_ledger ORDER BY id DESC LIMIT 5;")
for row in c.fetchall():
    print(row)

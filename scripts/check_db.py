import sqlite3

conn = sqlite3.connect("data/bagent.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in c.fetchall()]
print("Tables in bagent.db:", tables)
for t in ["matches", "team_stats", "teams", "simulated_tickets", "tipster_tickets", "tickets", "tracked_fixtures"]:
    if t in tables:
        c.execute(f"SELECT count(*) FROM {t}")
        print(f"Count {t}:", c.fetchone()[0])

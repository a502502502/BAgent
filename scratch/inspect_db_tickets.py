import sqlite3

conn = sqlite3.connect("storage/database/bagent.db")
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", c.fetchall())

for table in ["tickets", "bets", "bet_legs", "sessions", "predictions"]:
    try:
        c.execute(f"PRAGMA table_info({table});")
        info = c.fetchall()
        if info:
            print(f"Table {table}:", [x[1] for x in info])
            c.execute(f"SELECT COUNT(*) FROM {table}")
            print(f"Count {table}:", c.fetchone()[0])
            c.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT 3")
            print(f"Sample {table}:", c.fetchall())
    except Exception as e:
        print(f"Error {table}: {e}")

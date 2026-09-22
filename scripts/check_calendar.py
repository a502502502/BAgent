import sqlite3
from pathlib import Path

db_path = Path("data/bagent.db")
if db_path.exists():
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    tables = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    print("Tables:", tables)
    for t in tables:
        try:
            cnt = cur.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            print(f"Table {t}: {cnt} rows")
            cols = [c[1] for c in cur.execute(f"PRAGMA table_info({t})").fetchall()]
            print(f"  Columns: {cols}")
        except Exception as e:
            print(f"  Error on {t}: {e}")
else:
    print("No data/bagent.db found")

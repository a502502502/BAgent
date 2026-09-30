import sys
import sqlite3
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect('data/bagent.db')
c = conn.cursor()

print("=== Partite in DB per 2026-10-02 ===")
q = "SELECT date_gmt, league, home_team, away_team, status FROM matches WHERE date_gmt LIKE '2026-10-02%' ORDER BY league"
for row in c.execute(q):
    print(" ", row)

print("\n=== Partite in DB per UEFA Nations League (tutte le date ottobre 2026) ===")
q2 = "SELECT date_gmt, home_team, away_team, status FROM matches WHERE league LIKE '%Nations League%' AND date_gmt LIKE '2026-10%' ORDER BY date_gmt"
for row in c.execute(q2):
    print(" ", row)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.betting.netwin_cache_reader import load_cached_matches
matches = load_cached_matches()
print(f"\n=== Partite in Netwin Cache per 20261002 (totale matches in cache: {len(matches)}) ===")
oct2_cached = [m for m in matches if "20261002" in m.kickoff]
for m in oct2_cached:
    print(f"  {m.tournament:<30} | {m.match_name:<35} | {m.kickoff} | Odds: {len(m.odds_dict)}")

import sys
import sqlite3

sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.betting.netwin_cache_reader import load_cached_matches

conn = sqlite3.connect('data/bagent.db')
cursor = conn.cursor()

# Verifichiamo le statistiche generali sui primi tempi in Nations League
cursor.execute("""
    SELECT 
        COUNT(*),
        AVG(home_goals_ht + away_goals_ht),
        SUM(CASE WHEN (home_goals_ht + away_goals_ht) = 0 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        SUM(CASE WHEN (home_goals_ht + away_goals_ht) <= 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        SUM(CASE WHEN (home_goals_ht + away_goals_ht) >= 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*),
        SUM(CASE WHEN (home_goals_ht + away_goals_ht) >= 2 THEN 1 ELSE 0 END) * 100.0 / COUNT(*)
    FROM matches
    WHERE league LIKE '%Nations League%' AND status='FT'
""")
row = cursor.fetchone()
print("=========================================================================================")
print("⏱️ STATISTICHE 1° TEMPO — UEFA NATIONS LEAGUE 2026/27 (52 Partite FT)")
print("=========================================================================================")
print(f"• Media Gol 1° Tempo: {row[1]:.2f} gol a partita")
print(f"• Frequenza 0-0 al 45': {row[2]:.1f}%")
print(f"• Frequenza MultiGol 0-1 1°T (max 1 gol): {row[3]:.1f}%")
print(f"• Frequenza Over 0.5 1°T (almeno 1 gol): {row[4]:.1f}%")
print(f"• Frequenza Over 1.5 1°T (2 o più gol): {row[5]:.1f}%\n")

matches = load_cached_matches(tournament='Nations League')
oct1 = [m for m in matches if '20261001' in m.kickoff]

for m in oct1:
    ht_mkts = {k: v for k, v in m.odds_dict.items() if any(w in k.lower() for w in ['1° tempo', '1 tempo', '1t'])}
    print(f"⚽ {m.match_name} ({len(ht_mkts)} mercati 1°T):")
    for k, v in sorted(ht_mkts.items(), key=lambda x: x[1]):
        print(f"   • {k:<30} @ {v}")
    print()

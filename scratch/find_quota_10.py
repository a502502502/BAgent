import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.betting.netwin_cache_reader import load_cached_matches

matches = load_cached_matches(tournament='Nations League')
oct1_2 = [m for m in matches if '20261001' in m.kickoff or '20261002' in m.kickoff]

print("=========================================================================================")
print("🎯 CANDIDATI QUOTA 1.45 - 1.75 PER SCHEDINA A QUOTA 10")
print("=========================================================================================\n")

for m in sorted(oct1_2, key=lambda x: x.kickoff):
    good_picks = []
    for k, v in m.odds_dict.items():
        if 1.45 <= v <= 1.75:
            lower = k.lower()
            if any(w in lower for w in [
                '1x + multigol', 'x2 + multigol', '1 + over', '2 + over', '1x + over 1.5', 'x2 + over 1.5',
                'multigol 2-4', 'multigol 2-5', '1 1° tempo', 'over 2.5', 'gol', 'multigol 1-3 ospite',
                '1 + under 4.5', '2 + under 4.5', '1x + multigol 2-4', 'x2 + multigol 2-5', 'x2 + multigol 1-4'
            ]):
                good_picks.append((k, v))
    if good_picks:
        print(f"⚽ {m.match_name} ({m.kickoff[:8]}):")
        for k, v in sorted(good_picks, key=lambda x: x[1])[:6]:
            print(f"   • {k:<32} @ {v}")

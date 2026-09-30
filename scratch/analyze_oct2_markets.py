import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.betting.netwin_cache_reader import load_cached_matches

matches = load_cached_matches(tournament='Nations League')
oct2 = [m for m in matches if '20261002' in m.kickoff]

print("=========================================================================================")
print("🔍 ANALISI QUOTE CHIAVE — UEFA NATIONS LEAGUE (02 OTTOBRE 2026)")
print("=========================================================================================\n")

for m in sorted(oct2, key=lambda x: x.kickoff):
    print(f"⚽ {m.match_name} ({m.kickoff})")
    core = ['1', 'X', '2', '1X', 'X2', '12', 'Over 1.5', 'Under 1.5', 'Over 2.5', 'Under 2.5', 'Gol', 'NoGol']
    odds_str = " | ".join(f"{k}: {m.odds_dict.get(k)}" for k in core if k in m.odds_dict)
    print(f"   {odds_str}")
    
    # Cerchiamo combo protette e multigol interessanti
    combos = []
    for k, v in m.odds_dict.items():
        if 1.20 <= v <= 1.70:
            lower = k.lower()
            if any(w in lower for w in ['1x + multigol', 'x2 + multigol', '1 + over', '2 + over', 'multigol 1-3 ospite', 'multigol 2-5 casa', 'x2 + over 1.5', '1x + over 1.5', '1 + under 4.5', '2 + under 4.5']):
                combos.append((k, v))
    if combos:
        combos.sort(key=lambda x: x[1])
        print("   🔹 Top Combo Protette:")
        for c in combos[:6]:
            print(f"      • {c[0]:<30} @ {c[1]}")
    print()

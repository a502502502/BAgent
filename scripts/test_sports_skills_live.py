import sys
sys.stdout.reconfigure(encoding='utf-8')
from sports_skills import football

try:
    comps = football.get_competitions()
    print("Competitions count:", len(comps) if isinstance(comps, list) else "type: " + str(type(comps)))
    if isinstance(comps, list) and comps:
        print("Sample competitions:", comps[:5])
    else:
        print("Comps raw:", str(comps)[:300])
except Exception as e:
    print("Error calling get_competitions:", e)

try:
    from sports_skills import betting
    print("betting dir:", [d for d in dir(betting) if not d.startswith("_")])
except Exception as e:
    print("betting error:", e)

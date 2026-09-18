import sys
sys.path.insert(0, ".")
from services.football.external.sources.flashscore_live import FlashscoreLiveEngine

engine = FlashscoreLiveEngine()
matches = engine.fetch_feed()
print("Total matches from Flashscore feed:", len(matches))
keywords = ['chernomorets', 'obolon', 'zhejiang', 'wuhan', 'saudi', 'qatar', 'yavne', 'herzelia', 'polissya', 'kryvbas', 'highbury', 'gomora', 'hapoel']
for m in matches:
    txt = (m['home'] + ' ' + m['away']).lower()
    for kw in keywords:
        if kw in txt:
            print(f"FOUND: {m['home']} vs {m['away']} | Score: {m['score']} | Status: {m['status']} | Period: {m['period']} | ID: {m['match_id']}")
            break

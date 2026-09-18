import sys, json
sys.path.insert(0, ".")
from services.football.external.sources.flashscore_live import FlashscoreLiveEngine
import urllib.request

req = urllib.request.Request("https://local-it.flashscore.ninja/2/x/feed/f_1_0_1_it_1", headers=FlashscoreLiveEngine.HEADERS)
with urllib.request.urlopen(req, timeout=10) as resp:
    text = resp.read().decode("utf-8", errors="ignore")

blocks = text.split("~AA÷")
for b in blocks[1:]:
    fields = {}
    for p in b.split("¬"):
        if "÷" in p:
            k, v = p.split("÷", 1)
            fields[k] = v
    home = fields.get("AE", "")
    away = fields.get("AF", "")
    txt = (home + " " + away).lower()
    for kw in ["saudi", "zhejiang", "odesa", "yavne"]:
        if kw in txt:
            print(f"=== {home} vs {away} ===")
            for k, v in fields.items():
                print(f"  {k}: {v}")
            break

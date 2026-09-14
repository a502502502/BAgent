"""
Test what FootyStats actually returns right now for matches around 14:00 - 14:30.
"""

import urllib.request
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

key = "test85g57"

print("=== VERIFICA FOOTYSTATS SULLE PARTITE DELLE 14:00 / 14:30 ===")

# 1. Test chiamata a todays-matches con FootyStats
url_today = f"https://api.football-data-api.com/todays-matches?key={key}"
print(f"1. Chiamata a /todays-matches (API FootyStats):")
try:
    req = urllib.request.Request(url_today, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        data = res.get("data", [])
        status = res.get("status")
        msg = res.get("message", "")
        print(f"   Risposta API: Status={status}, Partite restituite={len(data)}")
        if len(data) == 0:
            print(f"   Messaggio FootyStats: '{msg}'")
            print("   ⚠️ Esito: L'endpoint /todays-matches con la chiave di prova 'test85g57' restituisce 0 partite.")
            print("      (La chiave trial non include il feed live giornaliero di oggi).")
except Exception as e:
    print(f"   Errore: {e}")

# 2. Test ricerca del campionato ucraino (Dynamo Kyiv delle 14:30) nell'elenco campionati
print(f"\n2. Ricerca campionato Ucraina Premier League (ID campionato):")
url_leagues = f"https://api.football-data-api.com/league-list?key={key}"
try:
    req = urllib.request.Request(url_leagues, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        leagues = res.get("data", [])
        ukraine_leagues = [l for l in leagues if "ukraine" in l.get("country", "").lower()]
        print(f"   Campionati ucraini registrati in FootyStats: {len(ukraine_leagues)}")
        for l in ukraine_leagues[:3]:
            print(f"   - {l.get('name')} ({l.get('country')})")
except Exception as e:
    print(f"   Errore: {e}")

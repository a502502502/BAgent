"""
FootyStats API Connector & Health Checker.
Tests API connection using FOOTYSTATS_API_KEY from .env or environment.
"""

import os
import sys
import json
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Try loading .env
env_path = Path(__file__).parent.parent / ".env"
api_key = os.environ.get("FOOTYSTATS_API_KEY")

if not api_key and env_path.exists():
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("FOOTYSTATS_API_KEY="):
                api_key = line.split("=", 1)[1].strip()

def check_footystats(key: str = None):
    print("=== FOOTYSTATS CONNECTION CHECK ===")
    if not key:
        print("❌ Nessuna FOOTYSTATS_API_KEY trovata nel file .env o nelle variabili d'ambiente.")
        print("ℹ️ Per collegare FootyStats via API:")
        print("   1. Vai su https://footystats.org/api/ e copia la tua API Key.")
        print("   2. Inseriscila nel file .env aggiungendo la riga: FOOTYSTATS_API_KEY=la_tua_chiave")
        return False

    url = f"https://api.football-data-api.com/todays-matches?key={key}"
    print(f"📡 Test chiamata a: https://api.football-data-api.com/todays-matches?key={key[:5]}...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "BAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            status = data.get("status", False)
            message = data.get("message", "")
            if status == 200 or status is True or "data" in data:
                print("✅ Connessione FootyStats API RIUSCITA!")
                print(f"📊 Partite disponibili oggi: {len(data.get('data', []))}")
                return True
            else:
                print(f"⚠️ Risposta API non valida: {message or data}")
                return False
    except Exception as e:
        print(f"❌ Errore durante la chiamata API: {e}")
        return False

if __name__ == "__main__":
    check_footystats(api_key)

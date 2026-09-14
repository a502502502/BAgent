"""
services/football/external/footystats_client.py — Client Ufficiale per API FootyStats.
Estrae classifiche reali, statistiche xG, medie gol e metriche certificate
direttamente dai server di FootyStats (https://api.football-data-api.com/).
"""

from __future__ import annotations
import os
import sys
import json
import urllib.request
import urllib.parse
from typing import Dict, List, Any, Optional
from pathlib import Path

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

class FootyStatsClient:
    BASE_URL = "https://api.football-data-api.com"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("FOOTYSTATS_API_KEY")
        if not self.api_key:
            env_path = Path(__file__).parent.parent.parent.parent / ".env"
            if env_path.exists():
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("FOOTYSTATS_API_KEY="):
                            self.api_key = line.split("=", 1)[1].strip()

    def _call(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.api_key:
            print("⚠️ [FootyStats] Nessuna API Key configurata.")
            return None
        
        all_params = {"key": self.api_key, **params}
        query_str = urllib.parse.urlencode(all_params)
        url = f"{self.BASE_URL}/{endpoint}?{query_str}"
        
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BAgent-FootyStats-Client/2.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except Exception as e:
            print(f"❌ [FootyStats] Errore chiamata {endpoint}: {e}")
            return None

    def get_league_list(self) -> List[Dict[str, Any]]:
        """Restituisce l'elenco di tutti i campionati monitorati da FootyStats."""
        res = self._call("league-list", {})
        if res and "data" in res and isinstance(res["data"], list):
            return res["data"]
        return []

    def get_league_table(self, league_id: int) -> List[Dict[str, Any]]:
        """Restituisce la classifica ufficiale certificata per un determinato league_id."""
        res = self._call("league-tables", {"league_id": league_id})
        if res and "data" in res:
            return res["data"].get("all_matches_table_overall", [])
        return []

    def get_match_stats(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Restituisce le statistiche approfondite (xG, tiri, possesso) di un match."""
        res = self._call("match", {"match_id": match_id})
        if res and "data" in res:
            return res["data"]
        return None

if __name__ == "__main__":
    client = FootyStatsClient()
    leagues = client.get_league_list()
    print(f"✅ FootyStats Client attivo! Campionati disponibili: {len(leagues)}")

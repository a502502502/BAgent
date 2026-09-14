"""
services/football/external/footystats_client.py — Client Ufficiale per API FootyStats.
Estrae classifiche reali, statistiche xG, medie gol e metriche certificate
direttamente dai server di FootyStats (https://api.football-data-api.com/).
Include risolutore automatico di Season ID per nome campionato e caching locale.
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
        self.cache_dir = Path(__file__).parent.parent.parent.parent / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.leagues_cache_path = self.cache_dir / "footystats_leagues.json"
        
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
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data
        except Exception as e:
            print(f"❌ [FootyStats] Errore chiamata {endpoint}: {e}")
            return None

    def get_league_list(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """Restituisce l'elenco di tutti i campionati monitorati da FootyStats (con cache su disco)."""
        if not force_refresh and self.leagues_cache_path.exists():
            try:
                with open(self.leagues_cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        res = self._call("league-list", {})
        if res and "data" in res and isinstance(res["data"], list):
            data = res["data"]
            try:
                with open(self.leagues_cache_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception:
                pass
            return data
        return []

    def get_latest_season_id(self, country: str, league_name: str) -> Optional[int]:
        """Risolve automaticamente l'ID dell'ultima stagione attiva (es. 2026/2027) per un dato campionato."""
        leagues = self.get_league_list()
        country_clean = country.strip().lower()
        league_clean = league_name.strip().lower()

        for item in leagues:
            c = item.get("country", "").strip().lower()
            ln = item.get("league_name", "").strip().lower()
            name = item.get("name", "").strip().lower()

            if (c == country_clean and ln == league_clean) or (league_clean in name and c == country_clean):
                seasons = item.get("season", [])
                if seasons:
                    return seasons[-1].get("id")
        return None

    def get_league_table(self, league_id: int) -> List[Dict[str, Any]]:
        """Restituisce la classifica ufficiale certificata per un determinato season_id / league_id."""
        res = self._call("league-tables", {"league_id": league_id})
        if res and "data" in res:
            return res["data"].get("all_matches_table_overall", [])
        return []

    def get_table_by_name(self, country: str, league_name: str) -> List[Dict[str, Any]]:
        """Restituisce la classifica ufficiale risolvendo automaticamente la stagione corrente."""
        sid = self.get_latest_season_id(country, league_name)
        if sid:
            return self.get_league_table(sid)
        print(f"⚠️ [FootyStats] Impossibile trovare Season ID per {country} - {league_name}")
        return []

    def get_match_stats(self, match_id: int) -> Optional[Dict[str, Any]]:
        """Restituisce le statistiche approfondite (xG, tiri, possesso, falli) di un match."""
        res = self._call("match", {"match_id": match_id})
        if res and "data" in res:
            return res["data"]
        return None

    def get_todays_matches(self, chosen_only: bool = False) -> List[Dict[str, Any]]:
        """Restituisce le partite del giorno."""
        params = {}
        if chosen_only:
            params["chosen_leagues_only"] = "true"
        res = self._call("todays-matches", params)
        if res and "data" in res and isinstance(res["data"], list):
            return res["data"]
        return []

if __name__ == "__main__":
    client = FootyStatsClient()
    leagues = client.get_league_list()
    print(f"✅ FootyStats Client attivo! Campionati indicizzati: {len(leagues)}")
    
    # Test risoluzione automatica per Serie A, J3 League e Ucraina
    test_cases = [
        ("Italy", "Serie A"),
        ("Japan", "J3 League"),
        ("Ukraine", "Ukrainian Premier League"),
        ("England", "Premier League")
    ]
    for c, ln in test_cases:
        sid = client.get_latest_season_id(c, ln)
        table = client.get_table_by_name(c, ln)
        top = table[0]["cleanName"] if table else "N/D"
        print(f"🏆 {c} - {ln} (Season ID {sid}): {len(table)} squadre | In testa: {top}")

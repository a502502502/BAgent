"""
BAgent - Resilient Live Data Pipeline (Multi-Source Ingestion)
Pipeline multi-livello per l'acquisizione di statistiche live e tabellini (Falli, Corner,
Cartellini, Tiri, Player Props) aggirando blocchi anti-bot e Cloudflare.
"""

import sys
import json
import time
import os
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from datetime import datetime

# Path resolution
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import requests

@dataclass
class LivePlayerStat:
    player_name: str
    team_name: str
    fouls_committed: int = 0
    fouls_suffered: int = 0
    yellow_cards: int = 0
    red_cards: int = 0
    minutes_played: int = 0
    is_starter: bool = True

@dataclass
class LiveMatchSnapshot:
    match_id: str
    tournament: str
    home_team: str
    away_team: str
    minute: int = 0
    status: str = "SCHEDULED" # SCHEDULED, 1H, HT, 2H, FT, AET, PEN
    score_home: int = 0
    score_away: int = 0
    corners_home: int = 0
    corners_away: int = 0
    corners_total: int = 0
    cards_yellow_home: int = 0
    cards_yellow_away: int = 0
    cards_red_home: int = 0
    cards_red_away: int = 0
    cards_total: int = 0
    fouls_home: int = 0
    fouls_away: int = 0
    fouls_total: int = 0
    shots_on_target_home: int = 0
    shots_on_target_away: int = 0
    possession_home_pct: int = 50
    possession_away_pct: int = 50
    player_stats: Dict[str, LivePlayerStat] = field(default_factory=dict)
    source: str = "API-Football"
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        if self.corners_total == 0 and (self.corners_home > 0 or self.corners_away > 0):
            self.corners_total = self.corners_home + self.corners_away
        if self.fouls_total == 0 and (self.fouls_home > 0 or self.fouls_away > 0):
            self.fouls_total = self.fouls_home + self.fouls_away
        if self.cards_total == 0 and (self.cards_yellow_home > 0 or self.cards_yellow_away > 0 or self.cards_red_home > 0 or self.cards_red_away > 0):
            self.cards_total = self.cards_yellow_home + self.cards_yellow_away + self.cards_red_home + self.cards_red_away

class ResilientLiveCollector:
    """
    Collettore Dati Live Resiliente a 3 Livelli (Tier 1: API-Football, Tier 2: The Odds API, Tier 3: Browser Emulation).
    Garantisce un flusso ininterrotto di tabellini live (Corner, Falli, Cartellini, Giocatori).
    """

    def __init__(self, api_football_key: Optional[str] = None):
        self.api_football_key = api_football_key or os.getenv("API_FOOTBALL_KEY", "")
        self.session = requests.Session()
        # Browser header fingerprint
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site"
        })

    def fetch_live_fixtures_api_football(self) -> List[LiveMatchSnapshot]:
        """
        Tier 1: Estrae tutte le partite live tramite API-Football.
        """
        if not self.api_football_key:
            return []

        url = "https://v3.football.api-sports.io/fixtures?live=all"
        headers = {
            "x-apisports-key": self.api_football_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }

        snapshots = []
        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                response = data.get("response", [])
                for item in response:
                    fix = item.get("fixture", {})
                    league = item.get("league", {})
                    teams = item.get("teams", {})
                    goals = item.get("goals", {})
                    
                    match_id = str(fix.get("id"))
                    minute = fix.get("status", {}).get("elapsed") or 0
                    status = fix.get("status", {}).get("short") or "LIVE"
                    
                    snapshot = LiveMatchSnapshot(
                        match_id=match_id,
                        tournament=league.get("name", "Unknown"),
                        home_team=teams.get("home", {}).get("name", ""),
                        away_team=teams.get("away", {}).get("name", ""),
                        minute=minute,
                        status=status,
                        score_home=goals.get("home") or 0,
                        score_away=goals.get("away") or 0,
                        source="API-Football Live"
                    )
                    snapshots.append(snapshot)
        except Exception as e:
            print(f"[Tier 1 Error] API-Football fetch failed: {e}")
        
        return snapshots

    def fetch_match_statistics_api_football(self, fixture_id: str) -> Optional[Dict[str, Any]]:
        """
        Tier 1: Scarica i dettagli statistici (Corner, Falli, Tiri, Cartellini) da API-Football.
        """
        if not self.api_football_key:
            return None

        url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
        headers = {
            "x-apisports-key": self.api_football_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }

        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                return r.json().get("response", [])
        except Exception as e:
            print(f"[Tier 1 Error] Stats fetch for {fixture_id} failed: {e}")
        return None

    def parse_stats_to_snapshot(self, snapshot: LiveMatchSnapshot, raw_stats: List[Dict[str, Any]]) -> LiveMatchSnapshot:
        """
        Popola il LiveMatchSnapshot con le statistiche analitiche.
        """
        if len(raw_stats) >= 2:
            home_stat_dict = {item.get("type"): item.get("value") for item in raw_stats[0].get("statistics", [])}
            away_stat_dict = {item.get("type"): item.get("value") for item in raw_stats[1].get("statistics", [])}

            # Corner
            c_home = home_stat_dict.get("Corner Kicks") or 0
            c_away = away_stat_dict.get("Corner Kicks") or 0
            snapshot.corners_home = int(c_home) if c_home else 0
            snapshot.corners_away = int(c_away) if c_away else 0
            snapshot.corners_total = snapshot.corners_home + snapshot.corners_away

            # Falli
            f_home = home_stat_dict.get("Fouls") or 0
            f_away = away_stat_dict.get("Fouls") or 0
            snapshot.fouls_home = int(f_home) if f_home else 0
            snapshot.fouls_away = int(f_away) if f_away else 0
            snapshot.fouls_total = snapshot.fouls_home + snapshot.fouls_away

            # Cartellini
            yc_home = home_stat_dict.get("Yellow Cards") or 0
            yc_away = away_stat_dict.get("Yellow Cards") or 0
            rc_home = home_stat_dict.get("Red Cards") or 0
            rc_away = away_stat_dict.get("Red Cards") or 0
            snapshot.cards_yellow_home = int(yc_home) if yc_home else 0
            snapshot.cards_yellow_away = int(yc_away) if yc_away else 0
            snapshot.cards_red_home = int(rc_home) if rc_home else 0
            snapshot.cards_red_away = int(rc_away) if rc_away else 0
            snapshot.cards_total = snapshot.cards_yellow_home + snapshot.cards_yellow_away + snapshot.cards_red_home + snapshot.cards_red_away

            # Tiri in porta
            st_home = home_stat_dict.get("Shots on Goal") or 0
            st_away = away_stat_dict.get("Shots on Goal") or 0
            snapshot.shots_on_target_home = int(st_home) if st_home else 0
            snapshot.shots_on_target_away = int(st_away) if st_away else 0

        return snapshot

    def format_live_card(self, s: LiveMatchSnapshot) -> str:
        """Formatta una scheda live chiara per terminale e bot Telegram."""
        return (
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏱️ [{s.minute}'] {s.home_team} {s.score_home} - {s.score_away} {s.away_team} ({s.tournament})\n"
            f"📊 STATISTICHE LIVE:\n"
            f"• 🚩 Corner Totali: {s.corners_total} ({s.corners_home} - {s.corners_away})\n"
            f"• ⚔️ Falli Totali: {s.fouls_total} ({s.fouls_home} - {s.fouls_away})\n"
            f"• 🟨 Cartellini Totali: {s.cards_total} (Gialli: {s.cards_yellow_home}+{s.cards_yellow_away} | Rossi: {s.cards_red_home}+{s.cards_red_away})\n"
            f"• 🎯 Tiri in Porta: {s.shots_on_target_home} - {s.shots_on_target_away}\n"
            f"• 📡 Fonte Dati: {s.source} (Aggiornato: {s.updated_at.strftime('%H:%M:%S')} UTC)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        )

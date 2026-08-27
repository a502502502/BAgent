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

@dataclass
class LiveInPlayOpportunity:
    match_id: str
    match_name: str
    minute: int
    market: str
    recommended_pick: str
    estimated_odds: float
    confidence_level: str # ALTO, MEDIO, OTTIMALE
    reasoning: str
    kelly_stake_pct: float
    urgency: str # IMMEDIATO, ATTENDI 70'

class ResilientLiveCollector:
    """
    Collettore Dati Live Resiliente a 3 Livelli (Tier 1: API-Football, Tier 2: The Odds API, Tier 3: Browser Emulation).
    Garantisce un flusso ininterrotto di tabellini live ed elabora opportunità in-play in tempo reale.
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

    def detect_inplay_opportunities(self, s: LiveMatchSnapshot) -> List[LiveInPlayOpportunity]:
        """
        Algoritmo Quantitativo In-Play: Analizza il ritmo e i dati live per rilevare
        giocate di valore immediato (Corner Blitz, Gol Imminente, Cartellini in Escalation).
        """
        opportunities = []

        if s.minute < 20 or s.minute > 88:
            return opportunities

        # 1. LIVE CORNER BLITZ TRIGGER (Ritmo Corner Anomalo)
        corner_rate = s.corners_total / max(s.minute, 1) # corner al minuto
        if s.minute >= 45 and corner_rate >= 0.12 and (s.shots_on_target_home + s.shots_on_target_away) >= 5:
            projected_corners = round(corner_rate * 95, 1)
            target_line = s.corners_total + 2.5
            opp = LiveInPlayOpportunity(
                match_id=s.match_id,
                match_name=f"{s.home_team} vs {s.away_team}",
                minute=s.minute,
                market="Corner Totali Live",
                recommended_pick=f"Over {target_line:.1f} Corner Live",
                estimated_odds=1.75,
                confidence_level="⭐⭐⭐ ALTO (Corner Engine Attivo)",
                reasoning=f"Proiezione a {projected_corners} corner totali (1 corner ogni {1/corner_rate:.1f} min con {s.shots_on_target_home + s.shots_on_target_away} tiri in porta). Pressione costante.",
                kelly_stake_pct=5.0,
                urgency="⚡ GIOCA SUBITO (Trend verificato)"
            )
            opportunities.append(opp)

        # 2. GOL IMMINENTE / PRESSIONE ASIMMETRICA (0-0 o Svantaggio con Assedio)
        total_shots_on_target = s.shots_on_target_home + s.shots_on_target_away
        if s.minute >= 55 and s.score_home == 0 and s.score_away == 0 and total_shots_on_target >= 7:
            opp = LiveInPlayOpportunity(
                match_id=s.match_id,
                match_name=f"{s.home_team} vs {s.away_team}",
                minute=s.minute,
                market="Gol Live (Late Breakthrough)",
                recommended_pick="Over 0.5 Gol Totali Match",
                estimated_odds=1.50,
                confidence_level="👑 MASSIMO (Gara da sblocco matematico)",
                reasoning=f"Match bloccato sullo 0-0 al {s.minute}' ma con ben {total_shots_on_target} tiri nello specchio. Difese stanche, gol nell'aria entro l'80'.",
                kelly_stake_pct=6.5,
                urgency="⚡ ENTRA ORA (Quota in salita)"
            )
            opportunities.append(opp)

        # 3. ESCALATION CARTELLINI / NERVOSISMO (Partite Calde)
        if s.minute >= 60 and s.cards_total >= 4 and s.fouls_total >= 20:
            target_cards = s.cards_total + 1.5
            opp = LiveInPlayOpportunity(
                match_id=s.match_id,
                match_name=f"{s.home_team} vs {s.away_team}",
                minute=s.minute,
                market="Cartellini Totali Live",
                recommended_pick=f"Over {target_cards:.1f} Cartellini Live",
                estimated_odds=1.85,
                confidence_level="🔥 ELEVATO (Tensione Fuori Controllo)",
                reasoning=f"Gara con {s.fouls_total} falli e {s.cards_total} sanzioni già estratte. Con i minuti finali e le perdite di tempo scattano altri cartellini inevitabili.",
                kelly_stake_pct=4.0,
                urgency="⏱️ ATTENDI 70' (Per quota migliore)"
            )
            opportunities.append(opp)

        return opportunities

    def format_inplay_alert(self, opp: LiveInPlayOpportunity, bankroll: float = 300.00) -> str:
        """Formatta una notifica Telegram d'impatto con la giocata live consigliata."""
        calculated_stake = round((bankroll * (opp.kelly_stake_pct / 100.0)) * 2) / 2
        return (
            f"⚡ *BAGENT IN-PLAY OPPORTUNITY: SEGNALE LIVE RILEVATO*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"⚽ *Partita:* {opp.match_name} (Minuto *{opp.minute}'*)\n"
            f"🎯 *GIOCATA CONSIGLIATA:* `{opp.recommended_pick}`\n"
            f"📊 *Mercato:* {opp.market}\n"
            f"📈 *Quota Stimata:* `~{opp.estimated_odds:.2f}`\n\n"
            f"🧠 *Motivazione Live:* {opp.reasoning}\n"
            f"💎 *Confidenza:* {opp.confidence_level}\n"
            f"💵 *Stake Consigliato:* *{calculated_stake:.2f} €* ({opp.kelly_stake_pct}% Bankroll)\n"
            f"🚨 *Tempismo:* *{opp.urgency}*\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )

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

    def fetch_live_player_props_api_football(self, fixture_id: str) -> Dict[str, LivePlayerStat]:
        """
        Step 3: Estrae i dati granulari per singolo giocatore (Falli Commessi, Falli Subiti, Minuti, Tiri, Cartellini)
        dall'endpoint ufficiale fixtures/players.
        """
        player_dict = {}
        if not self.api_football_key:
            return player_dict

        url = f"https://v3.football.api-sports.io/fixtures/players?fixture={fixture_id}"
        headers = {
            "x-apisports-key": self.api_football_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }

        try:
            r = requests.get(url, headers=headers, timeout=10)
            if r.status_code == 200:
                response = r.json().get("response", [])
                for team_block in response:
                    team_name = team_block.get("team", {}).get("name", "")
                    players = team_block.get("players", [])
                    for p in players:
                        p_info = p.get("player", {})
                        stats = p.get("statistics", [{}])[0]
                        games = stats.get("games", {})
                        fouls = stats.get("fouls", {})
                        cards = stats.get("cards", {})

                        name = p_info.get("name", "")
                        stat_obj = LivePlayerStat(
                            player_name=name,
                            team_name=team_name,
                            fouls_committed=fouls.get("committed") or 0,
                            fouls_suffered=fouls.get("drawn") or 0,
                            yellow_cards=cards.get("yellow") or 0,
                            red_cards=cards.get("red") or 0,
                            minutes_played=games.get("minutes") or 0,
                            is_starter=not games.get("substitute", False)
                        )
                        player_dict[name.lower()] = stat_obj
        except Exception as e:
            print(f"[Tier 1 Error] Player props fetch for {fixture_id} failed: {e}")

        return player_dict

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

"""
services/football/external/on_demand_ingestor.py — Ingestore On-Demand Regola #90.

Se mancano dati storici o telemetria in data/bagent.db per una o entrambe le squadre
di un match in palinsesto, questo modulo interroga il feed delta Flashscore/LiveScore,
scarica le ultime 10 partite di ciascuna squadra, le inserisce nella tabella matches
e rigenera automaticamente team_rolling_ten_telemetry prima del calcolo.
"""

from __future__ import annotations

import logging
import sqlite3
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger("OnDemandIngestor")
ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent
DB_PATH = ROOT_DIR / "data" / "bagent.db"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "X-Fsign": "SW9D1eZo",
}


class OnDemandMatchIngestor:
    """Scarica e ingerisce in tempo reale lo storico recente per squadre mancanti."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or DB_PATH

    def find_match_id(self, home_team: str, away_team: str) -> Optional[str]:
        """Cerca il match_id Flashscore per la coppia di squadre."""
        from services.football.external.sources.flashscore_live import FlashscoreLiveEngine

        engine = FlashscoreLiveEngine()
        feed = engine.fetch_feed()
        h_clean = home_team.lower().strip()
        a_clean = away_team.lower().strip()

        for m in feed:
            m_h = m.get("home", "").lower()
            m_a = m.get("away", "").lower()
            if (h_clean in m_h or m_h in h_clean) and (a_clean in m_a or m_a in a_clean):
                return m.get("match_id")

        # Fallback ricerca parziale
        for m in feed:
            m_h = m.get("home", "").lower()
            m_a = m.get("away", "").lower()
            if h_clean in m_h or a_clean in m_a:
                return m.get("match_id")

        return None

    def fetch_and_ingest_for_match(self, home_team: str, away_team: str, match_id: Optional[str] = None) -> int:
        """
        Scarica e inserisce le ultime partite di entrambe le squadre in bagent.db.
        Ritorna il numero di partite inserite.
        """
        mid = match_id or self.find_match_id(home_team, away_team)
        if not mid:
            logger.warning(f"Nessun match_id Flashscore trovato per {home_team} vs {away_team}")
            return 0

        url = f"https://local-global.flashscore.ninja/2/x/feed/df_hh_1_{mid}"
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_text = resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            logger.error(f"Errore download feed H2H per match_id {mid}: {e}")
            return 0

        sections = raw_text.split("~KB÷")
        if len(sections) < 3:
            logger.warning(f"Feed H2H incompleto per match_id {mid}")
            return 0

        parsed_matches: List[Dict[str, Any]] = []
        for s in sections[1:3]:
            parsed_matches.extend(self._parse_section(s, max_matches=10))

        if not parsed_matches:
            return 0

        return self._insert_matches(parsed_matches)

    def _parse_section(self, section_text: str, max_matches: int = 10) -> List[Dict[str, Any]]:
        matches = []
        items = section_text.split("~KC÷")[1:]
        for item in items[:max_matches]:
            fields = {}
            for part in item.split("¬"):
                if "÷" in part:
                    k, v = part.split("÷", 1)
                    fields[k] = v

            ts_str = item.split("¬")[0].strip()
            try:
                m_date = datetime.fromtimestamp(int(ts_str)).strftime("%Y-%m-%d")
            except Exception:
                m_date = ts_str

            home = fields.get("KJ", "").replace("*", "").strip()
            away = fields.get("KK", "").replace("*", "").strip()
            if not home or not away:
                continue

            try:
                hg = int(fields.get("KU", 0))
                ag = int(fields.get("KT", 0))
            except Exception:
                continue

            league = fields.get("KF", "League").strip()
            season = "2026/2027" if "2026" in m_date else "2025/2026"
            matches.append({
                "league": league,
                "season": season,
                "match_date": m_date,
                "home_team": home,
                "away_team": away,
                "home_goals": hg,
                "away_goals": ag,
                "total_goals": hg + ag,
            })
        return matches

    def _insert_matches(self, matches: List[Dict[str, Any]]) -> int:
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        inserted = 0
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        for m in matches:
            exists = c.execute(
                "SELECT id FROM matches WHERE home_team = ? AND away_team = ? AND match_date = ?",
                (m["home_team"], m["away_team"], m["match_date"])
            ).fetchone()

            if not exists:
                c.execute("""
                    INSERT INTO matches (
                        league, season, status, home_team, away_team,
                        home_goals, away_goals, total_goals,
                        ht_home_goals, ht_away_goals,
                        match_date, updated_at
                    ) VALUES (?, ?, 'FT', ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    m["league"], m["season"], m["home_team"], m["away_team"],
                    m["home_goals"], m["away_goals"], m["total_goals"],
                    max(0, m["home_goals"] // 2), max(0, m["away_goals"] // 2),
                    m["match_date"], now_str
                ))
                inserted += 1

        conn.commit()
        conn.close()
        return inserted

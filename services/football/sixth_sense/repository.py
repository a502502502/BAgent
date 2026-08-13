"""
SixthSenseRepository — persistenza DB per articoli ed eventi del Sesto Senso.

Salva automaticamente nel DB SQLite:
  - sixth_sense_news:   articoli grezzi raccolti per ogni partita
  - sixth_sense_events: eventi strutturati estratti dall'LLM

Utilizzo:
    from services.football.sixth_sense.repository import SixthSenseRepository
    repo = SixthSenseRepository()
    repo.save_news(bundle, home="Juventus", away="Inter", match_date="2026-08-14")
    repo.save_events(analysis, home="Juventus", away="Inter", match_date="2026-08-14")

Query utili:
    repo.get_recent_injuries("Juventus", days=30)
    repo.get_match_events("Juventus", "Inter", "2026-08-14")
    repo.team_injury_history("Inter", limit=20)
"""

from __future__ import annotations

from datetime import datetime, timezone, date, timedelta
from pathlib import Path
from typing import Optional

from services.database.schema import get_db


class SixthSenseRepository:
    """
    Accesso al DB per le tabelle sixth_sense_news e sixth_sense_events.
    """

    def __init__(self, db_path: Optional[Path] = None):
        self._db_path = db_path

    def _conn(self):
        if self._db_path:
            from services.database.schema import get_db as _get
            import sqlite3
            conn = sqlite3.connect(str(self._db_path))
            conn.row_factory = sqlite3.Row
            from services.database.schema import _create_tables
            _create_tables(conn)
            return conn
        return get_db()

    # ──────────────────────────────────────────────────────────────────
    # SALVATAGGIO
    # ──────────────────────────────────────────────────────────────────

    def save_news(
        self,
        news_bundle: dict,
        home: str,
        away: str,
        match_date: Optional[str] = None,
    ) -> int:
        """
        Salva gli articoli raccolti dal SixthSenseNewsCollector.
        `news_bundle` è il dict restituito da SixthSenseNewsCollector.collect().
        Ritorna il numero di articoli salvati.
        """
        collected_at = news_bundle.get("collected_at") or datetime.now(timezone.utc).isoformat()
        articles = news_bundle.get("articles", {})

        rows = []
        tag_map = {
            "match":     articles.get("match", []),
            "home":      articles.get("home_team", []),
            "away":      articles.get("away_team", []),
        }

        for tag, art_list in tag_map.items():
            for a in art_list:
                rows.append((
                    home, away, match_date, collected_at, tag,
                    a.get("title", ""),
                    a.get("url"),
                    a.get("source"),
                    a.get("snippet"),
                    a.get("language"),
                ))

        if not rows:
            return 0

        conn = self._conn()
        try:
            conn.executemany("""
                INSERT INTO sixth_sense_news
                    (home_team, away_team, match_date, collected_at, team_tag,
                     title, url, source, snippet, language)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, rows)
            conn.commit()
        finally:
            conn.close()

        return len(rows)

    def save_events(
        self,
        analysis,          # SixthSenseAnalysis
        home: str,
        away: str,
        match_date: Optional[str] = None,
    ) -> int:
        """
        Salva gli eventi strutturati estratti dall'LLM.
        `analysis` è un oggetto SixthSenseAnalysis (con .events, .summary, .overall_confidence).
        Ritorna il numero di righe salvate.
        """
        if not analysis or analysis.status in ("NO_NEWS", "NO_EVENTS", "ERROR"):
            return 0

        created_at = datetime.now(timezone.utc).isoformat()
        rows = []

        for ev in analysis.events:
            rows.append((
                home, away, match_date, created_at,
                getattr(ev, "team", None),
                getattr(ev, "player", None),
                getattr(ev, "event_type", None),
                getattr(ev, "impact", None),
                getattr(ev, "confidence", None),
                getattr(ev, "description", None),
                analysis.summary,
                analysis.overall_confidence,
            ))

        # Se non ci sono eventi ma c'è una summary, salva comunque una riga riepilogativa
        if not rows and analysis.summary:
            rows.append((
                home, away, match_date, created_at,
                None, None, "summary", None, analysis.overall_confidence,
                None, analysis.summary, analysis.overall_confidence,
            ))

        if not rows:
            return 0

        conn = self._conn()
        try:
            conn.executemany("""
                INSERT INTO sixth_sense_events
                    (home_team, away_team, match_date, created_at,
                     team, player, event_type, impact, confidence,
                     notes, summary, overall_confidence)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
            """, rows)
            conn.commit()
        finally:
            conn.close()

        return len(rows)

    # ──────────────────────────────────────────────────────────────────
    # QUERY
    # ──────────────────────────────────────────────────────────────────

    def get_match_events(
        self,
        home: str,
        away: str,
        match_date: Optional[str] = None,
    ) -> list[dict]:
        """Tutti gli eventi per una specifica partita."""
        conn = self._conn()
        try:
            if match_date:
                rows = conn.execute("""
                    SELECT * FROM sixth_sense_events
                    WHERE home_team = ? AND away_team = ? AND match_date = ?
                    ORDER BY created_at DESC
                """, (home, away, match_date)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM sixth_sense_events
                    WHERE home_team = ? AND away_team = ?
                    ORDER BY created_at DESC LIMIT 50
                """, (home, away)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_recent_injuries(
        self,
        team: str,
        days: int = 30,
        event_types: tuple = ("injury", "suspension"),
    ) -> list[dict]:
        """
        Infortuni/squalifiche recenti di una squadra (come casa o ospite).
        Utile per il Sesto Senso automatico.
        """
        since = (date.today() - timedelta(days=days)).isoformat()
        placeholders = ",".join("?" * len(event_types))

        conn = self._conn()
        try:
            rows = conn.execute(f"""
                SELECT * FROM sixth_sense_events
                WHERE (home_team = ? OR away_team = ?)
                  AND team = ?
                  AND event_type IN ({placeholders})
                  AND match_date >= ?
                ORDER BY match_date DESC
            """, (team, team, team, *event_types, since)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def team_injury_history(self, team: str, limit: int = 20) -> list[dict]:
        """Storico completo degli eventi per una squadra."""
        conn = self._conn()
        try:
            rows = conn.execute("""
                SELECT * FROM sixth_sense_events
                WHERE team = ?
                ORDER BY match_date DESC, created_at DESC
                LIMIT ?
            """, (team, limit)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_news(
        self,
        home: str,
        away: str,
        match_date: Optional[str] = None,
        team_tag: Optional[str] = None,
    ) -> list[dict]:
        """Articoli raccolti per una partita."""
        conn = self._conn()
        try:
            filters = ["home_team = ?", "away_team = ?"]
            params: list = [home, away]
            if match_date:
                filters.append("match_date = ?")
                params.append(match_date)
            if team_tag:
                filters.append("team_tag = ?")
                params.append(team_tag)
            where = " AND ".join(filters)
            rows = conn.execute(f"""
                SELECT * FROM sixth_sense_news
                WHERE {where}
                ORDER BY collected_at DESC
            """, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def most_injured_teams(self, days: int = 30, limit: int = 10) -> list[dict]:
        """
        Classifica squadre con più eventi injury/suspension negli ultimi N giorni.
        Utile per dashboard o filtri automatici.
        """
        since = (date.today() - timedelta(days=days)).isoformat()
        conn = self._conn()
        try:
            rows = conn.execute("""
                SELECT team,
                       COUNT(*) as total_events,
                       SUM(CASE WHEN event_type='injury' THEN 1 ELSE 0 END) as injuries,
                       SUM(CASE WHEN event_type='suspension' THEN 1 ELSE 0 END) as suspensions,
                       AVG(impact) as avg_impact
                FROM sixth_sense_events
                WHERE event_type IN ('injury', 'suspension')
                  AND match_date >= ?
                  AND team IS NOT NULL
                GROUP BY team
                ORDER BY total_events DESC
                LIMIT ?
            """, (since, limit)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def stats(self) -> dict:
        """Statistiche rapide sulle tabelle Sesto Senso."""
        conn = self._conn()
        try:
            n_news = conn.execute("SELECT COUNT(*) FROM sixth_sense_news").fetchone()[0]
            n_events = conn.execute("SELECT COUNT(*) FROM sixth_sense_events").fetchone()[0]
            n_matches = conn.execute(
                "SELECT COUNT(DISTINCT home_team||away_team||match_date) FROM sixth_sense_events"
            ).fetchone()[0]
            return {
                "total_articles": n_news,
                "total_events": n_events,
                "matches_analyzed": n_matches,
            }
        finally:
            conn.close()

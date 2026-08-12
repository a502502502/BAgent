"""
StatsCollector — interroga il database BAgent per una squadra o partita.

Utilizzo:
    from services.database.stats_collector import StatsCollector
    sc = StatsCollector()
    stats = sc.team_stats("Austria Wien", season="2026/2027")
    players = sc.top_players("Austria Wien", season="2026/2027")
    matches = sc.recent_matches("Austria Wien", n=5)
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
from services.database.schema import get_db, DB_PATH


class StatsCollector:

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path

    def _conn(self):
        return get_db(self.db_path)

    def _find_team(self, conn, name: str, season: Optional[str] = None) -> Optional[str]:
        """Trova il nome esatto nel DB (ricerca parziale case-insensitive)."""
        q = "SELECT team_name FROM teams WHERE LOWER(team_name) LIKE ?"
        params = [f"%{name.lower()}%"]
        if season:
            q += " AND season=?"
            params.append(season)
        q += " ORDER BY matches_played DESC LIMIT 1"
        row = conn.execute(q, params).fetchone()
        return row['team_name'] if row else None

    # ------------------------------------------------------------------
    # Stats squadra
    # ------------------------------------------------------------------

    def team_stats(self, team: str, season: Optional[str] = None) -> dict:
        """Restituisce le stats aggregate di una squadra."""
        conn = self._conn()
        db_name = self._find_team(conn, team, season)
        if not db_name:
            conn.close()
            return {"found": False, "team": team}

        q = "SELECT * FROM teams WHERE team_name=?"
        params = [db_name]
        if season:
            q += " AND season=?"
            params.append(season)
        q += " ORDER BY matches_played DESC LIMIT 1"
        row = conn.execute(q, params).fetchone()
        conn.close()

        if not row:
            return {"found": False, "team": team}

        return {
            "found":                True,
            "team_name":            row["team_name"],
            "common_name":          row["common_name"],
            "league":               row["league"],
            "season":               row["season"],
            "matches_played":       row["matches_played"],
            "wins":                 row["wins"],
            "draws":                row["draws"],
            "losses":               row["losses"],
            "win_pct":              row["win_pct"],
            "goals_scored":         row["goals_scored"],
            "goals_conceded":       row["goals_conceded"],
            "goals_scored_home":    row["goals_scored_home"],
            "goals_conceded_home":  row["goals_conceded_home"],
            "goals_scored_away":    row["goals_scored_away"],
            "goals_conceded_away":  row["goals_conceded_away"],
            "goals_scored_per_match":   row["goals_scored_per_match"],
            "goals_conceded_per_match": row["goals_conceded_per_match"],
            "clean_sheets":         row["clean_sheets"],
            "clean_sheet_pct":      row["clean_sheet_pct"],
            "btts_pct":             row["btts_pct"],
            "over25_pct":           row["over25_pct"],
            "corners_per_match":    row["corners_per_match"],
            "xg_for_avg":           row["xg_for_avg"],
            "xg_against_avg":       row["xg_against_avg"],
            "cards_per_match":      row["cards_per_match"],
            "leading_at_ht_pct":    row["leading_at_ht_pct"],
        }

    # ------------------------------------------------------------------
    # Ultime partite
    # ------------------------------------------------------------------

    def recent_matches(self, team: str, n: int = 5,
                       season: Optional[str] = None) -> list[dict]:
        """Ultime N partite di una squadra."""
        conn = self._conn()
        q = """
            SELECT * FROM matches
            WHERE (LOWER(home_team) LIKE ? OR LOWER(away_team) LIKE ?)
              AND status='complete'
        """
        like = f"%{team.lower()}%"
        params = [like, like]
        if season:
            q += " AND season=?"
            params.append(season)
        q += " ORDER BY timestamp DESC LIMIT ?"
        params.append(n)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Top giocatori
    # ------------------------------------------------------------------

    def top_players(self, team: str, season: Optional[str] = None,
                    top: int = 5) -> list[dict]:
        """Top scorer + assist della squadra."""
        conn = self._conn()
        q = """
            SELECT * FROM players
            WHERE LOWER(current_club) LIKE ?
        """
        params = [f"%{team.lower()}%"]
        if season:
            q += " AND season=?"
            params.append(season)
        q += " ORDER BY goals DESC, assists DESC LIMIT ?"
        params.append(top)
        rows = conn.execute(q, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Confronto due squadre (per analisi pre-partita)
    # ------------------------------------------------------------------

    def match_preview(self, home: str, away: str,
                      season: Optional[str] = None) -> dict:
        """
        Restituisce stats di entrambe le squadre pronte per l'analisi.
        """
        home_stats  = self.team_stats(home, season)
        away_stats  = self.team_stats(away, season)
        home_recent = self.recent_matches(home, n=5, season=season)
        away_recent = self.recent_matches(away, n=5, season=season)
        home_top    = self.top_players(home, season, top=3)
        away_top    = self.top_players(away, season, top=3)

        return {
            "home": {
                "stats":   home_stats,
                "recent":  home_recent,
                "players": home_top,
            },
            "away": {
                "stats":   away_stats,
                "recent":  away_recent,
                "players": away_top,
            },
        }

    def format_for_analysis(self, home: str, away: str,
                            season: Optional[str] = None) -> str:
        """
        Testo formattato pronto per analisi o prompt LLM.
        """
        data = self.match_preview(home, away, season)
        lines = [f"=== STATISTICHE DB: {home} vs {away} ===\n"]

        for side, label in [("home", home), ("away", away)]:
            s = data[side]["stats"]
            if not s.get("found"):
                lines.append(f"[{label}] Non trovata nel database.\n")
                continue

            lines.append(f"[{label}] — {s['league']} {s['season']}")
            lines.append(
                f"  Forma: {s['wins']}V {s['draws']}P {s['losses']}S "
                f"({s['win_pct']:.0f}% vittorie) su {s['matches_played']} partite"
            )
            lines.append(
                f"  Gol: {s['goals_scored_per_match']:.2f} segnati / "
                f"{s['goals_conceded_per_match']:.2f} subiti per partita"
            )
            lines.append(
                f"  xG: {s['xg_for_avg']:.2f} pro / {s['xg_against_avg']:.2f} contro"
            )
            lines.append(
                f"  BTTS: {s['btts_pct']:.0f}%  |  "
                f"Over 2.5: {s['over25_pct']:.0f}%  |  "
                f"Clean sheet: {s['clean_sheet_pct']:.0f}%"
            )
            lines.append(
                f"  Corner/partita: {s['corners_per_match']:.1f}  |  "
                f"Cartellini/partita: {s['cards_per_match']:.1f}"
            )

            # Ultimi risultati
            recent = data[side]["recent"]
            if recent:
                results = []
                for m in recent:
                    h, a = m['home_team'], m['away_team']
                    hg, ag = m['home_goals'], m['away_goals']
                    if label.lower() in h.lower():
                        results.append(f"{hg}-{ag}({'V' if hg>ag else 'P' if hg<ag else 'D'})")
                    else:
                        results.append(f"{hg}-{ag}({'V' if ag>hg else 'P' if ag<hg else 'D'})")
                lines.append(f"  Ultimi 5: {' | '.join(results)}")

            # Top scorer
            players = data[side]["players"]
            if players:
                top = [f"{p['full_name']} ({p['goals']}G/{p['assists']}A)" for p in players]
                lines.append(f"  Top scorer: {', '.join(top)}")

            lines.append("")

        return "\n".join(lines)

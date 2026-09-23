"""Repository calcio sulle tabelle matches, teams e leagues."""

from domain.interfaces.repository import Repository

SEASON = "2026"


class SqliteMatchRepository(Repository):

    def __init__(self, conn):
        self.conn = conn

    def save_competition(self, competition):
        self.conn.execute(
            """
            INSERT INTO leagues (name, season, country)
            VALUES (?, ?, ?)
            ON CONFLICT(name, season) DO NOTHING
            """,
            (competition.name, SEASON, getattr(competition, "country", None)),
        )
        self.conn.commit()

    def save_competitor(self, competitor):
        self.conn.execute(
            """
            INSERT INTO teams (team_name, league, season, country)
            VALUES (?, 'football', ?, ?)
            ON CONFLICT(team_name, league, season) DO NOTHING
            """,
            (competitor.name, SEASON, competitor.country),
        )
        self.conn.commit()

    def save_match(self, match):
        self.conn.execute(
            """
            INSERT INTO matches (
                league, season, date_gmt, status, home_team, away_team
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(league, season, home_team, away_team, date_gmt) DO UPDATE SET
                status = excluded.status
            """,
            (
                match.competition.name,
                SEASON,
                match.start_time,
                match.status,
                match.home.name,
                match.away.name,
            ),
        )
        self.conn.commit()

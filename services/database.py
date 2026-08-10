import sqlite3
from pathlib import Path


class Database:

    def __init__(self):

        from config.settings import DATABASE



self.connection = sqlite3.connect(DATABASE)

        self.connection = sqlite3.connect(db_path)

        self.cursor = self.connection.cursor()

        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches(

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                tournament TEXT,

                player1 TEXT,

                player2 TEXT,

                start_time TEXT,

                odd1 REAL,

                odd2 REAL,

                prediction TEXT,

                confidence REAL

            )
        """)

        self.connection.commit()

    def close(self):

        self.connection.close()
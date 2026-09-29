"""Il nome di una squadra non prende i gol di un omonimo in un altro campionato."""

import sqlite3

from services.betting.netwin_cache_reader import (
    CachedMatch,
    estimate_xg,
    historical_xg,
    team_names_match,
)


def test_short_names_do_not_swallow_a_longer_club():
    assert team_names_match("Flamengo RJ", "Flamengo")
    assert not team_names_match("Atlético PR", "Atlético Madrid")
    assert not team_names_match("Atlético PR", "Atlético Mineiro")
    assert not team_names_match("América", "América de Cali")
    assert not team_names_match("Cerro", "Cerro Porteño")
    assert not team_names_match("Austria", "Austria Wien")
    assert not team_names_match("Albion", "Brighton & Hove Albion")


def test_paranaense_goals_stay_out_of_madrid(tmp_path):
    db = tmp_path / "names.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """
        CREATE TABLE matches (
            league TEXT, home_team TEXT, away_team TEXT,
            home_goals REAL, away_goals REAL, status TEXT
        )
        """
    )
    for _ in range(6):
        conn.execute(
            "INSERT INTO matches VALUES ('La Liga', 'Atlético Madrid', 'Getafe', 5, 0, 'FT')"
        )
        conn.execute(
            "INSERT INTO matches VALUES ('Brazil Serie A', 'Atlético PR', 'Flamengo', 0, 1, 'FT')"
        )
        conn.execute(
            "INSERT INTO matches VALUES ('Liga MX', 'América', 'Cruz Azul', 1, 0, 'FT')"
        )
        conn.execute(
            "INSERT INTO matches VALUES ('Colombia Primera A', 'América de Cali', 'Once Caldas', 4, 0, 'FT')"
        )
    conn.commit()
    conn.close()

    home, _away = historical_xg("Atlético PR", "Flamengo", "Brazil Serie A", db)
    assert home < 1.2

    mexico, _rival = historical_xg("América", "Cruz Azul", "Liga MX", db)
    assert mexico < 2.0

    missing = historical_xg("Squadra Inesistente", "Altra", "Brazil Serie A", db)
    assert missing is None
    assert estimate_xg(
        CachedMatch("X vs Y", "Squadra Inesistente", "Altra", "Brazil Serie A", "", {}),
        db,
    ) is None

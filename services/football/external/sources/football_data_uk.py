"""
football-data.co.uk — fonte storica gratuita per ~40 campionati europei.
CSV scaricabili senza autenticazione.

Documentazione colonne: https://www.football-data.co.uk/notes.txt
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Optional

import pandas as pd
import requests


BASE_URL = "https://www.football-data.co.uk"

# Mappa campionato -> path sul sito
LEAGUE_PATHS: dict[str, str] = {
    # Inghilterra
    "premier_league":   "mmz4281/{season}/E0.csv",
    "championship":     "mmz4281/{season}/E1.csv",
    "league_one":       "mmz4281/{season}/E2.csv",
    "league_two":       "mmz4281/{season}/E3.csv",
    # Italia
    "serie_a":          "mmz4281/{season}/I1.csv",
    "serie_b":          "mmz4281/{season}/I2.csv",
    # Spagna
    "la_liga":          "mmz4281/{season}/SP1.csv",
    "segunda":          "mmz4281/{season}/SP2.csv",
    # Germania
    "bundesliga":       "mmz4281/{season}/D1.csv",
    "bundesliga_2":     "mmz4281/{season}/D2.csv",
    # Francia
    "ligue_1":          "mmz4281/{season}/F1.csv",
    "ligue_2":          "mmz4281/{season}/F2.csv",
    # Portogallo
    "primeira_liga":    "mmz4281/{season}/P1.csv",
    # Olanda
    "eredivisie":       "mmz4281/{season}/N1.csv",
    # Belgio
    "first_division_a": "mmz4281/{season}/B1.csv",
    # Grecia
    "super_league":     "mmz4281/{season}/G1.csv",
    # Turchia
    "super_lig":        "mmz4281/{season}/T1.csv",
    # Scozia
    "premiership":      "mmz4281/{season}/SC0.csv",
}

# Colonne chiave (non tutti i file le hanno)
CORE_COLUMNS = [
    "Date", "HomeTeam", "AwayTeam",
    "FTHG", "FTAG", "FTR",      # gol e risultato
    "HTHG", "HTAG", "HTR",      # primo tempo
    "HS", "AS",                  # tiri
    "HST", "AST",                # tiri in porta
    "HC", "AC",                  # corner
    "HY", "AY",                  # gialli
    "HR", "AR",                  # rossi
    "B365H", "B365D", "B365A",  # quote Bet365
]


class FootballDataUKSource:
    """
    Scarica e gestisce i CSV storici di football-data.co.uk.

    Metodi principali:
        load(league, season)          -> pd.DataFrame
        load_local(path)              -> pd.DataFrame
        team_form(df, team, date, n)  -> pd.DataFrame
        season_slug(year_start)       -> str  (es. 2425 per 2024-25)
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        self._cache_dir = cache_dir
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "BAgent/1.0"})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def season_slug(year_start: int) -> str:
        """2024 -> '2425', 2023 -> '2324'"""
        y1 = str(year_start)[2:]
        y2 = str(year_start + 1)[2:]
        return f"{y1}{y2}"

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(
        self,
        league: str,
        season: int,
    ) -> pd.DataFrame:
        """
        Scarica il CSV per un campionato e stagione.
        league: chiave in LEAGUE_PATHS (es. 'serie_b', 'premier_league')
        season: anno di inizio stagione (es. 2024 per 2024-25)
        """
        if league not in LEAGUE_PATHS:
            raise ValueError(
                f"Campionato '{league}' non supportato. "
                f"Disponibili: {list(LEAGUE_PATHS.keys())}"
            )

        slug = self.season_slug(season)
        path = LEAGUE_PATHS[league].format(season=slug)
        url = f"{BASE_URL}/{path}"

        # Controlla cache locale
        if self._cache_dir:
            cache_file = self._cache_dir / f"{league}_{slug}.csv"
            if cache_file.exists():
                return self._parse(cache_file.read_text(encoding="utf-8"))

        r = self._session.get(url, timeout=20)
        r.raise_for_status()

        if self._cache_dir:
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(r.text, encoding="utf-8")

        return self._parse(r.text)

    def load_local(self, path: Path | str) -> pd.DataFrame:
        """Carica un CSV locale già scaricato."""
        with open(path, encoding="utf-8", errors="replace") as f:
            return self._parse(f.read())

    def _parse(self, csv_text: str) -> pd.DataFrame:
        df = pd.read_csv(io.StringIO(csv_text))

        # Normalizza la colonna Date
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(
                df["Date"], dayfirst=True, errors="coerce"
            )

        # Tieni solo le colonne disponibili tra quelle core
        available = [c for c in CORE_COLUMNS if c in df.columns]
        extra = [c for c in df.columns if c not in CORE_COLUMNS]
        df = df[available + extra]

        return df.dropna(subset=["HomeTeam", "AwayTeam"])

    # ------------------------------------------------------------------
    # Statistiche di forma
    # ------------------------------------------------------------------

    def team_form(
        self,
        df: pd.DataFrame,
        team: str,
        before_date: pd.Timestamp,
        n: int = 10,
    ) -> pd.DataFrame:
        """
        Ultimi N risultati di una squadra prima di una data.
        Considera sia partite in casa che in trasferta.
        """
        mask = (
            (
                (df["HomeTeam"] == team) |
                (df["AwayTeam"] == team)
            ) &
            (df["Date"] < before_date)
        )

        return (
            df[mask]
            .sort_values("Date", ascending=False)
            .head(n)
        )

    def head_to_head(
        self,
        df: pd.DataFrame,
        home: str,
        away: str,
        before_date: pd.Timestamp,
        n: int = 5,
    ) -> pd.DataFrame:
        """Ultimi N scontri diretti tra le due squadre."""
        mask = (
            (
                (df["HomeTeam"] == home) & (df["AwayTeam"] == away)
            ) | (
                (df["HomeTeam"] == away) & (df["AwayTeam"] == home)
            )
        ) & (df["Date"] < before_date)

        return (
            df[mask]
            .sort_values("Date", ascending=False)
            .head(n)
        )

    def form_stats(
        self,
        df: pd.DataFrame,
        team: str,
        before_date: pd.Timestamp,
        n: int = 10,
    ) -> dict:
        """
        Statistiche di forma aggregate: PPG, gol fatti/subiti, win%.
        """
        form = self.team_form(df, team, before_date, n)

        if form.empty:
            return {}

        wins = draws = losses = gf = ga = 0

        for _, row in form.iterrows():
            is_home = row["HomeTeam"] == team
            ftr = row.get("FTR")
            hg = row.get("FTHG", 0) or 0
            ag = row.get("FTAG", 0) or 0

            if is_home:
                gf += hg
                ga += ag
                if ftr == "H":
                    wins += 1
                elif ftr == "D":
                    draws += 1
                else:
                    losses += 1
            else:
                gf += ag
                ga += hg
                if ftr == "A":
                    wins += 1
                elif ftr == "D":
                    draws += 1
                else:
                    losses += 1

        total = wins + draws + losses
        ppg = (wins * 3 + draws) / total if total > 0 else 0.0

        return {
            "matches": total,
            "wins": wins,
            "draws": draws,
            "losses": losses,
            "ppg": round(ppg, 3),
            "win_pct": round(wins / total, 3) if total > 0 else 0.0,
            "goals_for": gf,
            "goals_against": ga,
            "goal_diff": gf - ga,
        }

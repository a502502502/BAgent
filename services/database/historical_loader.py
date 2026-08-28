#!/usr/bin/env python3
"""
services/database/historical_loader.py — Modulo di ingestione dati storici gratuiti.
Scarica e formatta stagioni passate (statistiche + quote reali) per i principali campionati europei.
"""

import os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent.parent

class HistoricalDataLoader:
    """Estrae e formatta dati storici di calcio con quote di chiusura e statistiche di match."""

    LEAGUE_CODES = {
        "Serie A": "I1",
        "Serie B": "I2",
        "Premier League": "E0",
        "Championship": "E1",
        "La Liga": "SP1",
        "Segunda Division": "SP2",
        "Bundesliga": "D1",
        "2. Bundesliga": "D2",
        "Ligue 1": "F1",
        "Ligue 2": "F2",
        "Eredivisie": "N1",
        "Liga Portugal": "P1"
    }

    SEASON_CODES = {
        2018: "1819",
        2019: "1920",
        2020: "2021",
        2021: "2122",
        2022: "2223",
        2023: "2324",
        2024: "2425",
        2025: "2526"
    }

    def __init__(self):
        self.data_dir = ROOT / "data" / "historical"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def download_season(self, league: str, year: int, force_refresh: bool = False) -> pd.DataFrame:
        """Scarica e memorizza in cache locale un file CSV di una stagione."""
        code = self.LEAGUE_CODES.get(league)
        season = self.SEASON_CODES.get(year)
        if not code or not season:
            raise ValueError(f"Lega '{league}' o anno '{year}' non supportati.")

        local_file = self.data_dir / f"{code}_{season}.csv"
        if local_file.exists() and not force_refresh:
            return pd.read_csv(local_file)

        url = f"https://www.football-data.co.uk/mmz4281/{season}/{code}.csv"
        try:
            df = pd.read_csv(url)
            # Salva in cache
            df.to_csv(local_file, index=False)
            return df
        except Exception as e:
            print(f"⚠️ Errore download {league} {year} ({url}): {e}")
            return pd.DataFrame()

    def load_dataset(self, leagues: list[str] = None, years: list[int] = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """
        Carica i dati per multiple leghe e stagioni, restituendo le matrici:
        X: Feature di match (Lega, Data, Squadre, Tiri, Falli, Corner)
        Y: Target binari (home_win, draw, away_win, over25, btts)
        O: Quote di chiusura (1, X, 2, Over 2.5, Under 2.5)
        """
        if leagues is None:
            leagues = ["Serie A", "Premier League", "La Liga", "Bundesliga", "Ligue 1"]
        if years is None:
            years = [2021, 2022, 2023, 2024]

        dfs = []
        for l in leagues:
            for y in years:
                df_season = self.download_season(l, y)
                if not df_season.empty and "Date" in df_season.columns and "HomeTeam" in df_season.columns:
                    df_season["LeagueName"] = l
                    df_season["SeasonYear"] = y
                    dfs.append(df_season)

        if not dfs:
            raise RuntimeError("Nessun dato storico scaricato con successo.")

        raw_df = pd.concat(dfs, ignore_index=True)
        
        # Pulisci e normalizza date
        raw_df["DateClean"] = pd.to_datetime(raw_df["Date"], format="%d/%m/%Y", errors="coerce")
        mask_alt = raw_df["DateClean"].isna()
        if mask_alt.any():
            raw_df.loc[mask_alt, "DateClean"] = pd.to_datetime(raw_df.loc[mask_alt, "Date"], format="%d/%m/%y", errors="coerce")

        raw_df = raw_df.sort_values("DateClean").reset_index(drop=True)

        # 1. Costruisci Y (Target Binari)
        Y = pd.DataFrame(index=raw_df.index)
        Y["home_win"] = (raw_df["FTR"] == "H").astype(int)
        Y["draw"] = (raw_df["FTR"] == "D").astype(int)
        Y["away_win"] = (raw_df["FTR"] == "A").astype(int)
        
        total_goals = raw_df["FTHG"] + raw_df["FTAG"]
        Y["over_2.5"] = (total_goals > 2.5).astype(int)
        Y["under_2.5"] = (total_goals < 2.5).astype(int)
        Y["btts"] = ((raw_df["FTHG"] > 0) & (raw_df["FTAG"] > 0)).astype(int)

        # 2. Costruisci O (Quote di Mercato)
        O = pd.DataFrame(index=raw_df.index)
        # Preferisci quote massime o medie o Bet365
        O["home_win"] = raw_df.get("MaxH", raw_df.get("AvgH", raw_df.get("B365H", np.nan)))
        O["draw"] = raw_df.get("MaxD", raw_df.get("AvgD", raw_df.get("B365D", np.nan)))
        O["away_win"] = raw_df.get("MaxA", raw_df.get("AvgA", raw_df.get("B365A", np.nan)))
        O["over_2.5"] = raw_df.get("Max>2.5", raw_df.get("Avg>2.5", raw_df.get("B365>2.5", np.nan)))
        O["under_2.5"] = raw_df.get("Max<2.5", raw_df.get("Avg<2.5", raw_df.get("B365<2.5", np.nan)))

        # 3. Costruisci X (Feature per modellazione)
        feature_cols = [
            "LeagueName", "SeasonYear", "DateClean", "HomeTeam", "AwayTeam",
            "FTHG", "FTAG", "HTHG", "HTAG", "HS", "AS", "HST", "AST", "HC", "AC", "HF", "AF", "HY", "AY", "HR", "AR"
        ]
        available_cols = [c for c in feature_cols if c in raw_df.columns]
        X = raw_df[available_cols].copy()

        return X, Y, O

if __name__ == "__main__":
    loader = HistoricalDataLoader()
    print("Testing HistoricalDataLoader per Serie A 2023...")
    X, Y, O = loader.load_dataset(leagues=["Serie A"], years=[2023])
    print(f"✅ Successo! Partite caricate: {len(X)}")
    print("Target sample:")
    print(Y.head(3))
    print("Odds sample:")
    print(O.head(3))

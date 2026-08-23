#!/usr/bin/env python3
"""
query_player.py — Interroga istantaneamente il database giocatori di BAgent.

Uso:
    python scripts/query_player.py "Guimaraes"
    python scripts/query_player.py --team "Juventus"
    python scripts/query_player.py --league "Premier League" --pos "Attacker"
"""

import sqlite3
import sys
import argparse
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "storage" / "database" / "bagent.db"

def normalize(text):
    if not text:
        return ""
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn").lower().replace("ı", "i")

def main():
    parser = argparse.ArgumentParser(description="Cerca giocatori nel DB di BAgent")
    parser.add_argument("name", nargs="?", default="", help="Nome o cognome del giocatore")
    parser.add_argument("--team", default="", help="Filtra per nome squadra")
    parser.add_argument("--league", default="", help="Filtra per campionato")
    parser.add_argument("--pos", default="", help="Filtra per posizione (Attacker, Midfielder, Defender, Goalkeeper)")
    args = parser.parse_args()

    con = sqlite3.connect(DB_PATH)
    con.create_function("NORM", 1, normalize)
    cur = con.cursor()

    query = "SELECT p.name, p.number, p.position, p.age, p.team_name, p.league_name FROM players p WHERE 1=1"
    params = []

    if args.name:
        query += " AND NORM(p.name) LIKE ?"
        params.append(f"%{normalize(args.name)}%")
    if args.team:
        query += " AND NORM(p.team_name) LIKE ?"
        params.append(f"%{normalize(args.team)}%")
    if args.league:
        query += " AND NORM(p.league_name) LIKE ?"
        params.append(f"%{normalize(args.league)}%")
    if args.pos:
        query += " AND NORM(p.position) LIKE ?"
        params.append(f"%{normalize(args.pos)}%")

    query += " ORDER BY p.league_name, p.team_name, p.position, p.name LIMIT 50;"

    cur.execute(query, params)
    rows = cur.fetchall()

    if not rows:
        print("❌ Nessun giocatore trovato con i criteri specificati.")
        return

    print(f"\n🔍 Risultati Trovati ({len(rows)} giocatori):\n" + "="*75)
    print(f"{'Giocatore':<24} | {'N°':<3} | {'Ruolo':<11} | {'Età':<4} | {'Squadra':<18} | {'Lega'}")
    print("-"*75)
    for r in rows:
        num = f"#{r[1]}" if r[1] is not None else "-"
        print(f"{r[0]:<24} | {num:<3} | {r[2]:<11} | {r[3] or '-':<4} | {r[4]:<18} | {r[5]}")
    print("="*75 + "\n")
    con.close()

if __name__ == "__main__":
    main()

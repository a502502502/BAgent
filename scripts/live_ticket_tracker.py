# -*- coding: utf-8 -*-
"""
scripts/live_ticket_tracker.py — Tracker Live Istantaneo Biglietti BAgent.
Interroga FlashscoreLiveEngine e mostra lo stato reale, punteggio e minuti di gioco
di tutti i match in schedina con ZERO latenza.
"""
from __future__ import annotations
import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from services.football.external.sources.flashscore_live import FlashscoreLiveEngine

def check_all_tickets():
    engine = FlashscoreLiveEngine()
    print("📡 [BAgent Live Engine] Interrogazione feed Flashscore/Diretta in tempo reale...")
    feed = engine.fetch_feed()
    print(f"✅ Feed scaricato con successo: {len(feed)} partite monitorate live nel mondo.\n")

    targets = [
        # Pomeriggio Reconstituito (13:30 - 14:00, chiusura entro 15:55)
        {"name": "Nakhon Pathom vs Kanchanaburi", "kw": "Kanchanaburi", "pick": "X2 @ 1.27", "ticket": "Booster Pomeriggio"},
        {"name": "Gareji Sagarejo vs Gori", "kw": "Gareji", "pick": "1 @ 1.72 (o 1X @ 1.18)", "ticket": "Booster Pomeriggio"},
        {"name": "Kulikiv vs Veres Rivne", "kw": "Veres-Rivne", "pick": "2 @ 1.63 (o X2 @ 1.19)", "ticket": "Booster Pomeriggio"},
        {"name": "Merani Martvili vs Sioni", "kw": "Merani", "pick": "1X @ 1.28 (Opzionale 4ª)", "ticket": "Booster Pomeriggio"},
        # Sera (18:45 - 21:30)
        {"name": "Omonia vs Celta Vigo", "kw": "Celta", "pick": "X2 + MG 1-5 @ 1.42", "ticket": "Ticket 3"},
        {"name": "Ararat-Armenia vs Sparta Praga", "kw": "Ararat", "pick": "Sparta X2 @ 1.17", "ticket": "Europa League"},
        {"name": "Atl. Madrid vs Osasuna", "kw": "Osasuna", "pick": "1X + MG 1-4 @ 1.40", "ticket": "Ticket 1"},
        {"name": "Deportivo La Coruña vs Sevilla", "kw": "Sevilla", "pick": "1X + MG 1-4 @ 1.40", "ticket": "Ticket 2"},
        {"name": "AC Milan vs Benfica", "kw": "Benfica", "pick": "1X + MG 1-5 @ 1.42", "ticket": "Ticket 1"},
        {"name": "Bayer Leverkusen vs Celje", "kw": "Celje", "pick": "MultiGol 2-5 / Corner", "ticket": "Ticket 2 & 4"},
        {"name": "Manchester United vs Brighton", "kw": "Brighton", "pick": "MultiGol 2-5 / Tempi", "ticket": "Ticket 2 & Gem"},
        {"name": "Anderlecht vs Lyon", "kw": "Anderlecht", "pick": "MultiGol 2-5 @ 1.34", "ticket": "Ticket 3"},
        {"name": "Barcelona vs Racing Santander", "kw": "Racing Santander", "pick": "MultiGol 2-5 / 2-4 Casa", "ticket": "Ticket 1 & 4"}
    ]

    print(f"{'PARTITA':<32} | {'SCORE':<7} | {'STATO':<13} | {'PRONOSTICO':<22} | {'SCHEDINA'}")
    print("-" * 95)

    for t in targets:
        kw = t["kw"].lower()
        found = None
        for m in feed:
            if kw in m["home"].lower() or kw in m["away"].lower():
                found = m
                break
        
        if found:
            score = found["score"]
            status = found["status"]
            if found["status_code"] in ["2", "12", "13"]:
                status = f"🔴 {found['status']} {found['period']}'"
            elif found["status_code"] == "3":
                status = "🏁 Finale"
            elif found["status_code"] == "1":
                status = "⏳ Programmata"
            
            p_name = f"{found['home']} - {found['away']}"
            if len(p_name) > 31: p_name = p_name[:29] + ".."
            print(f"{p_name:<32} | {score:^7} | {status:<13} | {t['pick']:<22} | {t['ticket']}")
        else:
            print(f"{t['name']:<32} | {'-':^7} | {'⏳ Fuori Feed':<13} | {t['pick']:<22} | {t['ticket']}")

if __name__ == "__main__":
    check_all_tickets()

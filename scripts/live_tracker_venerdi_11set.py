#!/usr/bin/env python3
"""
scripts/live_tracker_venerdi_11set.py — Live Sentinel Telegram & Database per Venerdì 11 Settembre 2026.
Monitora in tempo reale le schedine in corso (Schedina 2, Schedina 3 e Schedina di Recupero):
1. Union Berlin vs Schalke 04 (FID 1575164) — 1X + Under 4.5 Gol @ 1.68
2. Venezia vs Fiorentina (FID 1550126) — Venezia Corner Over 3.5 @ 1.55
3. Sevilla vs Valencia (FID 1570381) — Over 1.5 Gol @ 1.40
4. Pisa vs Virtus Entella (FID 1601531) — 1X + Over 1.5 Gol @ 1.58
5. Newell's Old Boys vs Vélez Sarsfield (FID 1493133) — X2 @ 1.46 (Recupero)
6. 2 de Mayo vs Club Libertad (FID 1632002) — Under 2.5 Gol @ 1.62 (Recupero)
"""

from __future__ import annotations
import os
import sys
import time
import sqlite3
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_HOST = "v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")
DB_PATH = ROOT / "storage" / "database" / "bagent.db"

FID_UNION = 1575164
FID_VENEZIA = 1550126
FID_SEVILLA = 1570381
FID_PISA = 1601531
FID_NEWELL = 1493133
FID_LIBERTAD = 1632002

MATCH_CONFIG = {
    FID_UNION: {
        "name": "Union Berlin vs Schalke 04",
        "league": "Bundesliga",
        "market": "1X + Under 4.5 Gol",
        "odds": 1.68,
        "tickets": ["Schedina 2"],
    },
    FID_VENEZIA: {
        "name": "Venezia vs Fiorentina",
        "league": "Serie A",
        "market": "Venezia Corner Over 3.5",
        "odds": 1.55,
        "tickets": ["Schedina 3"],
    },
    FID_SEVILLA: {
        "name": "Sevilla vs Valencia",
        "league": "LaLiga",
        "market": "Over 1.5 Gol Totali",
        "odds": 1.40,
        "tickets": ["Schedina 3"],
    },
    FID_PISA: {
        "name": "Pisa vs Virtus Entella",
        "league": "Serie B",
        "market": "1X + Over 1.5 Gol",
        "odds": 1.58,
        "tickets": ["Schedina 2"],
    },
    FID_NEWELL: {
        "name": "Newell's Old Boys vs Vélez Sarsfield",
        "league": "Liga Profesional (ARG)",
        "market": "Doppia Chance X2",
        "odds": 1.46,
        "tickets": ["Schedina Recupero"],
    },
    FID_LIBERTAD: {
        "name": "2 de Mayo vs Club Libertad",
        "league": "Division Profesional (PAR)",
        "market": "Under 2.5 Gol",
        "odds": 1.62,
        "tickets": ["Schedina Recupero"],
    },
}

TICKETS = {
    "CONFIRMED_G2_UNION_PISA": {
        "name": "Schedina 2",
        "legs": [FID_UNION, FID_PISA],
        "stake": 30.0,
        "odds": 2.65,
        "payout": 79.63,
    },
    "CONFIRMED_G3_VENEZIA_SEVILLA": {
        "name": "Schedina 3",
        "legs": [FID_VENEZIA, FID_SEVILLA],
        "stake": 30.0,
        "odds": 2.17,
        "payout": 65.10,
    },
    "CONFIRMED_RECUPERO_VELEZ_2DEMAYO": {
        "name": "Schedina Recupero",
        "legs": [FID_NEWELL, FID_LIBERTAD],
        "stake": 15.0,
        "odds": 2.37,
        "payout": 35.55,
    },
}

def send_tg(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Errore invio TG: {e}", flush=True)
        return False

def get_fixture_data(fid: int):
    url = f"https://{API_HOST}/fixtures?id={fid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            res = r.json().get("response", [])
            if res:
                return res[0]
    except Exception as e:
        print(f"Errore API per {fid}: {e}", flush=True)
    return None

def update_db_leg(ticket_id: str, match_name: str, status: str):
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE bet_leg_ledger 
            SET result_status = ? 
            WHERE ticket_id = ? AND match_name LIKE ?
        """, (status, ticket_id, f"%{match_name.split()[0]}%"))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Errore update DB leg: {e}", flush=True)

def update_db_ticket(ticket_id: str, status: str, pnl: float):
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE ticket_ledger 
            SET status = ?, profit_loss_eur = ? 
            WHERE ticket_id = ?
        """, (status, pnl, ticket_id))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Errore update DB ticket: {e}", flush=True)

def main():
    print(f"=== [BAGENT] Live Sentinel con Schedina Recupero ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===", flush=True)
    
    recupero_msg = (
        "🔄 <b>BAGENT SCHEDINA RECUPERO AGGIUNTA AL MONITORAGGIO</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1. 🇦🇷 <b>Newell's Old Boys vs Vélez Sarsfield</b>\n"
        "   • Pick: <b>Doppia Chance X2</b> @ 1.46 (Ore 22:00)\n"
        "2. 🇵🇾 <b>CS 2 de Mayo vs Club Libertad</b>\n"
        "   • Pick: <b>Under 2.5 Gol</b> @ 1.62 (Ore 23:30 - Scontro 1ª vs 2ª)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 <b>Quota Totale:</b> 2.37×\n"
        "🎯 <i>Strict Pair filtrata: scartate leghe opache e altitudini fasulle.</i>"
    )
    send_tg(recupero_msg)

    seen_goals = {FID_UNION: 2, FID_VENEZIA: 3, FID_SEVILLA: 0, FID_PISA: 3, FID_NEWELL: 0, FID_LIBERTAD: 0}
    seen_kickoff = set([FID_UNION, FID_VENEZIA, FID_SEVILLA, FID_PISA])
    venezia_corners_seen = 1
    early_won_legs = set()
    finished_matches = set()
    leg_results = {}

    while len(finished_matches) < len(MATCH_CONFIG):
        for fid, cfg in MATCH_CONFIG.items():
            if fid in finished_matches:
                continue

            data = get_fixture_data(fid)
            if not data:
                continue

            status_obj = data.get("fixture", {}).get("status", {})
            st_short = status_obj.get("short", "NS")
            elapsed = status_obj.get("elapsed") or 0
            gh = data.get("goals", {}).get("home", 0) or 0
            ga = data.get("goals", {}).get("away", 0) or 0
            tot_goals = gh + ga

            # Kickoff
            if st_short == "1H" and fid not in seen_kickoff:
                seen_kickoff.add(fid)
                send_tg(
                    f"▶️ <b>CALCIO D'INIZIO:</b> {cfg['name']} ({cfg['league']})!\n"
                    f"🎯 Nostro Pick: <b>{cfg['market']}</b> (@ {cfg['odds']})"
                )
                print(f"[KICKOFF] {cfg['name']}", flush=True)

            # Notifica Gol
            if tot_goals > seen_goals[fid] and st_short in ["1H", "2H", "ET"]:
                seen_goals[fid] = tot_goals
                events = data.get("events", [])
                scorer_info = "Gol"
                for ev in reversed(events):
                    if ev.get("type") == "Goal":
                        p_name = ev.get("player", {}).get("name", "")
                        t_name = ev.get("team", {}).get("name", "")
                        scorer_info = f"{p_name} ({t_name})"
                        break

                send_tg(
                    f"⚽ <b>GOL LIVE ({elapsed}')!</b> {cfg['name']}\n"
                    f"Risultato: <b>{gh} - {ga}</b>\n"
                    f"Marcatore: {scorer_info}\n"
                    f"🎯 Nostro Pick: <b>{cfg['market']}</b>"
                )
                print(f"[GOAL] {cfg['name']} -> {gh}-{ga}", flush=True)

            # Anticipo matematico Over Siviglia
            if fid == FID_SEVILLA and tot_goals >= 2 and fid not in early_won_legs:
                early_won_legs.add(fid)
                send_tg(
                    f"🎉 <b>BOOM! SIVIGLIA-VALENCIA OVER 1.5 PRESO IN ANTICIPO!</b>\n"
                    f"Risultato al {elapsed}': <b>{gh} - {ga}</b>!\n"
                    f"✅ Selezione valida per Schedina 3 archiviata!"
                )

            # Corner Venezia
            if fid == FID_VENEZIA:
                stats_list = data.get("statistics", [])
                for s in stats_list:
                    if "venezia" in s.get("team", {}).get("name", "").lower():
                        for item in s.get("statistics", []):
                            if item.get("type") == "Corner Kicks":
                                v_corners = int(item.get("value") or 0)
                                if v_corners > venezia_corners_seen:
                                    venezia_corners_seen = v_corners
                                    send_tg(
                                        f"🚩 <b>CORNER VENEZIA ({elapsed}')!</b> Conteggio: <b>{v_corners}/4</b>\n"
                                        f"Punteggio: Venezia {gh} - {ga} Fiorentina\n"
                                        f"Target Over 3.5: {'🎯 PRESO AL 100%!' if v_corners >= 4 else f'Mancano {4 - v_corners} corner'}"
                                    )
                                    print(f"[CORNER] Venezia {v_corners}/4", flush=True)

                                if v_corners >= 4 and fid not in early_won_legs:
                                    early_won_legs.add(fid)
                                    send_tg(
                                        f"🎉 <b>CASSA CORNER! VENEZIA OVER 3.5 CORNER PRESO AL 100%!</b>\n"
                                        f"Battuto il 4° corner al {elapsed}'! Selezione Schedina 3 archiviata!"
                                    )

            # Fine Partita (FT)
            if st_short in ["FT", "AET", "PEN"]:
                finished_matches.add(fid)
                
                won = False
                if fid == FID_UNION:
                    won = (gh >= ga) and (tot_goals <= 4)
                elif fid == FID_VENEZIA:
                    won = (venezia_corners_seen >= 4)
                elif fid == FID_SEVILLA:
                    won = (tot_goals >= 2)
                elif fid == FID_PISA:
                    won = (gh >= ga) and (tot_goals >= 2)
                elif fid == FID_NEWELL:
                    won = (ga >= gh) # X2 (Velez away)
                elif fid == FID_LIBERTAD:
                    won = (tot_goals <= 2) # Under 2.5

                leg_results[fid] = won
                outcome_str = "✅ PRESA AL 100%" if won else "❌ PERSA"
                send_tg(
                    f"🏁 <b>RISULTATO FINALE:</b> {cfg['name']}\n"
                    f"Punteggio: <b>{gh} - {ga}</b> (Totale gol: {tot_goals})\n"
                    f"Mercato: {cfg['market']} (@ {cfg['odds']}) ➔ <b>{outcome_str}</b>"
                )
                print(f"[FT] {cfg['name']} -> {outcome_str}", flush=True)

            time.sleep(1)

        # Controllo se un ticket è completato
        for t_id, t_info in TICKETS.items():
            t_legs = t_info["legs"]
            if all(l in leg_results for l in t_legs):
                all_won = all(leg_results[l] for l in t_legs)
                t_status = "WON" if all_won else "LOST"
                pnl = (t_info["payout"] - t_info["stake"]) if all_won else -t_info["stake"]
                
                update_db_ticket(t_id, t_status, pnl)
                for l in t_legs:
                    update_db_leg(t_id, MATCH_CONFIG[l]["name"], "WON" if leg_results[l] else "LOST")

        time.sleep(40)

    print("Tutti i match monitorati. Live Sentinel concluso.", flush=True)

if __name__ == "__main__":
    main()

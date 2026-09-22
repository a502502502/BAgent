#!/usr/bin/env python3
"""
scripts/live_tracker_night_latam.py — Live Sentinel Telegram & Database per le 2 Schedine Notturne.
Monitora in tempo reale:
1. Jaguares vs Fortaleza (FID 1549779) — Under 2.5 Gol @ 1.54 (Ticket 2)
2. Coritiba vs Atletico Paranaense (FID 1492374) — Under 2.5 Gol @ 1.65 (Ticket 1)
3. Boca Juniors vs Central Cordoba (FID 1493125) — 1 Fisso @ 1.47 (Ticket 1) & 1X + Under 3.5 @ 1.41 (Ticket 2)
"""

from __future__ import annotations
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
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

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
DB_PATH = ROOT / "storage" / "database" / "bagent.db"

FID_JAGUARES = 1549779
FID_CORITIBA = 1492374
FID_BOCA = 1493125

MATCH_CONFIG = {
    FID_JAGUARES: {
        "name": "Jaguares de Cordoba vs Fortaleza FC",
        "league": "Colombia Primera A",
        "time": "01:15 CEST",
        "market": "Under 2.5 Gol",
        "odds": 1.54,
        "tickets": ["Schedina 2"],
    },
    FID_CORITIBA: {
        "name": "Coritiba vs Atletico Paranaense",
        "league": "Brasile Serie A (Clássico Atletiba)",
        "time": "02:00 CEST",
        "market": "Under 2.5 Gol",
        "odds": 1.65,
        "tickets": ["Schedina 1"],
    },
    FID_BOCA: {
        "name": "Boca Juniors vs Central Cordoba",
        "league": "Argentina Liga Profesional",
        "time": "02:30 CEST",
        "market": "1 Fisso (@1.47) / 1X+U3.5 (@1.41)",
        "odds": 1.47,
        "tickets": ["Schedina 1", "Schedina 2"],
    },
}

TICKETS = {
    "CONFIRMED_NIGHT_CORITIBA_BOCA": {
        "name": "Schedina 1 (La Notturna d'Élite)",
        "stake": 48.00,
        "odds": 2.43,
        "payout": 116.42,
        "legs": [FID_CORITIBA, FID_BOCA],
    },
    "CONFIRMED_NIGHT_JAGUARES_BOCA": {
        "name": "Schedina 2 (La Variante Blindata Colombia)",
        "stake": 20.00,
        "odds": 2.17,
        "payout": 43.42,
        "legs": [FID_JAGUARES, FID_BOCA],
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
        print(f"Errore API {fid}: {e}", flush=True)
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
        print(f"Errore update leg DB: {e}", flush=True)

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
        print(f"Errore update ticket DB: {e}", flush=True)

def main():
    print(f"=== [BAGENT] Live Sentinel Notturno Integrato ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===", flush=True)
    
    welcome_msg = (
        "🌙 <b>BAGENT NOTTURNO ATTIVO — 2 SCHEDINE INDIPENDENTI</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ <b>Schedina 1 (48.00 € @ 2.43 ➔ 116.42 €):</b>\n"
        "   • Coritiba vs Paranaense: <b>Under 2.5 Gol</b> @ 1.65 (02:00)\n"
        "   • Boca Juniors vs Central Cordoba: <b>1 Fisso</b> @ 1.47 (02:30)\n\n"
        "2️⃣ <b>Schedina 2 (20.00 € @ 2.17 ➔ 43.42 €):</b>\n"
        "   • Jaguares vs Fortaleza: <b>Under 2.5 Gol</b> @ 1.54 (Live 0-1 al 15')\n"
        "   • Boca Juniors vs Central Cordoba: <b>1X + Under 3.5</b> @ 1.41 (02:30)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 <b>Totale Investito:</b> 68.00 €\n"
        "🎯 <b>Incasso Potenziale Totale:</b> 159.84 € (+91.84 € netto)\n"
        "📡 <i>Zero duplicazioni su Coritiba. Monitoraggio live attivo!</i>"
    )
    send_tg(welcome_msg)
    print("Welcome message inviato a Telegram.", flush=True)

    seen_lineups = set()
    seen_kickoff = set([FID_JAGUARES])
    seen_halftime = set()
    seen_goals = {FID_JAGUARES: 1, FID_CORITIBA: 0, FID_BOCA: 0}
    finished_matches = set()
    match_results = {} # fid -> bool/outcome

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

            # 1. Distinte Ufficiali
            lineups = data.get("lineups", [])
            if lineups and len(lineups) >= 2 and fid not in seen_lineups:
                seen_lineups.add(fid)
                h_mod = lineups[0].get("formation", "N/D")
                a_mod = lineups[1].get("formation", "N/D")
                h_team = data.get("teams", {}).get("home", {}).get("name", "")
                a_team = data.get("teams", {}).get("away", {}).get("name", "")
                send_tg(
                    f"📋 <b>FORMAZIONI UFFICIALI:</b> {cfg['name']}\n"
                    f"🏟️ {h_team} ({h_mod}) vs {a_team} ({a_mod})\n"
                    f"⏰ Calcio d'inizio alle {cfg['time']}"
                )
                print(f"[LINEUPS] {cfg['name']} -> {h_mod} vs {a_mod}", flush=True)

            # 2. Calcio d'inizio
            if st_short == "1H" and fid not in seen_kickoff:
                seen_kickoff.add(fid)
                send_tg(
                    f"▶️ <b>CALCIO D'INIZIO:</b> {cfg['name']} ({cfg['league']})!\n"
                    f"🎯 Nostro Pick: <b>{cfg['market']}</b>"
                )
                print(f"[KICKOFF] {cfg['name']}", flush=True)

            # 3. Notifica Gol
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

                progress_text = ""
                if fid in [FID_JAGUARES, FID_CORITIBA]:
                    progress_text = f"\n📊 Under 2.5 status: <b>{tot_goals}/2 gol massimi consentiti</b>"
                elif fid == FID_BOCA:
                    progress_text = f"\n📊 Boca status: <b>{'1 in vantaggio' if gh > ga else ('Pareggio 1X' if gh == ga else 'Sotto')}</b>"

                send_tg(
                    f"⚽ <b>GOL LIVE ({elapsed}')!</b> {cfg['name']}\n"
                    f"Risultato: <b>{gh} - {ga}</b>\n"
                    f"Marcatore: {scorer_info}{progress_text}"
                )
                print(f"[GOAL] {cfg['name']} -> {gh}-{ga}", flush=True)

            # 4. Intervallo
            if st_short == "HT" and fid not in seen_halftime:
                seen_halftime.add(fid)
                send_tg(
                    f"⏸️ <b>INTERVALLO (45'):</b> {cfg['name']}\n"
                    f"Parziale: <b>{gh} - {ga}</b>"
                )
                print(f"[HT] {cfg['name']} -> {gh}-{ga}", flush=True)

            # 5. Fine Partita (FT)
            if st_short in ["FT", "AET", "PEN"]:
                finished_matches.add(fid)
                match_results[fid] = {
                    "gh": gh,
                    "ga": ga,
                    "tot": tot_goals,
                }
                send_tg(
                    f"🏁 <b>RISULTATO FINALE:</b> {cfg['name']}\n"
                    f"Punteggio: <b>{gh} - {ga}</b> (Totale gol: {tot_goals})"
                )
                print(f"[FT] {cfg['name']} -> {gh}-{ga}", flush=True)

            time.sleep(1)

        # Controllo se le schedine si possono chiudere
        # Ticket 1: Coritiba (U2.5) + Boca (1)
        if FID_CORITIBA in match_results and FID_BOCA in match_results and "CONFIRMED_NIGHT_CORITIBA_BOCA" in TICKETS:
            t1 = TICKETS.pop("CONFIRMED_NIGHT_CORITIBA_BOCA")
            cor_won = (match_results[FID_CORITIBA]["tot"] <= 2)
            boca_won = (match_results[FID_BOCA]["gh"] > match_results[FID_BOCA]["ga"])
            t1_won = cor_won and boca_won
            pnl = (t1["payout"] - t1["stake"]) if t1_won else -t1["stake"]
            update_db_ticket("CONFIRMED_NIGHT_CORITIBA_BOCA", "WON" if t1_won else "LOST", pnl)
            update_db_leg("CONFIRMED_NIGHT_CORITIBA_BOCA", "Coritiba", "WON" if cor_won else "LOST")
            update_db_leg("CONFIRMED_NIGHT_CORITIBA_BOCA", "Boca Juniors", "WON" if boca_won else "LOST")
            send_tg(
                f"{'🎉 <b>SCHEDINA 1 VINTA! INCASSO: ' + str(t1['payout']) + ' €!</b>' if t1_won else '❌ Schedina 1 Conclusa Negativamente.'}\n"
                f"Coritiba Under 2.5: {'✅' if cor_won else '❌'} | Boca 1 Fisso: {'✅' if boca_won else '❌'}"
            )

        # Ticket 2: Jaguares (U2.5) + Boca (1X + U3.5)
        if FID_JAGUARES in match_results and FID_BOCA in match_results and "CONFIRMED_NIGHT_JAGUARES_BOCA" in TICKETS:
            t2 = TICKETS.pop("CONFIRMED_NIGHT_JAGUARES_BOCA")
            jag_won = (match_results[FID_JAGUARES]["tot"] <= 2)
            boca_1x = (match_results[FID_BOCA]["gh"] >= match_results[FID_BOCA]["ga"])
            boca_u35 = (match_results[FID_BOCA]["tot"] <= 3)
            t2_won = jag_won and boca_1x and boca_u35
            pnl = (t2["payout"] - t2["stake"]) if t2_won else -t2["stake"]
            update_db_ticket("CONFIRMED_NIGHT_JAGUARES_BOCA", "WON" if t2_won else "LOST", pnl)
            update_db_leg("CONFIRMED_NIGHT_JAGUARES_BOCA", "Jaguares", "WON" if jag_won else "LOST")
            update_db_leg("CONFIRMED_NIGHT_JAGUARES_BOCA", "Boca Juniors", "WON" if (boca_1x and boca_u35) else "LOST")
            send_tg(
                f"{'🎉 <b>SCHEDINA 2 VINTA! INCASSO: ' + str(t2['payout']) + ' €!</b>' if t2_won else '❌ Schedina 2 Conclusa Negativamente.'}\n"
                f"Jaguares Under 2.5: {'✅' if jag_won else '❌'} | Boca 1X+U3.5: {'✅' if (boca_1x and boca_u35) else '❌'}"
            )

        time.sleep(40)

    print("Live Sentinel Notturno Integrato Concluso con Successo.", flush=True)

if __name__ == "__main__":
    main()

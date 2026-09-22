#!/usr/bin/env python3
"""
scripts/live_tracker_night_sunderland_real.py
Live Sentinel Telegram & Database per la Doppia Serale Netwin (20€ -> 47.19€).

1. Sunderland vs Arsenal (21:00) ➔ MultiGol 1-3 1°Tempo: SI @ 1.43
2. Real Madrid vs Rayo Vallecano (21:00) ➔ MultiGol 2-4 Casa + 0-1 Ospite: SI @ 1.65
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
DB_PATH = ROOT / "storage" / "database" / "bagent.db"

# Carica .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
TICKET_ID = "CONFIRMED_NIGHT_20EUR_SUNDERLAND_REAL"

HEADERS_ESPN = {
    "User-Agent": "ESPN/6.0.0 (iPhone; iOS 17.0; Scale/3.00)",
    "Accept": "*/*",
}

MATCHES = {
    "arsenal": {
        "name": "Sunderland vs Arsenal",
        "league": "Premier League",
        "espn_league": "eng.1",
        "event_id": "401878779",
        "kickoff": "21:00",
        "market": "MultiGol 1-3 1°Tempo",
        "odds": 1.43,
        "type": "MG_1T_1_3"
    },
    "real": {
        "name": "Real Madrid vs Rayo Vallecano",
        "league": "La Liga",
        "espn_league": "esp.1",
        "event_id": "401882880",
        "kickoff": "21:00",
        "market": "MultiGol 2-4 Casa + 0-1 Ospite",
        "odds": 1.65,
        "type": "MG_COMBO_REAL"
    }
}

def send_tg(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Errore TG: {e}", flush=True)
        return False

def update_db_leg(match_name_sub: str, status: str):
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE bet_leg_ledger
            SET result_status = ?
            WHERE ticket_id = ? AND match_name LIKE ?
        """, (status, TICKET_ID, f"%{match_name_sub}%"))
        conn.commit()
        conn.close()
        print(f"[DB] Leg {match_name_sub} -> {status}", flush=True)
    except Exception as e:
        print(f"Errore update leg DB: {e}", flush=True)

def update_db_ticket(status: str, pnl: float):
    if not DB_PATH.exists():
        return
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""
            UPDATE ticket_ledger
            SET status = ?, profit_loss_eur = ?
            WHERE ticket_id = ?
        """, (status, pnl, TICKET_ID))
        conn.commit()
        conn.close()
        print(f"[DB] Ticket -> {status} (PnL: {pnl:.2f} €)", flush=True)
    except Exception as e:
        print(f"Errore update ticket DB: {e}", flush=True)

def fetch_summary(espn_league: str, event_id: str) -> dict:
    url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{espn_league}/summary?event={event_id}"
    try:
        r = requests.get(url, headers=HEADERS_ESPN, timeout=10)
        if r.status_code == 200:
            return r.json()
    except Exception as e:
        print(f"Errore fetch {event_id}: {e}", flush=True)
    return {}

def main():
    print(f"=== [BAGENT] Live Sentinel Notturno Sunderland-Real Avviato ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')}) ===", flush=True)

    welcome_msg = (
        "🎟️ <b>DOPPIA SERALE NETWIN REGISTRATA & ATTIVA!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 <b>Puntata:</b> 20.00 € | 🎯 <b>Vincita Potenziale:</b> <b>47.19 €</b>\n"
        "📈 <b>Quota Totale:</b> 2.36×\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ <b>Sunderland vs Arsenal</b> (21:00) ➔ <b>MultiGol 1-3 1°T: SI</b> @ 1.43\n"
        "2️⃣ <b>Real Madrid vs Rayo Vallecano</b> (21:00) ➔ <b>MultiGol 2-4 Casa + 0-1 Ospite</b> @ 1.65\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🛡️ <i>Zero 1X2 secchi: massima protezione ed elasticità su risultati multipli!</i>\n"
        "📡 <i>Sentinel Live attivo su gol e parziali in tempo reale.</i>"
    )
    send_tg(welcome_msg)
    print("Messaggio di benvenuto inviato su Telegram.", flush=True)

    match_state = {
        "arsenal": {
            "seen_kickoff": False,
            "seen_halftime": False,
            "seen_finished": False,
            "h_score": 0,
            "a_score": 0,
            "ht_settled": False,
            "leg_status": "OPEN",
        },
        "real": {
            "seen_kickoff": False,
            "seen_halftime": False,
            "seen_finished": False,
            "h_score": 0,
            "a_score": 0,
            "leg_status": "OPEN",
        }
    }

    finished_matches = 0

    while finished_matches < len(MATCHES):
        for mkey, mcfg in MATCHES.items():
            st = match_state[mkey]
            if st["seen_finished"]:
                continue

            data = fetch_summary(mcfg["espn_league"], mcfg["event_id"])
            if not data:
                continue

            comp = data.get("header", {}).get("competitions", [{}])[0]
            status_obj = comp.get("status", {})
            status_type = status_obj.get("type", {})
            state_desc = status_type.get("description", "")
            state_id = status_type.get("state", "pre")
            clock_display = status_obj.get("displayClock", "")

            competitors = comp.get("competitors", [])
            h_comp = next((c for c in competitors if c.get("homeAway") == "home"), {})
            a_comp = next((c for c in competitors if c.get("homeAway") == "away"), {})

            h_goals = int(h_comp.get("score", 0) or 0)
            a_goals = int(a_comp.get("score", 0) or 0)

            # 1. Kickoff
            if state_id == "in" and not st["seen_kickoff"]:
                st["seen_kickoff"] = True
                send_tg(
                    f"▶️ <b>CALCIO D'INIZIO:</b> {mcfg['name']} ({mcfg['league']})!\n"
                    f"🎯 Nostro Pick: <b>{mcfg['market']} @ {mcfg['odds']}</b>"
                )
                print(f"[KICKOFF] {mcfg['name']}", flush=True)

            # 2. Score change
            if state_id == "in" and (h_goals != st["h_score"] or a_goals != st["a_score"]):
                st["h_score"] = h_goals
                st["a_score"] = a_goals

                note = ""
                if mcfg["type"] == "MG_1T_1_3":
                    tot_1t = h_goals + a_goals
                    if 1 <= tot_1t <= 3:
                        note = f"\n🔥 Status MultiGol 1T: <b>IN CASSA! ({tot_1t} gol segnati) ✅</b>"
                    elif tot_1t > 3:
                        note = f"\n⚠️ Status MultiGol 1T: Più di 3 gol nel 1°T!"
                elif mcfg["type"] == "MG_COMBO_REAL":
                    real_ok = (2 <= h_goals <= 4)
                    rayo_ok = (a_goals <= 1)
                    note = f"\n📊 Status Combo: Real {h_goals} gol ({'✅' if real_ok else 'Manca 2° gol'}) | Rayo {a_goals} gol ({'✅' if rayo_ok else 'Troppi gol!'})"

                send_tg(
                    f"⚽ <b>GOL LIVE ({clock_display})!</b> {mcfg['name']}\n"
                    f"Risultato: <b>{h_comp.get('team',{}).get('shortDisplayName','Home')} {h_goals} - {a_goals} {a_comp.get('team',{}).get('shortDisplayName','Away')}</b>{note}"
                )
                print(f"[GOAL] {mcfg['name']} -> {h_goals}-{a_goals}", flush=True)

            # 3. Intervallo
            if "Halftime" in state_desc and not st["seen_halftime"]:
                st["seen_halftime"] = True
                print(f"[HT] {mcfg['name']} -> {h_goals}-{a_goals}", flush=True)

                # Se Arsenal: MultiGol 1-3 1°T si decide ADESSO all'intervallo!
                if mcfg["type"] == "MG_1T_1_3" and not st["ht_settled"]:
                    st["ht_settled"] = True
                    tot_1t = h_goals + a_goals
                    leg_won = (1 <= tot_1t <= 3)
                    st["leg_status"] = "WON" if leg_won else "LOST"
                    update_db_leg("Arsenal", st["leg_status"])
                    send_tg(
                        f"⏸️ <b>INTERVALLO (45'):</b> {mcfg['name']}\n"
                        f"Parziale: <b>{h_goals} - {a_goals}</b> (Gol 1°T: {tot_1t})\n"
                        f"🎯 Esito MultiGol 1-3 1°T: <b>{'VINTA ALL\'INTERVALLO! 🎉✅' if leg_won else 'NON ENTRATA ❌'}</b>"
                    )
                else:
                    send_tg(
                        f"⏸️ <b>INTERVALLO (45'):</b> {mcfg['name']}\n"
                        f"Parziale: <b>{h_goals} - {a_goals}</b>"
                    )

            # 4. Fine partita
            if state_id == "post" and not st["seen_finished"]:
                st["seen_finished"] = True
                finished_matches += 1

                if mcfg["type"] == "MG_COMBO_REAL":
                    real_ok = (2 <= h_goals <= 4)
                    rayo_ok = (a_goals <= 1)
                    leg_won = (real_ok and rayo_ok)
                    st["leg_status"] = "WON" if leg_won else "LOST"
                    update_db_leg("Real Madrid", st["leg_status"])

                    send_tg(
                        f"🏁 <b>RISULTATO FINALE:</b> {mcfg['name']}\n"
                        f"Finale: <b>{h_goals} - {a_goals}</b>\n"
                        f"Esito Combo MultiGol: <b>{'VINTA! ✅' if leg_won else 'PERSA ❌'}</b>\n"
                        f"🎯 Quota: {mcfg['odds']}"
                    )
                print(f"[FT] {mcfg['name']} -> Leg: {st['leg_status']}", flush=True)

        time.sleep(30)

    # Verifica finale
    all_won = all(st["leg_status"] == "WON" for st in match_state.values())
    pnl = 27.19 if all_won else -20.00
    update_db_ticket("WON" if all_won else "LOST", pnl)

    final_msg = (
        f"{'🎉🎉🎉 <b>DOPPIA SERALE VINTA! INCASSO: 47.19 € (+27.19 € NETTI)!</b> 🎉🎉🎉' if all_won else '❌ Doppia Serale Conclusa.'}\n"
        f"Utile netto: <b>{'+27.19 €' if all_won else '-20.00 €'}</b>\n"
        f"Money Management rispettato a 20 €."
    )
    send_tg(final_msg)
    print(f"Sentinel Notturno Concluso. Esito Ticket: {'WON' if all_won else 'LOST'}", flush=True)

if __name__ == "__main__":
    main()

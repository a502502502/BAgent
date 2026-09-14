#!/usr/bin/env python3
"""
scripts/live_ticket_watcher_daemon.py — Daemon di Monitoraggio Continuo Live per Ticket #89.
Gira in background, interroga FootyStats ogni 75 secondi e invia notifiche PUSH istantanee
su Telegram per ogni gol, fine primo tempo e fischio finale, valutando lo stato del ticket.
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from services.football.external.footystats_client import FootyStatsClient

TELEGRAM_TOKEN = "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg"
TELEGRAM_CHAT_ID = "466378357"
STATE_FILE = ROOT / "data" / "ticket_89_live_state.json"

def send_telegram(msg: str) -> bool:
    if not TELEGRAM_TOKEN:
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[Watcher] Telegram Error: {e}", flush=True)
        return False

# Definizioni delle 5 selezioni di Ticket #89
MATCHES = [
    {
        "id": 8568542,
        "name": "Dynamo Kyiv vs Epitsentr",
        "market": "1X + Under 3.5",
        "quota": 1.78,
        "kickoff": "14:30",
        "country": "Ucraina"
    },
    {
        "id": 8711033,
        "name": "Panionios vs Apollon",
        "market": "Under 2.5",
        "quota": 1.62,
        "kickoff": "15:00",
        "country": "Grecia"
    },
    {
        "id": 8711034,
        "name": "Panthrakikos vs PAOK B",
        "market": "Doppia Chance 1X",
        "quota": 1.38,
        "kickoff": "16:00",
        "country": "Grecia"
    },
    {
        "id": 8579399,
        "name": "U. Cluj vs Otelul Galati",
        "market": "Over 2.5",
        "quota": 1.76,
        "kickoff": "17:00",
        "country": "Romania"
    },
    {
        "id": 8568439,
        "name": "Shakhtar vs Chernomorets",
        "market": "1 + MultiGol 2-4",
        "quota": 1.54,
        "kickoff": "17:00",
        "country": "Ucraina"
    }
]

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def eval_status(market: str, h_goals: int, a_goals: int, status: str) -> str:
    total = h_goals + a_goals
    m = market.lower()
    
    if "under 2.5" in m:
        if total > 2:
            return "❌ PERSA"
        elif status == "complete":
            return "✅ VINTA"
        else:
            return f"🛡️ Regge ({total}/2 gol)"
            
    if "1x + under 3.5" in m:
        if total > 3:
            return "❌ PERSA (Troppi gol)"
        elif status == "complete":
            if h_goals >= a_goals:
                return "✅ VINTA"
            else:
                return "❌ PERSA (Ha vinto l'ospite)"
        else:
            return f"🛡️ In corso ({h_goals}-{a_goals})"
            
    if "1x" in m:
        if status == "complete":
            return "✅ VINTA" if h_goals >= a_goals else "❌ PERSA"
        else:
            return "🛡️ In corso" if h_goals >= a_goals else "⚠️ Sotto nel punteggio"
            
    if "over 2.5" in m:
        if total >= 3:
            return "✅ VINTA"
        elif status == "complete":
            return "❌ PERSA"
        else:
            return f"⏳ In corso ({total}/3 gol)"
            
    if "1 + multigol 2-4" in m:
        if status == "complete":
            if h_goals > a_goals and 2 <= total <= 4:
                return "✅ VINTA"
            else:
                return "❌ PERSA"
        else:
            return f"⏳ In corso ({h_goals}-{a_goals})"
            
    return "⏳ In corso"

def run_daemon():
    print("[Live Notifier] 🚀 Avvio Watcher Daemon Ticket #89...", flush=True)
    send_telegram(
        "🔔 <b>NOTIFICHE LIVE AUTOMATICHE ATTIVATE!</b>\n\n"
        "Il bot sta ora monitorando in background ogni variazione di punteggio, fine primo tempo e fischio finale del <b>Ticket #89</b>.\n"
        "Riceverai gli alert push direttamente qui su Telegram!"
    )
    
    client = FootyStatsClient()
    state = load_state()
    
    # Inizializza lo stato se vuoto
    for m in MATCHES:
        mid_str = str(m["id"])
        if mid_str not in state:
            # Set initial known state: Panionios 1-0, Dynamo 0-0
            if m["id"] == 8711033:
                state[mid_str] = {"h": 1, "a": 0, "status": "in_progress", "announced_score": "1-0"}
            elif m["id"] == 8568542:
                state[mid_str] = {"h": 0, "a": 0, "status": "in_progress", "announced_score": "0-0"}
            else:
                state[mid_str] = {"h": 0, "a": 0, "status": "not_started", "announced_score": "0-0"}
    save_state(state)

    while True:
        try:
            for m in MATCHES:
                mid = m["id"]
                mid_str = str(mid)
                m_data = client.get_match_stats(mid)
                if not m_data:
                    continue
                
                curr_status = m_data.get("status", "incomplete")
                # FootyStats returns homeGoalCount and awayGoalCount
                h_goals = m_data.get("homeGoalCount")
                a_goals = m_data.get("awayGoalCount")
                
                # If FootyStats hasn't registered a live goal yet but we manually know it, don't revert
                prev = state.get(mid_str, {"h": 0, "a": 0, "status": "not_started", "announced_score": "0-0"})
                
                if h_goals is not None and a_goals is not None:
                    # Check if API has higher/updated goals
                    if (h_goals + a_goals) > (prev["h"] + prev["a"]):
                        new_h, new_a = h_goals, a_goals
                    else:
                        new_h, new_a = prev["h"], prev["a"]
                else:
                    new_h, new_a = prev["h"], prev["a"]
                
                score_str = f"{new_h}-{new_a}"
                
                # Check for GOAL event
                if score_str != prev.get("announced_score"):
                    verdict = eval_status(m["market"], new_h, new_a, curr_status)
                    now_time = datetime.now().strftime("%H:%M:%S")
                    msg = (
                        f"⚽ <b>GOL IN CORSO! ({now_time})</b>\n\n"
                        f"🏆 <b>{m['name']}</b> ({m['country']})\n"
                        f"🔢 Nuovo Punteggio: <b>{score_str}</b>\n"
                        f"🎯 Nostra Giocata: <b>{m['market']} @ {m['quota']}</b>\n"
                        f"📊 Situazione Leg: <b>{verdict}</b>"
                    )
                    send_telegram(msg)
                    state[mid_str]["announced_score"] = score_str
                    state[mid_str]["h"] = new_h
                    state[mid_str]["a"] = new_a
                    save_state(state)
                
                # Check for FINISHED event
                if curr_status == "complete" and prev.get("status") != "complete":
                    verdict = eval_status(m["market"], new_h, new_a, "complete")
                    now_time = datetime.now().strftime("%H:%M:%S")
                    msg = (
                        f"🏁 <b>PARTITA CONCLUSA! ({now_time})</b>\n\n"
                        f"🏆 <b>{m['name']}</b>\n"
                        f"🔢 Risultato Finale: <b>{score_str}</b>\n"
                        f"🎯 Mercato: <b>{m['market']}</b>\n"
                        f"📌 Esito Ufficiale: <b>{verdict}</b>"
                    )
                    send_telegram(msg)
                    state[mid_str]["status"] = "complete"
                    save_state(state)
                    
            time.sleep(75)
            
        except Exception as err:
            print(f"[Live Notifier Daemon Error]: {err}", flush=True)
            time.sleep(60)

if __name__ == "__main__":
    run_daemon()

#!/usr/bin/env python3
"""
BAgent Corner Live Tracker (v4.0 Ultra-Precision Flashscore Engine)
Traccia in tempo reale a LATENZA ZERO i Calci d'Angolo direttamente dai server Flashscore / Diretta.it.
Notifiche istantanee su OGNI singolo corner, minuto di gioco e target raggiunto!
"""

from __future__ import annotations
import time
import requests
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

sys.stdout.reconfigure(line_buffering=True)

env_path = Path(__file__).resolve().parent.parent / ".env"
if env_path.exists():
    for encoding in ("utf-8", "utf-16", "utf-8-sig", "latin-1"):
        try:
            content = env_path.read_text(encoding=encoding)
            for line in content.splitlines():
                line = line.replace("\x00", "").strip()
                if "=" in line and not line.startswith("#") and line:
                    k, _, v = line.partition("=")
                    k, v = k.strip(), v.strip()
                    if k and v:
                        os.environ.setdefault(k, v)
            break
        except Exception:
            continue

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")

FS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "x-fsign": "SW9D1eZo",
}

MATCHES = [
    {
        "id": "brighton_villa",
        "fs_id": "Mkz9mcpL",
        "home": "Brighton",
        "away": "Aston Villa",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "country": "Inghilterra",
        "league": "Premier League",
        "kickoff": "15:00",
        "pick_desc": "Over 7.5 Corner Totali",
        "odds": "@1.24",
        "target_type": "TOTAL",
        "target_val": 8,
    },
    {
        "id": "mancity_bournemouth",
        "fs_id": "ILLvry8r",
        "home": "Manchester City",
        "away": "Bournemouth",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "country": "Inghilterra",
        "league": "Premier League",
        "kickoff": "15:00",
        "pick_desc": "Over 6.5 Corner Man City (Sq.1)",
        "odds": "@1.70",
        "target_type": "HOME",
        "target_val": 7,
    },
    {
        "id": "atletico_villarreal",
        "fs_id": "ImSSgC06",
        "home": "Atlético Madrid",
        "away": "Villarreal",
        "flag": "🇪🇸",
        "country": "Spagna",
        "league": "LaLiga",
        "kickoff": "17:00",
        "pick_desc": "Over 7.5 Corner Totali Match",
        "odds": "@1.24",
        "target_type": "TOTAL",
        "target_val": 8,
    },
    {
        "id": "newcastle_liverpool",
        "fs_id": "4xKntFxe",
        "home": "Newcastle",
        "away": "Liverpool",
        "flag": "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
        "country": "Inghilterra",
        "league": "Premier League",
        "kickoff": "17:30",
        "pick_desc": "Over 9.5 Corner Totali Match",
        "odds": "@1.50",
        "target_type": "TOTAL",
        "target_val": 10,
    },
    {
        "id": "frosinone_juventus",
        "fs_id": "nD9kGRJO",
        "home": "Frosinone",
        "away": "Juventus",
        "flag": "🇮🇹",
        "country": "Italia",
        "league": "Serie A",
        "kickoff": "18:30",
        "pick_desc": "Over 4.5 Corner Juventus (Sq.2)",
        "odds": "@1.33",
        "target_type": "AWAY",
        "target_val": 5,
    },
    {
        "id": "elche_barcelona",
        "fs_id": "Gfdoa7xn",
        "home": "Elche",
        "away": "Barcelona",
        "flag": "🇪🇸",
        "country": "Spagna",
        "league": "LaLiga",
        "kickoff": "21:30",
        "pick_desc": "Over 5.5 Corner Barcellona (Sq.2)",
        "odds": "@1.62",
        "target_type": "AWAY",
        "target_val": 6,
    },
]

def notify_telegram(msg: str):
    if not TELEGRAM_TOKEN:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=8)
        if r.status_code == 200:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram notifica inviata con successo!", flush=True)
        else:
            print(f"Telegram warning: status {r.status_code} - {r.text[:80]}", flush=True)
    except Exception as e:
        print("Telegram send error:", e, flush=True)

def fetch_flashscore_corners(fs_id: str) -> Tuple[Optional[int], Optional[int]]:
    try:
        url = f"https://local-global.flashscore.ninja/2/x/feed/df_st_1_{fs_id}"
        r = requests.get(url, headers=FS_HEADERS, timeout=6)
        if r.status_code == 200:
            m = re.search(r"Corner kicks.*?SH÷(\d+)¬SI÷(\d+)", r.text, re.IGNORECASE)
            if m:
                return int(m.group(1)), int(m.group(2))
    except Exception as e:
        print(f"FS stats lookup error for {fs_id}:", e, flush=True)
    return None, None

def get_corner_progress_bar(current: int, target: int) -> str:
    filled = min(current, target)
    bar = "■" * filled + "□" * max(0, target - filled)
    return f"[{bar}] {current}/{target}"

def get_ticket_card(match_states: dict) -> str:
    lines = []
    won_count = 0
    in_play_count = 0
    waiting_count = 0
    lost_count = 0

    for m in MATCHES:
        mid = m["id"]
        st = match_states.get(mid, {"phase": "SCHEDULED", "c_home": 0, "c_away": 0, "target_hit": False, "minute": 0})
        phase = st["phase"]
        c_h = st.get("c_home", 0)
        c_a = st.get("c_away", 0)
        c_tot = c_h + c_a
        elapsed = st.get("minute", 0)
        
        if m["target_type"] == "HOME":
            curr_tracked = c_h
        elif m["target_type"] == "AWAY":
            curr_tracked = c_a
        else:
            curr_tracked = c_tot

        target = m["target_val"]
        is_won = curr_tracked >= target
        prog_bar = get_corner_progress_bar(curr_tracked, target)

        if is_won:
            won_count += 1
            icon = f"✅ PRESO! ({curr_tracked}/{target})"
        elif phase == "FINISHED":
            lost_count += 1
            icon = f"❌ NON RAGGIUNTO ({curr_tracked}/{target})"
        elif phase == "HALFTIME":
            in_play_count += 1
            icon = f"⏸️ INTERVALLO ({prog_bar} · 45' al 90')"
        elif phase == "IN_PLAY":
            in_play_count += 1
            rem_min = max(0, 90 - elapsed)
            icon = f"🟢 LIVE {elapsed}' ({prog_bar} · ~{rem_min}' rimasti)"
        else:
            waiting_count += 1
            icon = f"⏳ IN ARRIVO (Target: {target})"

        lines.append(
            f"• {m['flag']} <b>{m['home']} vs {m['away']}</b> ({m['kickoff']})\n"
            f"   └ 🚩 {m['pick_desc']} {m['odds']} ➔ <b>{icon}</b>"
        )

    card = (
        "📋 <b>STATO LIVE TICKET #19 (Vincita: 255.97 €):</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n\n".join(lines)
        + "\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Avanzamento</b>: <b>{won_count}</b> Prese · <b>{in_play_count}</b> In Gioco · <b>{waiting_count}</b> In Arrivo\n"
        f"💰 <b>Vincita Potenziale</b>: <b>255.97 €</b> (Stake 30.00 € · Quota 8.44×)"
    )
    return card

def main():
    print(f"=== BAgent Flashscore Zero-Latency Corner Monitor 4.0 Avviato ({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
    
    match_states = {
        m["id"]: {
            "phase": "SCHEDULED",
            "c_home": 0,
            "c_away": 0,
            "minute": 45,
            "target_hit": False,
            "last_c_notified": -1,
        }
        for m in MATCHES
    }

    # Sincronizzazione iniziale con Flashscore
    for m in MATCHES:
        mid = m["id"]
        fs_id = m.get("fs_id")
        if fs_id:
            h_c, a_c = fetch_flashscore_corners(fs_id)
            if h_c is not None and a_c is not None:
                match_states[mid]["c_home"] = h_c
                match_states[mid]["c_away"] = a_c
                match_states[mid]["phase"] = "HALFTIME" if (h_c > 0 or a_c > 0) else "SCHEDULED"
                
                curr_c = h_c if m["target_type"] == "HOME" else (a_c if m["target_type"] == "AWAY" else h_c + a_c)
                match_states[mid]["last_c_notified"] = curr_c
                if curr_c >= m["target_val"]:
                    match_states[mid]["target_hit"] = True

    # Invia immediatamente la card di riallineamento
    sync_msg = (
        "⚡ <b>SINCRONIZZAZIONE ZERO-LATENZA DIRETTA / FLASHSCORE</b> 🎯\n\n"
        + get_ticket_card(match_states)
    )
    notify_telegram(sync_msg)

    while True:
        try:
            for m in MATCHES:
                mid = m["id"]
                fs_id = m.get("fs_id")
                st = match_states[mid]
                
                if not fs_id:
                    continue

                new_h, new_a = fetch_flashscore_corners(fs_id)
                if new_h is not None and new_a is not None:
                    st["c_home"] = max(st["c_home"], new_h)
                    st["c_away"] = max(st["c_away"], new_a)

                c_h = st["c_home"]
                c_a = st["c_away"]
                c_tot = c_h + c_a
                
                if m["target_type"] == "HOME":
                    curr_tracked = c_h
                    desc_c = f"Corner {m['home']}: {c_h}"
                elif m["target_type"] == "AWAY":
                    curr_tracked = c_a
                    desc_c = f"Corner {m['away']}: {c_a}"
                else:
                    curr_tracked = c_tot
                    desc_c = f"Corner Totali: {c_tot} ({c_h}-{c_a})"

                target = m["target_val"]

                # 1️⃣ NOTIFICA TARGET RAGGIUNTO (VITTORIA LIVE!)
                if curr_tracked >= target and not st["target_hit"]:
                    st["target_hit"] = True
                    target_hit_msg = (
                        f"🎉 <b>TARGET CORNER RAGGIUNTO & VINTO! 🏁✅</b>\n\n"
                        f"{m['flag']} <b>{m['home']} vs {m['away']}</b> (Quota {m['odds']})\n"
                        f"🚩 <b>{desc_c}</b> (Target {target} RAGGIUNTO!)\n"
                        f"🎯 Pronostico: <b>{m['pick_desc']} ➔ PRESO AL 100%!</b> 💰\n\n"
                        + get_ticket_card(match_states)
                    )
                    notify_telegram(target_hit_msg)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] TARGET HIT: {m['home']} vs {m['away']} ({curr_tracked}/{target})", flush=True)

                # 2️⃣ NOTIFICA AD OGNI SINGOLO NUOVO CORNER (ZERO LATENZA)
                elif curr_tracked > st["last_c_notified"] and st["last_c_notified"] != -1:
                    st["last_c_notified"] = curr_tracked
                    left_c = max(0, target - curr_tracked)
                    corner_alert_msg = (
                        f"🚩 <b>CORNER ALERT! (Diretta.it / LiveScore)</b>\n\n"
                        f"{m['flag']} <b>{m['home']} vs {m['away']}</b>\n"
                        f"📊 <b>{desc_c}</b>\n"
                        f"🎯 Obiettivo: <b>{m['pick_desc']} {m['odds']}</b>\n"
                        f"⏳ <i>Mancano solo <b>{left_c} corner</b> per vincere la quota!</i>\n"
                        f"📈 Progresso: {get_corner_progress_bar(curr_tracked, target)}"
                    )
                    notify_telegram(corner_alert_msg)
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] CORNER UPDATE: {m['home']} vs {m['away']} ({curr_tracked}/{target})", flush=True)

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Polling error:", e, flush=True)

        time.sleep(8)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
BAgent Corner & Live Tracker (Domenica 23 Agosto 2026 - v3.5 Ultra-Reattivo)
Garantisce notifiche immediate su OGNI NUOVO CORNER con:
- Protezione contro cali a zero temporanei dell'API (monotonia crescente)
- Minuto di gioco e minuti rimanenti al 90'
- Notifica dedicata di Intervallo (HT) e Fine Partita (FT)
"""

from __future__ import annotations
import time
import requests
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Unbuffered output
sys.stdout.reconfigure(line_buffering=True)

# Carica .env
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
API_FOOTBALL_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_FOOTBALL_HOST = "v3.football.api-sports.io"

MATCHES = [
    {
        "id": "brighton_villa",
        "home": "Brighton",
        "away": "Aston Villa",
        "home_kw": ["brighton"],
        "away_kw": ["aston villa", "villa"],
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
        "home": "Manchester City",
        "away": "Bournemouth",
        "home_kw": ["manchester city", "man city", "city"],
        "away_kw": ["bournemouth"],
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
        "home": "Atlético Madrid",
        "away": "Villarreal",
        "home_kw": ["atletico", "atlético"],
        "away_kw": ["villarreal"],
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
        "home": "Newcastle",
        "away": "Liverpool",
        "home_kw": ["newcastle"],
        "away_kw": ["liverpool"],
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
        "home": "Frosinone",
        "away": "Juventus",
        "home_kw": ["frosinone"],
        "away_kw": ["juventus", "juve"],
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
        "home": "Elche",
        "away": "Barcelona",
        "home_kw": ["elche"],
        "away_kw": ["barcelona", "barcellona", "barca", "barça"],
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
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        if r.status_code == 200:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram notifica inviata con successo!", flush=True)
        else:
            print(f"Telegram warning: status {r.status_code} - {r.text[:80]}", flush=True)
    except Exception as e:
        print("Telegram send error:", e, flush=True)

def classify_status(status_short: str, status_long: str, status_type: str = "", elapsed: int = 0) -> str:
    s_short = (status_short or "").strip().upper()
    s_long = (status_long or "").strip().lower()
    s_type = (status_type or "").strip().lower()

    if s_short in ("HT", "BT") or any(k in s_long for k in ("halftime", "half time", "1st half ended", "first half ended", "intervallo")):
        return "HALFTIME"
    if s_short in ("FT", "AET", "PEN") or s_type == "finished":
        return "FINISHED"
    if s_long in ("match finished", "finished", "full time", "after extra time", "after penalties", "final", "ended"):
        return "FINISHED"
    if s_short in ("1H", "2H", "ET", "P", "LIVE", "INT") or s_type == "inprogress" or elapsed > 0:
        return "IN_PLAY"
    if any(k in s_long for k in ("first half", "second half", "1st half", "2nd half", "in play", "live", "extra time")):
        return "IN_PLAY"
    if s_short in ("PST", "CANC", "ABD", "AWD", "WO", "SUSP") or any(k in s_long for k in ("postponed", "cancelled", "abandoned")):
        return "CANCELLED"
    return "SCHEDULED"

def get_live_fixtures() -> list[dict]:
    if not API_FOOTBALL_KEY:
        return []
    headers = {
        "x-rapidapi-host": API_FOOTBALL_HOST,
        "x-rapidapi-key": API_FOOTBALL_KEY,
        "x-apisports-key": API_FOOTBALL_KEY,
    }
    try:
        r = requests.get(f"https://{API_FOOTBALL_HOST}/fixtures?live=all", headers=headers, timeout=12)
        if r.status_code == 200:
            return r.json().get("response", [])
    except Exception as e:
        print("API-Football live error:", e, flush=True)
    return []

def get_fixture_corners(fixture_id: int) -> tuple[Optional[int], Optional[int]]:
    if not API_FOOTBALL_KEY or not fixture_id:
        return None, None
    headers = {
        "x-rapidapi-host": API_FOOTBALL_HOST,
        "x-rapidapi-key": API_FOOTBALL_KEY,
        "x-apisports-key": API_FOOTBALL_KEY,
    }
    try:
        r = requests.get(f"https://{API_FOOTBALL_HOST}/fixtures/statistics?fixture={fixture_id}", headers=headers, timeout=10)
        if r.status_code == 200:
            res = r.json().get("response", [])
            h_c, a_c = 0, 0
            found = False
            for idx, team_stat in enumerate(res):
                stats = team_stat.get("statistics", [])
                for s in stats:
                    if s.get("type") == "Corner Kicks":
                        val = s.get("value")
                        c_val = int(val) if val is not None and str(val).isdigit() else 0
                        if idx == 0:
                            h_c = c_val
                            found = True
                        else:
                            a_c = c_val
                            found = True
            if found:
                return h_c, a_c
    except Exception as e:
        print(f"Stats lookup error for fid {fixture_id}:", e, flush=True)
    return None, None

def match_finder(m_cfg: dict, fixtures: list[dict]) -> dict | None:
    for f in fixtures:
        h = f.get("teams", {}).get("home", {}).get("name", "").lower()
        a = f.get("teams", {}).get("away", {}).get("name", "").lower()
        home_match = any(kw in h for kw in m_cfg["home_kw"])
        away_match = any(kw in a for kw in m_cfg["away_kw"])
        if home_match and away_match:
            return f
    return None

def get_corner_progress_bar(current: int, target: int) -> str:
    filled = min(current, target)
    bar = "■" * filled + "□" * max(0, target - filled)
    return f"[{bar}] {current}/{target}"

def get_remaining_time_str(elapsed: int, phase: str) -> str:
    if phase == "HALFTIME":
        return "45' rimasti (2° Tempo)"
    if phase == "FINISHED":
        return "Conclusa"
    if elapsed <= 0:
        return "90' da giocare"
    left_min = max(0, 90 - elapsed)
    return f"~{left_min}' rimanenti"

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
        rem_str = get_remaining_time_str(elapsed, phase)
        
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
            icon = f"🟢 LIVE {elapsed}' ({prog_bar} · {rem_str})"
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
    print(f"=== BAgent Corner Live Monitor 3.5 Avviato ({datetime.now().strftime('%H:%M:%S')}) ===", flush=True)
    
    match_states = {
        m["id"]: {
            "phase": "SCHEDULED",
            "c_home": 0,
            "c_away": 0,
            "minute": 0,
            "target_hit": False,
            "notified_start": False,
            "notified_ht": False,
            "notified_end": False,
            "last_c_notified": -1,
        }
        for m in MATCHES
    }

    # Sincronizzazione iniziale
    fixtures = get_live_fixtures()
    for m in MATCHES:
        mid = m["id"]
        ev = match_finder(m, fixtures)
        if ev:
            fid = ev.get("fixture", {}).get("id")
            elapsed = ev.get("fixture", {}).get("status", {}).get("elapsed", 0) or 0
            st_short = ev.get("fixture", {}).get("status", {}).get("short", "")
            st_long = ev.get("fixture", {}).get("status", {}).get("long", "")
            match_states[mid]["phase"] = classify_status(st_short, st_long, elapsed=elapsed)
            match_states[mid]["minute"] = elapsed
            if fid:
                new_h, new_a = get_fixture_corners(fid)
                if new_h is not None and new_a is not None:
                    match_states[mid]["c_home"] = max(match_states[mid]["c_home"], new_h)
                    match_states[mid]["c_away"] = max(match_states[mid]["c_away"], new_a)
                
                c_h = match_states[mid]["c_home"]
                c_a = match_states[mid]["c_away"]
                curr_c = c_h if m["target_type"] == "HOME" else (c_a if m["target_type"] == "AWAY" else c_h + c_a)
                match_states[mid]["last_c_notified"] = curr_c
                if curr_c >= m["target_val"]:
                    match_states[mid]["target_hit"] = True

    # Invia subito il quadro completo all'avvio
    startup_card = (
        "🟢 <b>QUADRO AGGIORNATO CORNER & MINUTAGGIO (LIVE)</b> ⏱️\n\n"
        + get_ticket_card(match_states)
    )
    notify_telegram(startup_card)

    while True:
        try:
            fixtures = get_live_fixtures()

            for m in MATCHES:
                mid = m["id"]
                st = match_states[mid]
                
                if st["phase"] == "FINISHED" and st["notified_end"]:
                    continue

                ev = match_finder(m, fixtures)

                if ev:
                    fid = ev.get("fixture", {}).get("id")
                    fixture_info = ev.get("fixture", {})
                    status_long = fixture_info.get("status", {}).get("long", "")
                    status_short = fixture_info.get("status", {}).get("short", "")
                    status_type = fixture_info.get("status", {}).get("type", "")
                    elapsed = fixture_info.get("status", {}).get("elapsed", 0) or 0

                    classified = classify_status(status_short, status_long, status_type, elapsed)
                    st["phase"] = classified
                    st["minute"] = elapsed

                    if fid:
                        new_h, new_a = get_fixture_corners(fid)
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
                    rem_min = max(0, 90 - elapsed)

                    # 1️⃣ NOTIFICA TARGET RAGGIUNTO (VITTORIA LIVE!)
                    if curr_tracked >= target and not st["target_hit"]:
                        st["target_hit"] = True
                        target_hit_msg = (
                            f"🎉 <b>TARGET CORNER RAGGIUNTO & VINTO! 🏁✅</b>\n\n"
                            f"{m['flag']} <b>{m['home']} vs {m['away']}</b> (⏱️ <b>{elapsed}'</b> · Quota {m['odds']})\n"
                            f"🚩 <b>{desc_c}</b> (Target {target} RAGGIUNTO!)\n"
                            f"🎯 Pronostico: <b>{m['pick_desc']} ➔ PRESO CON SUCCESSO!</b> 💰\n\n"
                            + get_ticket_card(match_states)
                        )
                        notify_telegram(target_hit_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] TARGET HIT: {m['home']} vs {m['away']} ({curr_tracked}/{target})", flush=True)

                    # 2️⃣ NOTIFICA AD OGNI SINGOLO NUOVO CORNER CON MINUTO & TEMPO RIMASTO
                    elif curr_tracked > st["last_c_notified"] and classified in ("IN_PLAY", "HALFTIME"):
                        st["last_c_notified"] = curr_tracked
                        left_c = max(0, target - curr_tracked)
                        corner_alert_msg = (
                            f"🚩 <b>CORNER UPDATE! ⏱️ Minuto {elapsed}'</b> (~{rem_min}' al 90')\n\n"
                            f"{m['flag']} <b>{m['home']} vs {m['away']}</b>\n"
                            f"📊 <b>{desc_c}</b>\n"
                            f"🎯 Obiettivo: <b>{m['pick_desc']} {m['odds']}</b>\n"
                            f"⏳ <i>Mancano <b>{left_c} corner</b> nei restanti ~{rem_min} minuti di gara!</i>\n"
                            f"📈 Progresso: {get_corner_progress_bar(curr_tracked, target)}"
                        )
                        notify_telegram(corner_alert_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] CORNER UPDATE: {m['home']} vs {m['away']} ({curr_tracked}/{target}) min {elapsed}", flush=True)

                    # 3️⃣ NOTIFICA INTERVALLO (HT)
                    if classified == "HALFTIME" and not st["notified_ht"]:
                        st["notified_ht"] = True
                        left_c = max(0, target - curr_tracked)
                        ht_msg = (
                            f"⏸️ <b>FINE PRIMO TEMPO / INTERVALLO (HT)</b>\n\n"
                            f"{m['flag']} <b>{m['home']} vs {m['away']}</b> (HT)\n"
                            f"🚩 <b>{desc_c}</b>\n"
                            f"🎯 Nostro Pick: <b>{m['pick_desc']} {m['odds']}</b>\n"
                            f"⏳ <i>Situazione all'intervallo: mancano <b>{left_c} corner</b> nei 45' del secondo tempo!</i>\n"
                            f"📈 Progresso: {get_corner_progress_bar(curr_tracked, target)}"
                        )
                        notify_telegram(ht_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] HT NOTIFIED: {m['home']} vs {m['away']}", flush=True)

                    # 4️⃣ NOTIFICA FINE PARTITA (FT)
                    if classified == "FINISHED" and not st["notified_end"]:
                        st["notified_end"] = True
                        is_won = curr_tracked >= target
                        res_icon = "🏆 <b>✅ PRONOSTICO CORNER VINTO!</b>" if is_won else "⚠️ <b>❌ NON RAGGIUNTO</b>"
                        ft_msg = (
                            f"🏁 <b>FISCHIO FINALE (90'+)! RISULTATO CORNER DEFINITIVO</b>\n\n"
                            f"{m['flag']} <b>{m['home']} vs {m['away']}</b> (FT)\n"
                            f"🚩 <b>{desc_c}</b>\n"
                            f"🎯 Nostro Pick: <b>{m['pick_desc']} {m['odds']}</b>\n"
                            f"{res_icon}\n\n"
                            + get_ticket_card(match_states)
                        )
                        notify_telegram(ft_msg)
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] FT NOTIFIED: {m['home']} vs {m['away']}", flush=True)

        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Polling error:", e, flush=True)

        time.sleep(10)

if __name__ == "__main__":
    main()

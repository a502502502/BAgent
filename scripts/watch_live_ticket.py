#!/usr/bin/env python3
"""
scripts/watch_live_ticket.py — Monitor live ad alta frequenza per la schedina attiva.
Traccia gol, cartellini, corner e tempi sui 5 match e invia alert Telegram immediati.
"""

from __future__ import annotations
import os
import sys
import time
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "X-Fsign": "SW9D1eZo"
}

MATCHES = {
    "d8KSN37t": {
        "name": "Italia vs Turchia",
        "leg": "Italia Over 4.5 Corner",
        "type": "corner_home",
        "target": 5
    },
    "EmmmJQ3L": {
        "name": "Francia vs Belgio",
        "leg": "Belgio Over 1.5 Cartellini",
        "type": "cards_away",
        "target": 2
    },
    "SbevBQf2": {
        "name": "Romania vs Svezia",
        "leg": "Doppia Chance 1°T: 12",
        "type": "dc_1t",
        "target": "12"
    },
    "8twU9Dfc": {
        "name": "Montenegro vs Armenia",
        "leg": "MultiGol 0-2 1°T + 1-3 2°T",
        "type": "mg_tempi"
    },
    "0rhJIHdB": {
        "name": "Bosnia vs Polonia",
        "leg": "Doppia Chance 2°T: 12",
        "type": "dc_2t"
    }
}

STATE_FILE = ROOT / "data" / "live_watch_state.json"


def send_telegram(text: str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[NO TELEGRAM CREDENTIALS]")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            pass
    except Exception as e:
        print(f"Telegram error: {e}", flush=True)


def fetch_match_stats(mid: str) -> dict:
    url = f"https://local-it.flashscore.ninja/2/x/feed/df_st_1_{mid}"
    req = urllib.request.Request(url, headers=HEADERS)
    stats = {}
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            txt = r.read().decode("utf-8", errors="ignore")
            for item in txt.split("~SD÷"):
                parts = item.split("¬SG÷")
                if len(parts) > 1:
                    rest = parts[1]
                    sname = rest.split("¬SH÷")[0]
                    vals = rest.split("¬SH÷")[1].split("¬SI÷")
                    h_val = vals[0].strip()
                    a_val = vals[1].split("¬")[0].strip()
                    stats[sname] = (h_val, a_val)
    except Exception:
        pass
    return stats


def fetch_global_feed() -> dict:
    url = "https://local-it.flashscore.ninja/2/x/feed/f_1_0_1_it_1"
    req = urllib.request.Request(url, headers=HEADERS)
    res = {}
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            txt = r.read().decode("utf-8", errors="ignore")
            for block in txt.split("~AA÷")[1:]:
                mid, _, rest = block.partition("¬")
                fields = {}
                for p in rest.split("¬"):
                    if "÷" in p:
                        k, v = p.split("÷", 1)
                        fields[k] = v
                if mid in MATCHES:
                    res[mid] = {
                        "score": f"{fields.get('AG', '0')}-{fields.get('AH', '0')}",
                        "period": fields.get("AC", ""),
                        "status": fields.get("AB", ""),
                        "ht_score": f"{fields.get('BC', '')}-{fields.get('BD', '')}" if fields.get("BC") else ""
                    }
    except Exception:
        pass
    return res


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_state(state: dict) -> None:
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def main():
    print("[SENTINELLA LIVE ATTIVA] Monitoraggio Nations League...")
    send_telegram("👀 <b>Sentinella BAgent Live Attiva</b>\nMonitoraggio continuo dei 5 match avviato. Riceverai notifiche in tempo reale su ogni gol, corner e cartellino delle tue selezioni!")
    
    state = load_state()

    while True:
        try:
            feed = fetch_global_feed()
            for mid, mcfg in MATCHES.items():
                mname = mcfg["name"]
                mstate = state.get(mid, {})
                finfo = feed.get(mid, {})

                curr_score = finfo.get("score", mstate.get("score", "0-0"))
                curr_period = finfo.get("period", mstate.get("period", ""))
                old_score = mstate.get("score", "0-0")
                old_period = mstate.get("period", "")

                # 1. Rileva GOL
                if curr_score != old_score and curr_score != "-":
                    msg = f"⚽ <b>GOL! {mname}</b>\nNuovo punteggio: <b>{curr_score}</b> (min. {curr_period})\n🎯 Selezione leg: {mcfg['leg']}"
                    print(msg, flush=True)
                    send_telegram(msg)
                    mstate["score"] = curr_score

                # 2. Rileva Intervallo / Fine 1°T
                if curr_period in ["Intervallo", "11", "HT"] and old_period not in ["Intervallo", "11", "HT"]:
                    ht_s = finfo.get("ht_score") or curr_score
                    status_note = ""
                    if mcfg["type"] == "dc_1t":
                        h_g, a_g = ht_s.split("-")
                        won = h_g != a_g
                        status_note = f"\n🏁 <b>Esito Leg DC 1°T (12): {'✅ VINTA' if won else '❌ PERSA'}</b>"
                    msg = f"⏸️ <b>Fine 1° Tempo: {mname}</b>\nPunteggio all'intervallo: <b>{ht_s}</b>{status_note}"
                    print(msg, flush=True)
                    send_telegram(msg)
                    mstate["period"] = curr_period

                # 3. Statistiche dettagliate (Corner & Cartellini)
                stats = fetch_match_stats(mid)
                
                # Check Corner Italia
                if mcfg["type"] == "corner_home":
                    corners = stats.get("Corner kicks", ("0", "0"))
                    h_corners = int(corners[0]) if corners[0].isdigit() else 0
                    old_c = mstate.get("corners_home", 0)
                    if h_corners != old_c:
                        won = " (✅ OBIETTIVO RAGGIUNTO!)" if h_corners >= mcfg["target"] else f" (target: {mcfg['target']})"
                        msg = f"🚩 <b>Corner Italia: {h_corners}</b>{won}\nPartita: {mname}\nTotale Corner: {corners[0]} - {corners[1]}"
                        print(msg, flush=True)
                        send_telegram(msg)
                        mstate["corners_home"] = h_corners

                # Check Cartellini Belgio
                if mcfg["type"] == "cards_away":
                    cards = stats.get("Yellow cards", ("0", "0"))
                    a_cards = int(cards[1]) if cards[1].isdigit() else 0
                    old_cards = mstate.get("cards_away", 0)
                    if a_cards != old_cards:
                        won = " (✅ OBIETTIVO RAGGIUNTO!)" if a_cards >= mcfg["target"] else f" (target: {mcfg['target']})"
                        msg = f"🟨 <b>Cartellino Belgio: {a_cards}</b>{won}\nPartita: {mname}\nCartellini: {cards[0]} - {cards[1]}"
                        print(msg, flush=True)
                        send_telegram(msg)
                        mstate["cards_away"] = a_cards

                state[mid] = mstate

            save_state(state)
        except Exception as e:
            print(f"Loop error: {e}", flush=True)

        time.sleep(15)


if __name__ == "__main__":
    main()

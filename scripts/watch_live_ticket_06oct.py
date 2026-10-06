#!/usr/bin/env python3
"""
scripts/watch_live_ticket_06oct.py — Sentinella Telegram per le 3 schedine attive di stasera (Martedì 6 Ottobre 2026).
Monitora:
1. Scozia vs Slovenia (Corner Scozia, Bijol falli/carte, McGinn tiri)
2. Inghilterra vs Repubblica Ceca (Cartellini totali, Alexander-Arnold tiri)
3. Croazia vs Spagna (Tiri in porta totali, Pedri tiri, X2+MG 2-5)
4. Albania vs San Marino (Under 4.5 gol)
5. Lussemburgo vs Bulgaria (Doppia Chance X2)
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
    "S2ToNxm4": {
        "name": "Scozia vs Slovenia",
        "legs": [
            "🚩 Scozia Prima a 4 Corner (Target: 4)",
            "🟨 Bijol Quasi Cartellino (Falli/Carte)",
            "🎯 McGinn Over 0.5 Tiri Ultra"
        ]
    },
    "OvE4kA1E": {
        "name": "Inghilterra vs Repubblica Ceca",
        "legs": [
            "🟨 Over 2.5 Punti Cartellini Match (Target: 3 carte)",
            "🎯 Alexander-Arnold Over 0.5 Tiri Ultra"
        ]
    },
    "GYG5XytT": {
        "name": "Croazia vs Spagna",
        "legs": [
            "🎯 Over 8.5 Tiri in Porta Totali (Target: 9)",
            "🛡️ X2 + MultiGol 2-5",
            "🎯 Pedri Over 0.5 Tiri Ultra"
        ]
    },
    "8IQ4zY4U": {
        "name": "Albania vs San Marino",
        "legs": [
            "🥅 Under 4.5 Gol Match"
        ]
    },
    "r5r0BrlC": {
        "name": "Lussemburgo vs Bulgaria",
        "legs": [
            "🛡️ Doppia Chance: X2"
        ]
    }
}

STATE_FILE = ROOT / "data" / "live_watch_06oct_state.json"


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
                    sname = parts[1].split("¬SH÷")[0]
                    vals = parts[1].split("¬SH÷")[1].split("¬SI÷")
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
    print("[SENTINELLA LIVE 06 OTT ATTIVA] Monitoraggio 3 Schedine Nations League...")
    send_telegram("👀 <b>Sentinella BAgent Live Attiva (06 Ottobre)</b>\nMonitoraggio in tempo reale avviato per le 3 schedine in gioco!\nPartite tracciate: Scozia-Slovenia, Inghilterra-Rep. Ceca, Croazia-Spagna, Albania-San Marino, Lussemburgo-Bulgaria.")
    
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
                    legs_str = "\n".join([f"  • {l}" for l in mcfg["legs"]])
                    msg = f"⚽ <b>GOL! {mname}</b>\nNuovo punteggio: <b>{curr_score}</b> (min. {curr_period})\n🎯 Selezioni attive:\n{legs_str}"
                    print(msg, flush=True)
                    send_telegram(msg)
                    mstate["score"] = curr_score

                # 2. Rileva Intervallo
                if curr_period in ["Intervallo", "11", "HT"] and old_period not in ["Intervallo", "11", "HT"]:
                    ht_s = finfo.get("ht_score") or curr_score
                    msg = f"⏸️ <b>Fine 1° Tempo: {mname}</b>\nPunteggio all'intervallo: <b>{ht_s}</b>"
                    print(msg, flush=True)
                    send_telegram(msg)
                    mstate["period"] = curr_period

                # 3. Statistiche dettagliate
                stats = fetch_match_stats(mid)
                
                # Check Corner Scozia
                if mid == "S2ToNxm4":
                    corners = stats.get("Corner kicks", ("0", "0"))
                    h_corners = int(corners[0]) if corners[0].isdigit() else 0
                    old_c = mstate.get("corners_scotland", 0)
                    if h_corners != old_c:
                        won_c = " (✅ OBIETTIVO 4 CORNER RAGGIUNTO!)" if h_corners >= 4 else " (target: 4)"
                        msg = f"🚩 <b>Corner Scozia: {h_corners}</b>{won_c}\nPartita: {mname}\nTotale corner: {corners[0]} - {corners[1]}"
                        print(msg, flush=True)
                        send_telegram(msg)
                        mstate["corners_scotland"] = h_corners

                # Check Cartellini Inghilterra vs Rep Ceca
                if mid == "OvE4kA1E":
                    cards = stats.get("Yellow cards", ("0", "0"))
                    tot_cards = (int(cards[0]) if cards[0].isdigit() else 0) + (int(cards[1]) if cards[1].isdigit() else 0)
                    old_cards = mstate.get("tot_cards", 0)
                    if tot_cards != old_cards:
                        won_card = " (✅ OVER 2.5 CARTELLINI VINTO!)" if tot_cards >= 3 else f" (totale: {tot_cards}/3)"
                        msg = f"🟨 <b>Cartellino in Inghilterra - Rep. Ceca!</b>\nTotale cartellini: <b>{tot_cards}</b>{won_card} (Casa: {cards[0]} - Ospite: {cards[1]})"
                        print(msg, flush=True)
                        send_telegram(msg)
                        mstate["tot_cards"] = tot_cards

                # Check Tiri in Porta Croazia vs Spagna
                if mid == "GYG5XytT":
                    shots = stats.get("Shots on target", ("0", "0"))
                    tot_shots = (int(shots[0]) if shots[0].isdigit() else 0) + (int(shots[1]) if shots[1].isdigit() else 0)
                    old_shots = mstate.get("tot_shots_target", 0)
                    if tot_shots != old_shots:
                        won_s = " (✅ OVER 8.5 TIRI IN PORTA VINTO!)" if tot_shots >= 9 else f" (totale: {tot_shots}/9)"
                        msg = f"🎯 <b>Tiri in Porta: Croazia vs Spagna!</b>\nTotale tiri nello specchio: <b>{tot_shots}</b>{won_s} ({shots[0]} - {shots[1]})"
                        print(msg, flush=True)
                        send_telegram(msg)
                        mstate["tot_shots_target"] = tot_shots

                state[mid] = mstate

            save_state(state)
        except Exception as e:
            print(f"Loop error: {e}", flush=True)

        time.sleep(15)


if __name__ == "__main__":
    main()

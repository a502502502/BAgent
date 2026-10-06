#!/usr/bin/env python3
"""
scripts/live_ticket_sentinel_06ott.py — Sentinella Real-Time Telegram per la Schedina Diurna SNAI (8 Eventi).
Legge i risultati in diretta da Flashscore Mobile e invia notifiche istantanee via Telegram.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import requests
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def send_telegram(msg: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("[TELEGRAM] Token o Chat ID non configurati.", flush=True)
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=8
        )
        return r.ok
    except Exception as e:
        print(f"[TELEGRAM EXCEPTION] {e}", flush=True)
        return False


def get_all_flashscore_football() -> tuple[str, str]:
    """Scarica sia la pagina LIVE che la pagina TODAY da flashscore.mobi."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    live_txt = ""
    today_txt = ""
    try:
        r_live = requests.get("https://www.flashscore.mobi/?s=2", headers=headers, timeout=10)
        if r_live.ok:
            live_txt = r_live.text
    except Exception as e:
        print(f"[FLASH LIVE ERROR] {e}", flush=True)

    try:
        r_today = requests.get("https://www.flashscore.mobi/", headers=headers, timeout=10)
        if r_today.ok:
            today_txt = r_today.text
    except Exception as e:
        print(f"[FLASH TODAY ERROR] {e}", flush=True)

    return live_txt, today_txt


def parse_match_status(match_name: str, live_txt: str, today_txt: str) -> dict:
    combined = live_txt + "\n" + today_txt
    name_clean = match_name.replace("Sông Lam", "Song Lam").replace("City Development", "").strip()

    # Match specifico per Lam Dong
    if "lam dong" in match_name.lower():
        m = re.search(r"(\d+['\+]?)\s*Lam Dong\s*-\s*Song Lam[^0-9]*(\d+)\s*-\s*(\d+)", combined, re.IGNORECASE)
        if m:
            return {
                "status": f"{m.group(1)} (Live)",
                "score": f"{m.group(2)} - {m.group(3)}",
                "h": int(m.group(2)),
                "a": int(m.group(3)),
                "target_ok": int(m.group(3)) > int(m.group(2))
            }
        # Verifica FT o HT
        m_fin = re.search(r"Lam Dong\s*-\s*Song Lam[^0-9]*(\d+)\s*-\s*(\d+)", combined, re.IGNORECASE)
        if m_fin:
            return {
                "status": "In corso / HT",
                "score": f"{m_fin.group(1)} - {m_fin.group(2)}",
                "h": int(m_fin.group(1)),
                "a": int(m_fin.group(2)),
                "target_ok": int(m_fin.group(2)) > int(m_fin.group(1))
            }

    # Match Trencin
    if "trencin" in match_name.lower():
        m = re.search(r"(\d+['\+]?)\s*Trencin[^0-9]*-\s*Trnava[^0-9]*(\d+)\s*-\s*(\d+)", combined, re.IGNORECASE)
        if m:
            return {
                "status": f"{m.group(1)} (Live)",
                "score": f"{m.group(2)} - {m.group(3)}",
                "h": int(m.group(2)),
                "a": int(m.group(3)),
                "target_ok": int(m.group(2)) >= int(m.group(3))
            }
        m_gen = re.search(r"Trencin[^0-9]*-\s*Trnava[^0-9]*(\d+)\s*-\s*(\d+)", combined, re.IGNORECASE)
        if m_gen:
            return {
                "status": "In corso",
                "score": f"{m_gen.group(1)} - {m_gen.group(2)}",
                "h": int(m_gen.group(1)),
                "a": int(m_gen.group(2)),
                "target_ok": int(m_gen.group(1)) >= int(m_gen.group(2))
            }

    # Match Saudi Arabia
    if "saudi" in match_name.lower():
        m = re.search(r"(\d+['\+]?)\s*Saudi Arabia[^0-9]*-\s*Armenia[^0-9]*(\d+)\s*-\s*(\d+)", combined, re.IGNORECASE)
        if m:
            return {
                "status": f"{m.group(1)} (Live)",
                "score": f"{m.group(2)} - {m.group(3)}",
                "h": int(m.group(2)),
                "a": int(m.group(3)),
                "target_ok": int(m.group(2)) > int(m.group(3))
            }
        m_gen = re.search(r"Saudi Arabia[^0-9]*-\s*Armenia[^0-9]*(\d+)\s*-\s*(\d+)", combined, re.IGNORECASE)
        if m_gen:
            return {
                "status": "In corso",
                "score": f"{m_gen.group(1)} - {m_gen.group(2)}",
                "h": int(m_gen.group(1)),
                "a": int(m_gen.group(2)),
                "target_ok": int(m_gen.group(1)) > int(m_gen.group(2))
            }

    return {"status": "In attesa / Non iniziato", "score": "- - -", "target_ok": None}


def run_daemon():
    print("Avvio demone di monitoraggio Telegram...", flush=True)
    ticket_file = ROOT / "reports/tickets/ticket_giocato_06ott_8legs.json"
    with open(ticket_file, encoding="utf-8") as f:
        ticket = json.load(f)

    last_scores = {}

    while True:
        try:
            live_txt, today_txt = get_all_flashscore_football()
            updates = []

            for m in ticket["matches"]:
                m_name = m["match"]
                st = parse_match_status(m_name, live_txt, today_txt)
                sc = st.get("score")
                stat = st.get("status")

                if sc != "- - -":
                    last = last_scores.get(m_name)
                    if last != sc:
                        last_scores[m_name] = sc
                        updates.append(
                            f"<b>AGGIORNAMENTO RISULTATO</b>\n"
                            f"Incontro: <b>{m_name}</b>\n"
                            f"Punteggio: <b>{sc}</b> [{stat}]\n"
                            f"Nostro Obiettivo: {m['market']} [{m['selection']}] @ {m['odds']}\n"
                            f"Esito Attuale: {'FAVOREVOLE' if st.get('target_ok') else ('PAREGGIO' if st.get('h') == st.get('a') else 'SFORTUNATO')}"
                        )

            for upd in updates:
                send_telegram(upd)
                print(f"[NOTIFICA INVIATA] {upd[:50]}...", flush=True)

        except Exception as e:
            print(f"[DAEMON LOOP ERROR] {e}", flush=True)

        time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true")
    args = parser.parse_args()

    if args.daemon:
        run_daemon()
    else:
        print("Test singolo completato.")

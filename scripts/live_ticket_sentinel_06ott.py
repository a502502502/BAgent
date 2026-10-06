#!/usr/bin/env python3
"""
scripts/live_ticket_sentinel_06ott.py — Sentinella Real-Time Telegram per la Schedina Diurna SNAI (8 Eventi).
Legge i risultati da Flashscore Mobile distinguendo rigorosamente tra:
- FT (Terminata / Full-Time, tag a con class 'fin')
- LIVE (In corso con minuto o 'Half Time', tag a con class 'live')
- SCHED (Programmata, tag a con class 'sched')
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


def extract_flashscore_matches(html: str) -> list[dict]:
    """
    Estrae tutti i match dal container #score-data di Flashscore mobi.
    Distingue:
      - 'fin': match terminato (FT)
      - 'live': match in corso (LIVE con minuto o Half Time)
      - 'sched': match programmato
    """
    soup = BeautifulSoup(html, "html.parser")
    score_div = soup.find("div", id="score-data")
    if not score_div:
        return []

    children = list(score_div.children)
    results = []

    for i, c in enumerate(children):
        if isinstance(c, BeautifulSoup.element.NavigableString if hasattr(BeautifulSoup, "element") else str) and " - " in str(c):
            t = str(c).strip()
            # Cerca time_tag precedente
            time_tag = None
            for j in range(max(0, i - 4), i):
                if hasattr(children[j], "name") and children[j].name == "span":
                    time_tag = children[j]
            # Cerca score_tag successivo
            score_tag = None
            for j in range(i + 1, min(len(children), i + 6)):
                if hasattr(children[j], "name") and children[j].name == "a":
                    classes = children[j].get("class", [])
                    if any(cls in classes for cls in ["fin", "live", "sched"]):
                        score_tag = children[j]
                        break

            if score_tag:
                cls_list = score_tag.get("class", [])
                cls = cls_list[0] if cls_list else ""
                if cls == "fin":
                    status = "FT"
                elif cls == "live":
                    status = "LIVE"
                else:
                    status = "SCHED"

                time_val = time_tag.get_text(strip=True) if time_tag else ""
                score_val = score_tag.get_text(strip=True)

                results.append({
                    "match": t,
                    "time_info": time_val,
                    "score": score_val,
                    "status": status,
                })

    return results


def evaluate_bet_outcome(market: str, selection: str, h: int, a: int, is_ft: bool) -> tuple[bool, str]:
    """
    Valuta se l'esito della scommessa e' attualmente vincente, perdente o incassato.
    """
    m_up = market.upper()
    sel_up = selection.upper()

    if "1X2" in m_up or "ESITO FINALE" in m_up:
        if sel_up == "1":
            ok = (h > a)
        elif sel_up == "2":
            ok = (a > h)
        elif sel_up == "X":
            ok = (h == a)
        else:
            ok = False
        desc = "VINTA" if (is_ft and ok) else ("PERSA" if (is_ft and not ok) else ("IN VANTAGGIO" if ok else "IN SVANTAGGIO"))
        return ok, desc

    if "DOPPIA CHANCE" in m_up:
        if sel_up == "1X":
            ok = (h >= a)
        elif sel_up == "X2":
            ok = (a >= h)
        elif sel_up == "12":
            ok = (h != a)
        else:
            ok = False
        desc = "VINTA" if (is_ft and ok) else ("PERSA" if (is_ft and not ok) else ("IN GIOCO (OK)" if ok else "IN SVANTAGGIO"))
        return ok, desc

    if "UNDER/OVER" in m_up or "U/O" in m_up or "OVER" in m_up or "UNDER" in m_up:
        tot = h + a
        line_match = re.search(r"(\d+(?:[.,]\d+)?)", market + " " + selection)
        if line_match:
            line_val = float(line_match.group(1).replace(",", "."))
            if "OVER" in sel_up:
                ok = (tot > line_val)
                desc = "VINTA" if ok else ("PERSA" if is_ft else "IN CORSO")
                return ok, desc
            elif "UNDER" in sel_up:
                ok = (tot < line_val)
                desc = "VINTA" if (is_ft and ok) else ("PERSA" if not ok else "IN CORSO")
                return ok, desc

    return False, "SCONOSCIUTO"


def parse_ticket_matches_status(ticket_matches: list[dict], fs_matches: list[dict]) -> list[dict]:
    status_list = []
    
    # Mappe di corrispondenza nomi
    alias_map = {
        "Lam Dong - Sông Lam": ["Lam Dong", "Song Lam"],
        "AS Trencin U19 - Spartak Trnava U19": ["Trencin", "Trnava"],
        "Saudi Arabia U20 - Armenia U20": ["Saudi Arabia U20", "Armenia U20"],
        "UD Leiria U23 - Santa Clara U23": ["Leiria U23", "Santa Clara U23"],
        "Changchun Yatai - Yanbian Longding": ["Changchun Yatai", "Yanbian"],
        "Pho Hien FC - Huda Hue": ["PVF-CAND", "Hue", "Pho Hien"],
        "Binh Phuoc - CS. Dong Thap": ["Binh Phuoc", "Dong Thap", "Truong Tuoi Dong Nai"],
        "Nantong Zhiyun - Shanghai Jiading City Development": ["Nantong Zhiyun", "Ningbo", "Jiading"]
    }

    for tm in ticket_matches:
        name = tm["match"]
        keywords = alias_map.get(name, [name])
        found = None

        for fs in fs_matches:
            fs_name = fs["match"].lower()
            if any(k.lower() in fs_name for k in keywords):
                found = fs
                break

        if not found:
            status_list.append({
                "match": name,
                "status": "NON RILEVATO / PROGRAMMATO",
                "time_info": tm.get("kickoff_cest", ""),
                "score": "- - -",
                "is_ft": False,
                "outcome_desc": "IN ATTESA",
                "target_ok": None
            })
            continue

        score_str = found["score"]
        status = found["status"]
        time_info = (found.get("time_info") or "").strip()
        is_ft = (status == "FT")

        # Parsing punteggio
        score_clean = re.sub(r"\(.*?\)", "", score_str).strip()
        parts = score_clean.split("-")
        h, a = 0, 0
        has_score = (len(parts) == 2 and parts[0].strip().isdigit() and parts[1].strip().isdigit())
        if has_score:
            h = int(parts[0].strip())
            a = int(parts[1].strip())

        # Un tag live senza minuto non e' "in corso": target_ok resta vuoto e lo stato e' "punteggio senza minuto"
        has_minute = bool(re.search(r"\d+|half\s*time|ht", time_info, re.IGNORECASE))
        if status == "LIVE" and not has_minute:
            target_ok = None
            status_desc = "punteggio senza minuto"
            outcome_desc = "IN ATTESA"
        elif is_ft:
            status_desc = "TERMINATA (FT)"
            if has_score:
                target_ok, outcome_desc = evaluate_bet_outcome(tm["market"], tm["selection"], h, a, is_ft=True)
            else:
                target_ok = None
                outcome_desc = "IN ATTESA"
        elif status == "LIVE":
            status_desc = f"IN CORSO ({time_info})"
            if has_score:
                target_ok, outcome_desc = evaluate_bet_outcome(tm["market"], tm["selection"], h, a, is_ft=False)
            else:
                target_ok = None
                outcome_desc = "IN ATTESA"
        else:
            status_desc = "PROGRAMMATA"
            target_ok = None
            outcome_desc = "PROGRAMMATO"

        status_list.append({
            "match": name,
            "status": status_desc,
            "time_info": time_info,
            "score": score_str,
            "is_ft": is_ft,
            "outcome_desc": outcome_desc,
            "target_ok": target_ok,
            "h": h,
            "a": a
        })

    return status_list


def check_and_report_now():
    print("Verifica stato schedina giocata in corso...", flush=True)
    ticket_file = ROOT / "reports/tickets/ticket_giocato_06ott_8legs.json"
    with open(ticket_file, encoding="utf-8") as f:
        ticket = json.load(f)

    live_html, today_html = get_all_flashscore_football()
    fs_today = extract_flashscore_matches(today_html)
    fs_live = extract_flashscore_matches(live_html)

    # Preferisci aggiornamenti live se la partita e' in corso
    merged = {m["match"]: m for m in fs_today}
    merged.update({m["match"]: m for m in fs_live})
    fs_matches = list(merged.values())

    status_list = parse_ticket_matches_status(ticket["matches"], fs_matches)

    print("\n==========================================================================")
    print("REPORT SENTINELLA RISULTATI REALI (Shedina Diurna Utente SNAI - 8 Eventi)")
    print("==========================================================================")
    
    any_lost = False
    for i, s in enumerate(status_list, 1):
        tm = ticket["matches"][i - 1]
        print(f"Leg {i}: {s['match']}")
        print(f"  Stato: {s['status']} | Punteggio: {s['score']}")
        print(f"  Selezione giocata: {tm['market']} [{tm['selection']}] @ {tm['odds']}")
        print(f"  Esito attuale: {s['outcome_desc']}\n")
        if s["outcome_desc"] == "PERSA":
            any_lost = True

    if any_lost:
        print("[VERDETTO TICKET] Il ticket presenta eventi gia' matematicamente PERSI a tempo regolamentare.")
    else:
        print("[VERDETTO TICKET] Il ticket e' ancora in corsa.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true")
    args = parser.parse_args()

    if args.daemon:
        print("Avvio modalita demone...")
        # (Demone continuo)
    else:
        check_and_report_now()

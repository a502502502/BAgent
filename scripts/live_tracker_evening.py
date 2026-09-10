#!/usr/bin/env python3
"""
live_tracker_evening.py — Monitoraggio Live Mercoledì 9 Settembre 2026.
Focus Gare delle 21:00 per Ticket #74 (La Principale da 85.11 €) e Dembélé.
"""

from __future__ import annotations
import os
import sys
import requests
from pathlib import Path
from datetime import datetime

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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


def get_fixture_data(fid: int):
    url = f"https://{API_HOST}/fixtures?id={fid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            res = r.json().get("response", [])
            return res[0] if res else None
    except Exception as e:
        print(f"Errore API {fid}: {e}")
    return None


def run_check():
    print(f"\n=======================================================")
    print(f"📡 BAGENT LIVE RADAR 21:00 — {datetime.now().strftime('%H:%M:%S')}")
    print(f"=======================================================")

    # 1. Liverpool vs Atletico Madrid (1635686)
    liv_data = get_fixture_data(1635686)
    if liv_data:
        status = liv_data['fixture']['status']
        goals = liv_data['goals']
        events = liv_data.get('events', [])
        elapsed = status.get('elapsed', 0)
        print(f"\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 [21:00] Liverpool {goals['home']} - {goals['away']} Atletico Madrid | {status['short']} ({elapsed}')")
        tot_goals = (goals['home'] or 0) + (goals['away'] or 0)
        lead_1x = (goals['home'] or 0) >= (goals['away'] or 0)
        ok_1x_ov = lead_1x and tot_goals >= 2
        status_msg = "🟢 PRESA AL 100%!" if ok_1x_ov else f"Goals: {tot_goals}/2 | 1X: {'In controllo' if lead_1x else 'In svantaggio'}"
        print(f"   ➔ Ticket #74 (Liverpool 1X + Over 1.5 @ 1.43): {status_msg}")

    # 2. Napoli vs Arsenal (1635698)
    nap_data = get_fixture_data(1635698)
    if nap_data:
        status = nap_data['fixture']['status']
        goals = nap_data['goals']
        elapsed = status.get('elapsed', 0)
        print(f"\n🇮🇹 [21:00] Napoli {goals['home']} - {goals['away']} Arsenal | {status['short']} ({elapsed}')")
        tot_nap = (goals['home'] or 0) + (goals['away'] or 0)
        status_nap = "🟢 PRESA AL 100%!" if tot_nap >= 2 else f"Goals: {tot_nap}/2 (Mancano {2 - tot_nap} gol)"
        print(f"   ➔ Ticket #74 (Napoli vs Arsenal Over 1.5 @ 1.28): {status_nap}")

    # 3. PSG vs Slovan Bratislava (1635705)
    psg_data = get_fixture_data(1635705)
    if psg_data:
        status = psg_data['fixture']['status']
        goals = psg_data['goals']
        events = psg_data.get('events', [])
        elapsed = status.get('elapsed', 0)
        print(f"\n🇫🇷 [21:00] PSG {goals['home']} - {goals['away']} Slovan Bratislava | {status['short']} ({elapsed}')")
        dembele_event = False
        for ev in events:
            p = str(ev.get('player', {}).get('name', '')).lower()
            if "dembélé" in p or "dembele" in p:
                print(f"   • {ev.get('time', {}).get('elapsed')}' [{ev.get('type')}] {ev.get('player', {}).get('name')} ({ev.get('detail')})")
                if ev.get('type') == 'Goal':
                    dembele_event = True
        print(f"   ➔ Dembélé Focus (Maglia #10 Titolare): {'🟢 IN GOL!' if dembele_event else '⏳ In campo'}")

    print("\n" + "="*55 + "\n")


if __name__ == "__main__":
    run_check()

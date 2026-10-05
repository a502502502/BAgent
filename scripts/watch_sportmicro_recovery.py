#!/usr/bin/env python3
"""
scripts/watch_sportmicro_recovery.py — Poller automatico ogni 2 minuti.
Monitora Sportmicro per 2 ore (fino a 60 tentativi da 120s).
Termina non appena il server torna a rispondere 200 OK.
"""

from __future__ import annotations

import os
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("SPORTMICRO_API_KEY", "").strip()
LOG_FILE = ROOT / "data" / "cache" / "sportmicro" / "recovery_poll.log"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

INTERVAL_SECONDS = 120  # 2 minuti
MAX_ATTEMPTS = 60       # 60 * 2 min = 120 min (2 ore)

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "User-Agent": "BAgent-RecoveryWatcher/1.0",
}


def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def check_status() -> tuple[int, str]:
    url = "https://football.sportmicro.com/countries?limit=1"
    try:
        r = requests.get(url, headers=headers, timeout=8)
        return r.status_code, r.text[:120]
    except Exception as exc:
        return 0, str(exc)


def main() -> int:
    log("🚀 AVVIO WATCHER SPORTMICRO (intervallo: 2 min, max: 2 ore)")
    if not API_KEY:
        log("❌ ERRORE: SPORTMICRO_API_KEY mancante!")
        return 1

    for attempt in range(1, MAX_ATTEMPTS + 1):
        status, text = check_status()
        if status == 200:
            log(f"🟢 BINGO! Tentativo {attempt}/{MAX_ATTEMPTS}: Sportmicro è TORNATO ONLINE (HTTP 200)!")
            log(f"Risposta: {text}")
            return 0

        log(f"⏳ Tentativo {attempt}/{MAX_ATTEMPTS} fallito (HTTP {status}): {text}")

        if attempt < MAX_ATTEMPTS:
            time.sleep(INTERVAL_SECONDS)

    log("🛑 TIMEOUT 2 ORE RAGGIUNTO: Sportmicro non ha risposto entro 2 ore.")
    return 2


if __name__ == "__main__":
    sys.exit(main())

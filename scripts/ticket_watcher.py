#!/usr/bin/env python3
"""
BAgent Ticket Watcher
Controlla lo stato live delle selezioni di un ticket tracciato in
data/ticket_watch.json e invia un riepilogo su Telegram quando cambia
qualcosa (gol, fine primo tempo, fine partita) o quando una gamba passa
da "in corso" a "vinta"/"persa".

Pensato per girare su cron (es. ogni 10-15 minuti) sul Raspberry Pi, cosi'
segue il ticket anche a computer spento.

Uso: python3 scripts/ticket_watcher.py
"""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import requests
from services.football.external.collector import FootballExternalCollector

WATCH_FILE = ROOT / "data" / "ticket_watch.json"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")


def notify_telegram(message: str) -> None:
    if not TELEGRAM_TOKEN:
        print("(TELEGRAM_TOKEN mancante) ->")
        print(message)
        return
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "HTML"},
            timeout=10,
        )
        if not r.ok:
            print(f"Telegram errore {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"Telegram: {e}")


def load_watch() -> dict:
    return json.loads(WATCH_FILE.read_text(encoding="utf-8"))


def save_watch(data: dict) -> None:
    WATCH_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def eval_leg(market: str, goals_home: int | None, goals_away: int | None) -> str:
    """Valuta una leg 'Over X.5 Gol' / 'Under X.5 Gol' dato il punteggio attuale.
    Solo per mercati sul numero di GOL — corner/cartellini/altri mercati non
    vengono valutati automaticamente (servirebbe fixture_stats live, non
    incluso qui per restare veloce), si limita a mostrare il punteggio."""
    if goals_home is None or goals_away is None:
        return "non iniziata"
    total = goals_home + goals_away
    m = market.lower()
    if "gol" not in m and "goal" not in m:
        return f"{goals_home}-{goals_away} (mercato non-gol — corner/cartellini, controlla a mano)"
    import re
    match = re.search(r"(over|under)\s*([\d.]+)", m)
    if not match:
        return f"{goals_home}-{goals_away} (mercato non riconosciuto, controllare a mano)"
    direction, threshold = match.group(1), float(match.group(2))
    if direction == "over":
        return "✅ VINTA" if total > threshold else f"in corso ({total} gol, serve {int(threshold+0.5)-total} in piu')"
    else:
        return "❌ PERSA" if total > threshold else f"✅ in corso, regge ({total}/{int(threshold)} gol max)"


def main() -> None:
    data = load_watch()
    c = FootballExternalCollector()

    lines = [f"📊 <b>Aggiornamento {data['ticket_name']}</b>\n"]
    any_change = False

    for leg in data["legs"]:
        fx = c.fixture(leg["fixture_id"])
        resp = fx.get("response", [])
        if not resp:
            continue
        r = resp[0]
        status = r["fixture"]["status"]["short"]
        elapsed = r["fixture"]["status"]["elapsed"]
        gh, ga = r["goals"]["home"], r["goals"]["away"]
        home, away = r["teams"]["home"]["name"], r["teams"]["away"]["name"]

        state_key = f"{status}_{gh}_{ga}"
        if leg.get("last_state") != state_key:
            any_change = True
        leg["last_state"] = state_key

        verdict = eval_leg(leg["market"], gh, ga)
        score_txt = f"{gh}-{ga}" if gh is not None else "-"
        status_txt = f"{status} {elapsed}'" if elapsed else status
        lines.append(f"<b>{leg['label']}</b>")
        lines.append(f"  {home} {score_txt} {away} | {status_txt}")
        lines.append(f"  Pick: {leg['market']} @{leg['odd']} → {verdict}\n")

    lines.append(f"Quota totale: {data['total_odd']}× | Stake: {data['stake']}€")

    if any_change or data.get("force_notify"):
        notify_telegram("\n".join(lines))
        print("Aggiornamento inviato su Telegram")
        data["force_notify"] = False
    else:
        print("Nessun cambiamento, nessun invio")

    save_watch(data)


if __name__ == "__main__":
    main()

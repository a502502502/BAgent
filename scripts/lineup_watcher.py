#!/usr/bin/env python3
"""
BAgent Lineup Watcher
Controlla le formazioni delle partite tracciate in data/tracked_fixtures.json
e segnala su Telegram quando escono, evidenziando eventuali anomalie
rispetto agli infortuni/assenze noti (Regola #16 — Audit Preventivo
Integrita della Rosa).

Fonte primaria: Flashscore/LiveScore.in (services/football/external/sources/
flashscore.py) — pubblica le formazioni prima di API-Football e non e'
bloccata come Sofascore (403). Fallback su API-Football se il match non ha
un flashscore_mid tracciato o se Flashscore non ha ancora dati.

Uso: python3 scripts/lineup_watcher.py
Pensato per essere eseguito su un cron ricorrente (es. ogni 15 minuti).
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
from services.football.external.sources.flashscore import FlashscoreSource

TRACKED_FILE = ROOT / "data" / "tracked_fixtures.json"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")


def notify_telegram(message: str) -> None:
    if not TELEGRAM_TOKEN:
        print("(TELEGRAM_TOKEN mancante, salto invio) ->")
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


def load_tracked() -> list[dict]:
    if not TRACKED_FILE.exists():
        return []
    return json.loads(TRACKED_FILE.read_text(encoding="utf-8"))


def save_tracked(items: list[dict]) -> None:
    TRACKED_FILE.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")


def format_lineup_message(label: str, teams: dict, injured_names_lower: set[str], source: str) -> str:
    lines = [f"📋 <b>Formazioni uscite</b> (fonte: {source})\n{label}\n"]
    anomalies = []

    for team_idx in (1, 2):
        t = teams[team_idx]
        lines.append(f"<b>Squadra {team_idx}</b> ({len(t['starters'])} titolari)")
        for p in t["starters"]:
            base_name = p.split(" (")[0].strip()
            lines.append(f"  {p}")
            for inj_name in injured_names_lower:
                surname = inj_name.split()[-1] if " " in inj_name else inj_name
                if surname and surname in base_name.lower():
                    anomalies.append(f"⚠️ {base_name} (Squadra {team_idx}) risultava infortunato/assente ma è titolare — verificare!")
        if t.get("coach"):
            lines.append(f"  Coach: {t['coach']}")
        lines.append("")

    if anomalies:
        lines.append("🚨 <b>ANOMALIE RILEVATE</b>")
        lines.extend(anomalies)
    elif injured_names_lower:
        lines.append("✅ Nessuna anomalia rispetto agli infortuni noti.")
    else:
        lines.append("ℹ️ Nessun dato infortuni disponibile per questo campionato — impossibile verificare anomalie.")

    return "\n".join(lines)


def main() -> None:
    tracked = load_tracked()
    if not tracked:
        print("Nessuna fixture tracciata in data/tracked_fixtures.json")
        return

    c = FootballExternalCollector()
    fs = FlashscoreSource()
    changed = False

    for item in tracked:
        if item.get("notified"):
            continue

        fid = item.get("fixture_id")
        mid = item.get("flashscore_mid")
        label = item["label"]

        teams = None
        source = None

        if mid:
            fs_lineups = fs.lineups(mid)
            if fs_lineups[1]["starters"] or fs_lineups[2]["starters"]:
                teams = fs_lineups
                source = "Flashscore/LiveScore.in"

        if teams is None and fid:
            lu = c.lineups(fid)
            resp = lu.get("response", [])
            if resp:
                teams = {
                    1: {"starters": [f"{p['player']['number']} {p['player']['name']} ({p['player']['pos']})" for p in resp[0].get("startXI", [])], "subs": [], "coach": resp[0].get("coach", {}).get("name")},
                    2: {"starters": [f"{p['player']['number']} {p['player']['name']} ({p['player']['pos']})" for p in resp[1].get("startXI", [])] if len(resp) > 1 else [], "subs": [], "coach": resp[1].get("coach", {}).get("name") if len(resp) > 1 else None},
                }
                source = "API-Football"

        if teams is None:
            print(f"[{label}] formazioni non ancora disponibili (ne' Flashscore ne' API-Football)")
            continue

        injured_names_lower = set()
        if fid:
            inj = c.injuries(fid)
            injured_names_lower = {it["player"]["name"].lower() for it in inj.get("response", [])}

        msg = format_lineup_message(label, teams, injured_names_lower, source)
        notify_telegram(msg)
        print(f"[{label}] formazioni inviate su Telegram (fonte: {source})")

        item["notified"] = True
        changed = True

    if changed:
        save_tracked(tracked)


if __name__ == "__main__":
    main()

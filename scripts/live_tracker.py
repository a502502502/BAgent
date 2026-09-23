"""Monitor live calcio. Il minuto arriva dallo status API, non dall'orologio locale.

Esempio:
    python scripts/live_tracker.py --fixture 123 --fixture 456 --once
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def load_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" not in line or line.strip().startswith("#"):
            continue
        key, _, value = line.partition("=")
        if key.strip() and value.strip():
            os.environ.setdefault(key.strip(), value.strip())


def fetch_fixture(fixture_id: int, session: requests.Session | None = None) -> dict | None:
    load_env()
    api_key = os.getenv("API_FOOTBALL_KEY", "")
    if not api_key:
        raise RuntimeError("API_FOOTBALL_KEY mancante")
    client = session or requests
    response = client.get(
        "https://v3.football.api-sports.io/fixtures",
        params={"id": fixture_id},
        headers={"x-apisports-key": api_key},
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json().get("response") or []
    return payload[0] if payload else None


def format_fixture(payload: dict) -> str:
    fixture = payload["fixture"]
    teams = payload["teams"]
    goals = payload["goals"]
    status = fixture["status"]
    elapsed = status.get("elapsed")
    minute = f"{elapsed}'" if elapsed is not None else status.get("short", "?")
    home_goals = goals.get("home")
    away_goals = goals.get("away")
    score = f"{home_goals}-{away_goals}" if home_goals is not None else "vs"
    return (
        f"{teams['home']['name']} {score} {teams['away']['name']} "
        f"| {status.get('short')} ({minute}) | fixture {fixture['id']}"
    )


def poll_once(fixture_ids: list[int]) -> list[str]:
    lines = []
    for fixture_id in fixture_ids:
        payload = fetch_fixture(fixture_id)
        if payload is None:
            lines.append(f"fixture {fixture_id}: non trovato")
            continue
        lines.append(format_fixture(payload))
    return lines


def main() -> None:
    parser = argparse.ArgumentParser(description="Tracker live calcio su fixture API-Football")
    parser.add_argument("--fixture", action="append", type=int, required=True, help="ID fixture, ripetibile")
    parser.add_argument("--once", action="store_true", help="Una sola lettura, poi esce")
    parser.add_argument("--interval", type=int, default=45, help="Secondi tra un poll e il successivo")
    args = parser.parse_args()

    while True:
        for line in poll_once(args.fixture):
            print(line, flush=True)
        if args.once:
            return
        time.sleep(args.interval)


if __name__ == "__main__":
    main()

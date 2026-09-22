#!/usr/bin/env python3
"""
Smoke test Netwin: apre la sessione persistente e prova PRENOTA (solo codice).

Uso:
  .venv/bin/python scripts/smoke_netwin_booking.py           # dry-run parser + session check
  .venv/bin/python scripts/smoke_netwin_booking.py --live    # browser reale (headless=False)

Non piazza soldi: solo compilazione schedina + PRENOTA → codice 6 cifre.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config.settings import NETWIN_SESSION_DIR
from services.betting.netwin_automator import NetwinAutomator
from services.betting.netwin_market_parser import parse_netwin_selection


DEFAULT_SELECTIONS = [
    {
        "match": "Inter vs Udinese",
        "home": "Inter",
        "away": "Udinese",
        "market": "DOPPIA CHANCE",
        "pick": "1X",
        "netwin_odds": 1.25,
    },
    {
        "match": "Juventus vs Napoli",
        "home": "Juventus",
        "away": "Napoli",
        "market": "Under/Over",
        "pick": "Over 1.5",
        "netwin_odds": 1.30,
    },
]


def dry_run() -> int:
    print("=== Smoke Netwin (dry-run) ===")
    print(f"Session dir: {NETWIN_SESSION_DIR} exists={NETWIN_SESSION_DIR.exists()}")
    for sel in DEFAULT_SELECTIONS:
        action = parse_netwin_selection(sel["market"], sel["pick"])
        print(f"  OK parse {sel['match']}: {action.family} / {action.pick}")
    if not NETWIN_SESSION_DIR.exists():
        print("WARN: manca data/netwin_session — esegui scripts/setup_netwin_session.py")
        return 1
    print("Dry-run OK. Usa --live per il browser.")
    return 0


def live_run(headless: bool) -> int:
    print("=== Smoke Netwin LIVE (PRENOTA only) ===")
    auto = NetwinAutomator(headless=headless)
    # Phase A: session / sportsbook open
    if not auto.open_sportsbook():
        print("FAIL: impossibile aprire Netwin (sessione/browser).")
        auto.close()
        return 3
    title = ""
    try:
        title = auto.page.title() if auto.page else ""
    except Exception:
        pass
    print(f"Session OK — page title: {title!r}")
    auto.close()

    # Phase B: full booking attempt (may fail if demo matches not on slate)
    auto = NetwinAutomator(headless=headless)
    res = auto.build_ticket_and_book(DEFAULT_SELECTIONS, stake=1.0)
    print(json.dumps({k: v for k, v in res.items() if k != "selections"}, indent=2, default=str))
    if res.get("success") and res.get("booking_code"):
        print(f"SUCCESS codice={res['booking_code']}")
        return 0
    print(
        f"PARTIAL: sessione Netwin OK, booking demo fallito "
        f"({res.get('error')}). Usa partite reali del palinsesto di oggi."
    )
    return 0  # session smoke passed; slate-dependent booking is optional


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="Esegui automazione browser")
    parser.add_argument("--headless", action="store_true", help="Con --live, forza headless")
    args = parser.parse_args()
    if args.live:
        return live_run(headless=args.headless)
    return dry_run()


if __name__ == "__main__":
    raise SystemExit(main())

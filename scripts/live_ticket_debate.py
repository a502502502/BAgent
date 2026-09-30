#!/usr/bin/env python3
"""
Dibattito sul bus tra Cursor e Antigravity.

Cursor misura e pubblica le obiezioni. Antigravity replica. Cursor vota solo dopo
la replica, e solo CONCEDE o REPLACE cambiano una selezione.

    python scripts/live_ticket_debate.py open --title "Test Double" --legs-json ticket.json
    python scripts/live_ticket_debate.py rebut --debate-id debate_... --text "LEG 1: CONCEDE"
    python scripts/live_ticket_debate.py judge --debate-id debate_...
    python scripts/live_ticket_debate.py wait --debate-id debate_... --timeout 180
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.debate.live_exchange import LiveTicketDebate


def _print_debate(debate: dict) -> None:
    print("=" * 75)
    print(f"{debate.get('debate_id')}  [{debate.get('status')}]  {debate.get('title')}")
    print("=" * 75)
    turn = (debate.get("turns") or [])[-1]
    if turn:
        print(turn.get("content") or "")
    print("=" * 75)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dibattito live Cursor ↔ Antigravity")
    sub = parser.add_subparsers(dest="command", required=True)

    open_parser = sub.add_parser("open", help="Misura le selezioni e pubblica la critica")
    open_parser.add_argument("--title", required=True)
    open_parser.add_argument("--legs-json", required=True, help="JSON array di selezioni")
    open_parser.add_argument("--wait", action="store_true", help="Attende la replica e vota")
    open_parser.add_argument("--timeout", type=float, default=180)

    rebut_parser = sub.add_parser("rebut", help="Replica di Antigravity")
    rebut_parser.add_argument("--debate-id", required=True)
    rebut_parser.add_argument("--text", required=True)

    judge_parser = sub.add_parser("judge", help="Voto di Cursor sull'ultima replica")
    judge_parser.add_argument("--debate-id", required=True)

    wait_parser = sub.add_parser("wait", help="Attende la replica e vota")
    wait_parser.add_argument("--debate-id", required=True)
    wait_parser.add_argument("--timeout", type=float, default=180)
    wait_parser.add_argument("--interval", type=float, default=2.0)

    show_parser = sub.add_parser("show", help="Mostra lo stato del dibattito")
    show_parser.add_argument("--debate-id", required=True)

    args = parser.parse_args()
    debate = LiveTicketDebate()

    if args.command == "open":
        proposals = json.loads(Path(args.legs_json).read_text(encoding="utf-8"))
        opened = debate.open(args.title, proposals)
        _print_debate(opened)
        if args.wait:
            judged = debate.wait_rebuttal(opened["debate_id"], timeout=args.timeout)
            if judged is None:
                print("Timeout: replica non arrivata. Il dibattito resta in attesa.")
                sys.exit(1)
            _print_debate(judged)
        return

    if args.command == "rebut":
        _print_debate(debate.rebut(args.debate_id, args.text))
        return

    if args.command == "judge":
        _print_debate(debate.judge(args.debate_id))
        return

    if args.command == "wait":
        judged = debate.wait_rebuttal(args.debate_id, timeout=args.timeout, interval=args.interval)
        if judged is None:
            print("Timeout: replica non arrivata.")
            sys.exit(1)
        _print_debate(judged)
        return

    found = debate.store.get_debate(args.debate_id)
    if found is None:
        print(f"Dibattito {args.debate_id} assente.")
        sys.exit(1)
    _print_debate(found)


if __name__ == "__main__":
    main()

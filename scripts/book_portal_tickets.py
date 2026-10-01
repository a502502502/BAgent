"""Prenota su Netwin le schedine future del portale e salva il codice a 6 cifre.

Esempi:
    python scripts/book_portal_tickets.py --all
    python scripts/book_portal_tickets.py --ticket-id TICKET_TRIPLA_NATIONS_LEAGUE_01OTT --no-headless
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.netwin_automator import NetwinAutomator

FEED_PATH = ROOT / "portal" / "schedine.json"
TICKETS_DIR = ROOT / "reports" / "tickets"
DEFAULT_STAKE = 2.50


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = _parser().parse_args(argv)
    if args.codes:
        print(format_chat(collect_codes(_read_json(args.feed), args.tickets_dir, sections=("future",))))
        return 0
    if not args.all and not args.ticket_id:
        print("Indica --all oppure --ticket-id.")
        return 2
    feed = _read_json(args.feed)
    chosen = select_tickets(feed, all_future=args.all, ticket_id=args.ticket_id)
    if not chosen:
        print("Nessuna schedina futura da prenotare.")
        return 1
    booked = 0
    for ticket in chosen:
        result = book_ticket(
            ticket,
            stake=args.stake,
            tickets_dir=args.tickets_dir,
            feed_path=args.feed,
            automator_factory=lambda: NetwinAutomator(headless=args.headless),
        )
        print(result["message"])
        if result["ok"]:
            booked += 1
    print(format_chat(collect_codes(_read_json(args.feed), args.tickets_dir, only_ids=[str(row.get("id") or "") for row in chosen])))
    print(f"Prenotate {booked}/{len(chosen)}")
    return 0 if booked == len(chosen) else 1


def collect_codes(
    feed: dict,
    tickets_dir: Path,
    only_ids: list[str] | None = None,
    sections: tuple[str, ...] = ("future", "present", "past"),
) -> list[dict]:
    """Codici già salvati, pronti da incollare in chat."""
    wanted = set(only_ids or [])
    rows = []
    for section in sections:
        for ticket in feed.get(section) or []:
            if not isinstance(ticket, dict):
                continue
            ticket_id = str(ticket.get("id") or "")
            if wanted and ticket_id not in wanted:
                continue
            source = find_ticket_file(tickets_dir, ticket_id)
            stored = _read_json(source) if source is not None else {}
            code = _code(ticket.get("booking_code")) or _code(stored.get("booking_code"))
            legs = ticket.get("legs") or stored.get("legs") or []
            rows.append({
                "id": ticket_id,
                "title": str(ticket.get("title") or stored.get("name") or ticket_id),
                "code": code,
                "legs": [
                    {
                        "match": str(leg.get("match") or ""),
                        "pick": str(leg.get("pick") or leg.get("selection") or ""),
                    }
                    for leg in legs
                    if isinstance(leg, dict)
                ],
            })
    return rows


def format_chat(rows: list[dict]) -> str:
    lines = ["Codici prenotazione Netwin"]
    if not rows:
        lines.append("Nessuna schedina in elenco.")
        return "\n".join(lines)
    for row in rows:
        lines.append("")
        lines.append(f"{row['code'] or 'manca'}  {row['title']}")
        for leg in row["legs"]:
            lines.append(f"  {leg['match']} — {leg['pick']}")
    missing = sum(1 for row in rows if not row["code"])
    lines.append("")
    lines.append(f"{len(rows) - missing} codici su {len(rows)} schedine")
    return "\n".join(lines)


def select_tickets(feed: dict, *, all_future: bool, ticket_id: str) -> list[dict]:
    future = [row for row in feed.get("future") or [] if isinstance(row, dict)]
    if ticket_id:
        return [row for row in future if str(row.get("id") or "") == ticket_id]
    if all_future:
        return future
    return []


def book_ticket(
    ticket: dict,
    *,
    stake: float | None,
    tickets_dir: Path,
    feed_path: Path,
    automator_factory,
) -> dict:
    ticket_id = str(ticket.get("id") or "")
    existing = _code(ticket.get("booking_code"))
    if existing:
        return {"ok": True, "code": existing, "message": f"{ticket_id} già prenotata: {existing}"}
    source = find_ticket_file(tickets_dir, ticket_id)
    payload = _read_json(source) if source is not None else {}
    if not payload:
        payload = ticket
    selections = selections_from(payload if payload.get("legs") else ticket)
    if not selections:
        return {"ok": False, "code": None, "message": f"{ticket_id}: nessuna selezione"}
    amount = stake if stake is not None else stake_of(payload)
    automator = automator_factory()
    result = automator.build_ticket_and_book(selections, stake=amount, receipt_id=ticket_id)
    code = _code(result.get("booking_code"))
    if not result.get("success") or code is None:
        error = result.get("error") or "codice non generato"
        return {"ok": False, "code": None, "message": f"{ticket_id}: {error}"}
    if source is not None:
        _write_code(source, code)
    _write_feed_code(feed_path, ticket_id, code)
    shot = result.get("screenshot") or ""
    return {"ok": True, "code": code, "message": f"{ticket_id}: codice {code} {shot}".strip()}


def find_ticket_file(tickets_dir: Path, ticket_id: str) -> Path | None:
    if not ticket_id or not tickets_dir.exists():
        return None
    direct = tickets_dir / f"{ticket_id.lower()}.json"
    if direct.exists():
        return direct
    for path in sorted(tickets_dir.glob("*.json")):
        payload = _read_json(path)
        if str(payload.get("ticket_id") or "") == ticket_id:
            return path
    return None


def selections_from(payload: dict) -> list[dict]:
    rows = []
    for leg in payload.get("legs") or []:
        if not isinstance(leg, dict):
            continue
        match = str(leg.get("match") or "")
        pick = str(leg.get("pick") or leg.get("selection") or "")
        if not match or not pick:
            continue
        odd = leg.get("netwin_odds") or leg.get("odd") or leg.get("odds")
        try:
            odd_value = float(str(odd).replace("€", "").strip())
        except (TypeError, ValueError):
            odd_value = None
        rows.append({
            "match": match,
            "home": match.split(" vs ")[0].strip(),
            "market": str(leg.get("market") or ""),
            "pick": pick,
            "netwin_odds": odd_value,
        })
    return rows


def stake_of(payload: dict) -> float:
    raw = payload.get("stake") or payload.get("stake_eur")
    if isinstance(raw, str):
        raw = raw.replace("€", "").strip()
    try:
        amount = float(raw)
    except (TypeError, ValueError):
        return DEFAULT_STAKE
    return amount if amount > 0 else DEFAULT_STAKE


def _write_code(path: Path, code: str) -> None:
    payload = _read_json(path)
    payload["booking_code"] = code
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=4) + "\n", encoding="utf-8")


def _write_feed_code(path: Path, ticket_id: str, code: str) -> None:
    payload = _read_json(path)
    for section in ("future", "present", "past"):
        for row in payload.get(section) or []:
            if isinstance(row, dict) and str(row.get("id") or "") == ticket_id:
                row["booking_code"] = code
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _code(value: object) -> str | None:
    text = str(value or "").strip()
    if len(text) == 6 and text.isdigit():
        return text
    return None


def _read_json(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Prenota le schedine future su Netwin")
    parser.add_argument("--codes", action="store_true", help="Stampa in chat i codici già salvati, senza aprire Netwin")
    parser.add_argument("--all", action="store_true", help="Tutte le schedine nella sezione future")
    parser.add_argument("--ticket-id", default="", help="Una sola schedina, per id")
    parser.add_argument("--headless", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--stake", type=float, default=None, help="Importo nel carrello. Default: stake del ticket o 2.50")
    parser.add_argument("--feed", type=Path, default=FEED_PATH)
    parser.add_argument("--tickets-dir", type=Path, default=TICKETS_DIR)
    return parser


if __name__ == "__main__":
    raise SystemExit(main())

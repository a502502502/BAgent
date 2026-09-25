"""Motore della richiesta schedina. La pagina pubblica gli manda la data e le squadre.

La chiave FootyStats resta nell'ambiente. Non viene mai rimandata al browser.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.portal.slip_advisor import advise_records, context_from_flags, records_from_feed, rows_on_date

load_dotenv(ROOT / ".env")
PORT = 8765
ROME = ZoneInfo("Europe/Rome")


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self) -> None:
        self._send(204, b"")

    def do_POST(self) -> None:
        if self.path.split("?", 1)[0] != "/api/schedina":
            self._send(404, {"message": "Percorso assente"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > 20_000:
            self._send(400, {"message": "Richiesta troppo lunga"})
            return
        try:
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._send(400, {"message": "Richiesta non leggibile"})
            return
        date = str(payload.get("date") or "")
        if len(date) != 10 or date[4] != "-" or date[7] != "-":
            self._send(400, {"message": "Data non valida"})
            return
        try:
            rows, leagues = _feed(date)
        except requests.RequestException:
            self._send(502, {"message": "FootyStats non raggiungibile"})
            return
        result = advise_records(
            records_from_feed(rows, leagues),
            datetime.now(ROME),
            context_from_flags(payload.get("flags")),
            str(payload.get("query") or "")[:500],
        )
        self._send(200, result)

    def log_message(self, fmt: str, *args) -> None:
        return

    def _send(self, status: int, body: dict | bytes) -> None:
        raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


def _feed(date: str) -> tuple[list[dict], dict[int, str]]:
    key = os.getenv("FOOTYSTATS_API_KEY", "")
    if not key:
        raise requests.RequestException("chiave assente")
    matches = requests.get(
        "https://api.football-data-api.com/todays-matches",
        params={"key": key, "date": date},
        timeout=25,
    )
    matches.raise_for_status()
    leagues = requests.get(
        "https://api.football-data-api.com/league-list",
        params={"key": key},
        timeout=40,
    )
    leagues.raise_for_status()
    catalog = leagues.json().get("data") or []
    names: dict[int, str] = {}
    nations_id = None
    for item in catalog:
        label = f"{item.get('country') or ''} | {item.get('name') or item.get('league_name') or ''}"
        title = f"{item.get('name') or ''} {item.get('league_name') or ''}".lower()
        seasons = item.get("season") or []
        if "uefa nations league" in title and "women" not in title and seasons:
            nations_id = int(seasons[-1]["id"])
        for season in seasons:
            season_id = season.get("id")
            if season_id is not None:
                names[int(season_id)] = label.strip(" |")
    rows = matches.json().get("data") or []
    if nations_id:
        extra = requests.get(
            "https://api.football-data-api.com/league-matches",
            params={"key": key, "league_id": nations_id},
            timeout=40,
        )
        extra.raise_for_status()
        known = {row.get("id") for row in rows}
        names[nations_id] = names.get(nations_id) or "International UEFA Nations League"
        for row in rows_on_date(extra.json().get("data") or [], date):
            if row.get("id") in known:
                continue
            copied = dict(row)
            copied["competition_id"] = nations_id
            rows.append(copied)
    return rows, names


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(f"Motore schedina su http://127.0.0.1:{PORT}/api/schedina", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()

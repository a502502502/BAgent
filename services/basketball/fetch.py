"""Box score NBA da Basketball-Reference. Solo regular season, solo gare in casa.

Ogni riga casalinga contiene anche il box score dell'ospite, quindi una partita
entra una volta sola. Le sigle CHO/BRK/PHO diventano CHA/BKN/PHX.
"""

from __future__ import annotations

import csv
import re
import time
from datetime import date, datetime
from pathlib import Path

import requests

from services.basketball.gamelog import TeamBox, pair_team_boxes

TEAMS = (
    "ATL", "BOS", "BRK", "CHO", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
    "OKC", "ORL", "PHI", "PHO", "POR", "SAC", "SAS", "TOR", "UTA", "WAS",
)
CANONICAL = {"BRK": "BKN", "CHO": "CHA", "PHO": "PHX"}
BOX_FIELDS = [
    "game_id",
    "date",
    "season",
    "team",
    "is_home",
    "points",
    "fga",
    "fta",
    "oreb",
    "tov",
]
_CELL = re.compile(r'data-stat="([^"]+)"[^>]*>([\s\S]*?)</t[dh]>', re.I)
_GAME_ID = re.compile(r"/boxscores/([^./]+)\.html")
_TAG = re.compile(r"<[^>]+>")


def fetch_team_boxes(
    season: str,
    teams: tuple[str, ...] | list[str] | None = None,
    pause_seconds: float = 1.5,
    timeout: float = 20.0,
) -> list[TeamBox]:
    """`season` nel formato `2024-25`. L'anno sul sito è quello di chiusura, 2025."""
    year = int(season.split("-")[0]) + 1
    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})
    selected = tuple(teams) if teams is not None else TEAMS
    boxes: list[TeamBox] = []
    for index, team in enumerate(selected):
        url = f"https://www.basketball-reference.com/teams/{team}/{year}/gamelog/"
        html = _get(session, url, timeout)
        boxes.extend(parse_home_games(html, season, team))
        if pause_seconds and index < len(selected) - 1:
            time.sleep(pause_seconds)
    return boxes


def parse_home_games(html: str, season: str, team: str) -> list[TeamBox]:
    table = _regular_season_table(html)
    boxes: list[TeamBox] = []
    for row in re.findall(r"<tr[\s\S]*?</tr>", table):
        cells = {name: _text(value) for name, value in _CELL.findall(row)}
        if cells.get("game_location") == "@" or not cells.get("fga") or not cells.get("opp_fga"):
            continue
        game_date = _parse_date(cells.get("date", ""))
        if game_date is None:
            continue
        game_id_match = _GAME_ID.search(row)
        game_id = game_id_match.group(1) if game_id_match else f"{game_date.isoformat()}-{team}"
        home = _canonical(team)
        away = _canonical(cells["opp_name_abbr"])
        boxes.append(_box(game_id, game_date, season, home, True, cells, ""))
        boxes.append(_box(game_id, game_date, season, away, False, cells, "opp_"))
    return boxes


def write_team_boxes(boxes: list[TeamBox], path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=BOX_FIELDS)
        writer.writeheader()
        for box in boxes:
            writer.writerow(
                {
                    "game_id": box.game_id,
                    "date": box.game_date.isoformat(),
                    "season": box.season,
                    "team": box.team,
                    "is_home": int(box.is_home),
                    "points": box.points,
                    "fga": box.fga,
                    "fta": box.fta,
                    "oreb": box.oreb,
                    "tov": box.tov,
                }
            )
    return len(pair_team_boxes(boxes))


def _box(game_id: str, game_date: date, season: str, team: str, is_home: bool, cells: dict, prefix: str) -> TeamBox:
    points_key = "team_game_score" if is_home else "opp_team_game_score"
    return TeamBox(
        game_id=game_id,
        game_date=game_date,
        season=season,
        team=team,
        is_home=is_home,
        points=int(cells[points_key]),
        fga=float(cells[f"{prefix}fga"]),
        fta=float(cells[f"{prefix}fta"]),
        oreb=float(cells[f"{prefix}orb"]),
        tov=float(cells[f"{prefix}tov"]),
    )


def _regular_season_table(html: str) -> str:
    match = re.search(r'<table[^>]*id="team_game_log"[\s\S]*?</table>', html, re.I)
    if match:
        return match.group(0)
    return html


def _canonical(team: str) -> str:
    code = team.strip().upper()
    return CANONICAL.get(code, code)


def _text(value: str) -> str:
    return _TAG.sub("", value).strip()


def _parse_date(value: str) -> date | None:
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _get(session: requests.Session, url: str, timeout: float) -> str:
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            response = session.get(url, timeout=(8, timeout))
            if response.status_code == 429:
                last_error = requests.HTTPError(f"429 Too Many Requests: {url}")
                time.sleep(20)
                continue
            response.raise_for_status()
            return response.text
        except requests.RequestException as error:
            last_error = error
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(
        f"Basketball-Reference ha rifiutato {url}. "
        "Le squadre gia' salvate restano nel CSV: rilancia lo stesso comando piu' tardi."
    ) from last_error

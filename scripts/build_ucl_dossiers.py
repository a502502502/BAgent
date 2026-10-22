#!/usr/bin/env python3
"""Schede partita per la Champions League del 21 ottobre 2026.

Legge i nove incontri in data/netwin_live_odds.json e i tabellini in data/bagent.db.
La pagina è una tabella di frequenze (le più alte in evidenza), il dettaglio
degli ultimi incontri e i totali individuali 2026/2027 già salvati in players.
Non propone una selezione e non calcola un edge.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "bagent.db"
ODDS_PATH = ROOT / "data" / "netwin_live_odds.json"
OUT_PATH = ROOT / "portal" / "ucl_21ott_2026.html"

SKIP_STATUS = {"NS", "incomplete", "canceled", "suspended", "PST"}
HIGH = 0.75
MID = 0.60

# Nome Netwin -> nomi esatti in bagent.db. Il collegamento è scritto in pagina.
LINKS = {
    "Aston Villa": (["Aston Villa"], "Aston Villa"),
    "Viking Fk": (["Viking"], "Viking"),
    "Real Betis": (["Real Betis"], "Real Betis"),
    "Feyenoord": (["Feyenoord"], "Feyenoord"),
    "Real Madrid": (["Real Madrid"], "Real Madrid"),
    "Lipsia": (["RB Leipzig"], "RB Leipzig"),
    "Sporting": (["Sporting CP"], "Sporting CP"),
    "Lask Linz": (["LASK Linz", "Lask Linz"], "LASK Linz"),
    "Como": (["Como"], "Como"),
    "Manchester United": (["Manchester United"], "Manchester United"),
    "Club Brugge": (["Club Brugge"], "Club Brugge"),
    "Lens": (["Lens"], "Lens"),
    "Inter": (["Inter"], "Inter"),
    "Shakhtar Donetsk": (["Shakhtar Donetsk"], "Shakhtar Donetsk"),
    "Lilla": (["Lille"], "Lille"),
    "Galatasaray": (["Galatasaray"], "Galatasaray"),
    "Bayern Monaco": (["Bayern Monaco"], "Bayern Monaco"),
    "Arsenal": (["Arsenal"], "Arsenal"),
}

SAMPLE = 8
SEASON = "2026/2027"

# Nome Netwin -> (club, campionato) in players. Il primo candidato con righe vince.
# Viking, Club Brugge, Shakhtar e LASK non sono in questo feed.
PLAYER_CLUBS: dict[str, list[tuple[str, str]]] = {
    "Como": [("Como", "Serie A")],
    "Manchester United": [("Manchester United", "Premier League")],
    "Lilla": [("Lille", "Ligue 1")],
    "Galatasaray": [("Galatasaray", "Super Lig")],
    "Aston Villa": [("Aston Villa", "Premier League")],
    "Viking Fk": [],
    "Bayern Monaco": [("Bayern München", "Bundesliga"), ("Bayern Munich", "Bundesliga")],
    "Arsenal": [("Arsenal", "Premier League")],
    "Club Brugge": [],
    "Lens": [("Lens", "Ligue 1")],
    "Inter": [("Inter Milan", "Serie A")],
    "Shakhtar Donetsk": [],
    "Real Betis": [("Real Betis", "La Liga")],
    "Feyenoord": [("Feyenoord", "Eredivisie")],
    "Real Madrid": [("Real Madrid", "La Liga")],
    "Lipsia": [("RB Leipzig", "Bundesliga")],
    "Sporting": [("Sporting CP", "Primeira Liga")],
    "Lask Linz": [],
}

ROLES = {
    "Forward": "Attacco",
    "Midfielder": "Centrocampo",
    "Defender": "Difesa",
    "Goalkeeper": "Portiere",
}

COLUMNS = (
    "id", "league", "status", "date_gmt", "match_date", "timestamp",
    "home_team", "away_team", "home_goals", "away_goals",
    "home_goals_ht", "away_goals_ht", "ht_home_goals", "ht_away_goals",
    "home_shots", "away_shots", "home_corners", "away_corners",
    "home_xg", "away_xg", "home_sot", "away_sot",
    "home_shots_on_target", "away_shots_on_target",
)


def esc(value) -> str:
    return html.escape(str(value), quote=True)


def kickoff_label(raw: str) -> str:
    text = raw.strip()
    if len(text) >= 15 and text[:8].isdigit():
        return f"{text[6:8]}/{text[4:6]}/{text[0:4]} ore {text[9:14]} CEST"
    return text


def kickoff_clock(raw: str) -> str:
    text = raw.strip()
    if len(text) >= 14 and text[:8].isdigit():
        return f"{text[6:8]}/{text[4:6]}/{text[0:4]} {text[9:14]}"
    return text


def pct(rate: float) -> str:
    return f"{round(rate * 100):.0f}%"


def pretty_date(iso: str) -> str:
    if len(iso) >= 10 and iso[4] == "-" and iso[7] == "-":
        return f"{iso[8:10]}/{iso[5:7]}/{iso[0:4]}"
    return iso


def band(rate: float | None) -> str:
    if rate is None:
        return ""
    if rate >= HIGH:
        return "hi"
    if rate >= MID:
        return "mid"
    return ""


def load_odds() -> tuple[str, list[dict]]:
    payload = json.loads(ODDS_PATH.read_text(encoding="utf-8"))
    rows = [
        match for match in payload["matches"]
        if str(match.get("kickoff", "")).startswith("20261021")
        and "champ" in (match.get("tournament") or "").lower()
    ]
    rows.sort(key=lambda match: (match["kickoff"], match["match_name"]))
    return payload.get("timestamp") or "", rows


def first_value(*values):
    for value in values:
        if value is not None:
            return value
    return None


def as_count(value):
    if value is None:
        return None
    number = float(value)
    if number < 0:
        return None
    if number.is_integer():
        return int(number)
    return number


def iso_date(row: dict) -> str:
    match_date = row.get("match_date")
    if isinstance(match_date, str):
        text = match_date.strip()
        if len(text) >= 10 and text[4] == "-" and text[7] == "-":
            return text[:10]
    raw = (row.get("date_gmt") or "").strip()
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%b %d %Y - %I:%M%p", "%d/%m/%Y"):
        if not raw:
            break
        try:
            return datetime.strptime(raw, fmt).date().isoformat()
        except ValueError:
            continue
    stamp = row.get("timestamp")
    if stamp:
        try:
            return datetime.fromtimestamp(int(stamp), timezone.utc).date().isoformat()
        except (OSError, OverflowError, ValueError):
            return ""
    return ""


def load_played(conn: sqlite3.Connection, names: list[str]) -> list[dict]:
    marks = ",".join("?" for _ in names)
    status_marks = ",".join("?" for _ in SKIP_STATUS)
    query = f"""
        SELECT {", ".join(COLUMNS)}
        FROM matches
        WHERE (home_team IN ({marks}) OR away_team IN ({marks}))
          AND home_goals IS NOT NULL AND away_goals IS NOT NULL
          AND COALESCE(status, 'FT') NOT IN ({status_marks})
    """
    found = []
    for rec in conn.execute(query, (*names, *names, *SKIP_STATUS)):
        raw = dict(zip(COLUMNS, rec))
        found.append({
            "id": raw["id"],
            "league": raw["league"] or "",
            "status": raw["status"],
            "date_gmt": raw["date_gmt"],
            "match_date": raw["match_date"],
            "timestamp": raw["timestamp"],
            "home": raw["home_team"],
            "away": raw["away_team"],
            "hg": raw["home_goals"],
            "ag": raw["away_goals"],
            "hth": as_count(first_value(raw["home_goals_ht"], raw["ht_home_goals"])),
            "hta": as_count(first_value(raw["away_goals_ht"], raw["ht_away_goals"])),
            "hs": raw["home_shots"],
            "aws": raw["away_shots"],
            "hc": raw["home_corners"],
            "ac": raw["away_corners"],
            "hx": raw["home_xg"],
            "ax": raw["away_xg"],
            "hso": as_count(first_value(raw["home_sot"], raw["home_shots_on_target"])),
            "aso": as_count(first_value(raw["away_sot"], raw["away_shots_on_target"])),
        })
    return collapse(found)


def useful_number(value, negative_ok: bool = False) -> bool:
    if value is None:
        return False
    if not negative_ok and value < 0:
        return False
    return True


def richness(row: dict) -> tuple:
    shots = useful_number(row["hs"]) and useful_number(row["aws"]) and row["hs"] > 0 and row["aws"] > 0
    corners = useful_number(row["hc"]) and useful_number(row["ac"])
    xg = row["hx"] is not None and row["ax"] is not None and (row["hx"] > 0 or row["ax"] > 0 or shots)
    ht = row["hth"] is not None and row["hta"] is not None
    sot = row["hso"] is not None and row["aso"] is not None
    return (int(shots), int(corners), int(xg), int(ht), int(sot), int(bool(iso_date(row))), row["id"])


def canon_team(name: str) -> str:
    text = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    tokens = re.sub(r"[^a-z0-9]+", " ", text.lower()).split()
    tokens = [token for token in tokens if token not in {"as", "fc", "ac", "afc", "cf", "club"}]
    return " ".join(tokens) or (name or "").casefold()


def collapse(rows: list[dict]) -> list[dict]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for row in rows:
        groups[(canon_team(row["home"]), canon_team(row["away"]), row["hg"], row["ag"])].append(row)
    kept = []
    for items in groups.values():
        merged = dict(max(items, key=richness))
        for other in items:
            if not iso_date(merged) and iso_date(other):
                merged["match_date"] = other.get("match_date")
                merged["date_gmt"] = other.get("date_gmt")
                merged["timestamp"] = other.get("timestamp")
            for field in ("hth", "hta", "hx", "ax", "hso", "aso"):
                if merged.get(field) is None and other.get(field) is not None and other.get(field) >= 0:
                    merged[field] = other[field]
            for field in ("hs", "aws", "hc", "ac"):
                if not useful_number(merged.get(field)) and useful_number(other.get(field)):
                    merged[field] = other[field]
            if not merged.get("league") and other.get("league"):
                merged["league"] = other["league"]
        merged["iso"] = iso_date(merged)
        kept.append(merged)
    kept.sort(key=lambda row: (bool(row["iso"]), row["iso"], row["id"]), reverse=True)
    return kept


def shot_pair(row: dict) -> tuple[int, int] | None:
    if useful_number(row["hs"]) and useful_number(row["aws"]) and row["hs"] > 0 and row["aws"] > 0:
        return (row["hs"], row["aws"])
    return None


def corner_pair(row: dict) -> tuple[int, int] | None:
    if useful_number(row["hc"]) and useful_number(row["ac"]):
        return (row["hc"], row["ac"])
    return None


def sot_pair(row: dict) -> tuple[int, int] | None:
    if row["hso"] is None or row["aso"] is None:
        return None
    if row["hso"] == 0 and row["aso"] == 0 and shot_pair(row) is None:
        return None
    return (row["hso"], row["aso"])


def repeated(rows: list[dict], pair) -> bool:
    values = [pair(row) for row in rows]
    values = [value for value in values if value is not None]
    return len(values) >= 4 and len(set(values)) == 1


def view(row: dict, names: set[str]) -> dict:
    is_home = row["home"] in names
    pair_shots = shot_pair(row)
    pair_corners = corner_pair(row)
    pair_sot = sot_pair(row)
    xg_for = row["hx"] if is_home else row["ax"]
    xg_against = row["ax"] if is_home else row["hx"]
    xg_ok = row["hx"] is not None and row["ax"] is not None and (row["hx"] > 0 or row["ax"] > 0 or pair_shots)
    ht_for = ht_against = None
    if row["hth"] is not None and row["hta"] is not None:
        ht_for = row["hth"] if is_home else row["hta"]
        ht_against = row["hta"] if is_home else row["hth"]
    sot_for = sot_against = None
    if pair_sot:
        sot_for = row["hso"] if is_home else row["aso"]
        sot_against = row["aso"] if is_home else row["hso"]
    gf = row["hg"] if is_home else row["ag"]
    ga = row["ag"] if is_home else row["hg"]
    return {
        "venue": "Casa" if is_home else "Trasferta",
        "opponent": row["away"] if is_home else row["home"],
        "home": row["home"],
        "away": row["away"],
        "hg": row["hg"],
        "ag": row["ag"],
        "gf": gf,
        "ga": ga,
        "league": row["league"],
        "iso": row.get("iso") or "",
        "date_label": pretty_date(row.get("iso") or "") or "—",
        "board": f"{row['home']} {row['hg']}-{row['ag']} {row['away']}",
        "result": f"{gf}-{ga}",
        "ht_line": f"{ht_for}-{ht_against}" if ht_for is not None else "",
        "ht_total": (ht_for + ht_against) if ht_for is not None else None,
        "shots_line": f"{(row['hs'] if is_home else row['aws'])}-{(row['aws'] if is_home else row['hs'])}" if pair_shots else "",
        "corners_line": f"{(row['hc'] if is_home else row['ac'])}-{(row['ac'] if is_home else row['hc'])}" if pair_corners else "",
        "xg_line": f"{xg_for:.2f}-{xg_against:.2f}" if xg_ok else "",
        "sot_line": f"{sot_for}-{sot_against}" if sot_for is not None else "",
        "sf": (row["hs"] if is_home else row["aws"]) if pair_shots else None,
        "sa": (row["aws"] if is_home else row["hs"]) if pair_shots else None,
        "cf": (row["hc"] if is_home else row["ac"]) if pair_corners else None,
        "ca": (row["ac"] if is_home else row["hc"]) if pair_corners else None,
        "sof": sot_for,
        "soa": sot_against,
        "xf": xg_for if xg_ok else None,
        "xa": xg_against if xg_ok else None,
    }


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def fmt_mean(values: list[float], digits: int, total: int | None = None) -> str:
    value = mean(values)
    if value is None:
        return "—"
    text = f"{value:.{digits}f}"
    if total is not None and len(values) != total:
        text += f" · su {len(values)}"
    return text


def freq(matches: list[dict], test) -> tuple[float | None, str]:
    if not matches:
        return None, "assente"
    hit = sum(1 for match in matches if test(match))
    return hit / len(matches), f"{hit}/{len(matches)}"


def none_pair() -> tuple[float | None, str]:
    return None, "—"


def build_side(conn: sqlite3.Connection, netwin_name: str) -> dict:
    db_names, canonical = LINKS[netwin_name]
    played = load_played(conn, db_names)
    names = set(db_names)
    shots_repeated = repeated(played, shot_pair)
    corners_repeated = repeated(played, corner_pair)
    sot_repeated = repeated(played, sot_pair)
    sample = [view(row, names) for row in played[:SAMPLE]]
    if shots_repeated:
        for match in sample:
            match["shots_line"] = ""
            match["sf"] = None
            match["sa"] = None
    if corners_repeated:
        for match in sample:
            match["corners_line"] = ""
            match["cf"] = None
            match["ca"] = None
    if sot_repeated:
        for match in sample:
            match["sot_line"] = ""
            match["sof"] = None
            match["soa"] = None
    shot_rows = [match for match in sample if match["sf"] is not None]
    corner_rows = [match for match in sample if match["cf"] is not None]
    xg_rows = [match for match in sample if match["xf"] is not None]
    sot_rows = [match for match in sample if match["sof"] is not None]
    home_rows = [match for match in sample if match["venue"] == "Casa"]
    away_rows = [match for match in sample if match["venue"] == "Trasferta"]
    notes = []
    if netwin_name != canonical:
        notes.append(f"Nome Netwin «{netwin_name}» agganciato a «{canonical}».")
    if len(played) > len(sample):
        notes.append(f"Ultime {len(sample)} partite distinte, su {len(played)} disponibili.")
    if shots_repeated:
        notes.append("Tiri identici su tutte le righe: colonna esclusa.")
    elif shot_rows and len(shot_rows) != len(sample):
        notes.append(f"Tiri presenti su {len(shot_rows)} delle {len(sample)} partite.")
    elif not shot_rows:
        notes.append("Tiri assenti su queste righe.")
    if corners_repeated:
        notes.append("Corner identici su tutte le righe: colonna esclusa.")
    if sot_repeated:
        notes.append("Tiri in porta identici su tutte le righe: colonna esclusa.")
    if not xg_rows:
        notes.append("xG assente su queste righe.")
    dated = sum(1 for match in sample if match["iso"])
    if sample and dated == 0:
        notes.append("Data assente su queste righe.")
    elif dated and dated != len(sample):
        notes.append(f"Data presente su {dated} delle {len(sample)} partite.")
    if len(sample) < 4:
        notes.append("Campione corto.")
    squad = load_squad(conn, netwin_name)
    return {
        "netwin": netwin_name,
        "canonical": canonical,
        "matches": sample,
        "shot_rows": shot_rows,
        "corner_rows": corner_rows,
        "xg_rows": xg_rows,
        "sot_rows": sot_rows,
        "home_rows": home_rows,
        "away_rows": away_rows,
        "available": len(played),
        "notes": notes,
        "squad": squad,
    }


def load_squad(conn: sqlite3.Connection, netwin_name: str) -> dict:
    options = list(PLAYER_CLUBS.get(netwin_name, []))
    if netwin_name == "Bayern Monaco":
        for (name,) in conn.execute(
            """
            SELECT DISTINCT current_club FROM players
            WHERE season=? AND league='Bundesliga' AND current_club LIKE 'Bayern %'
            """,
            (SEASON,),
        ):
            if (name, "Bundesliga") not in options:
                options.append((name, "Bundesliga"))
    club = ""
    league = ""
    fetched: list[tuple] = []
    for candidate, candidate_league in options:
        rows = conn.execute(
            """
            SELECT p.full_name,
                   COALESCE(NULLIF(r.display_name, ''), p.full_name),
                   p.position, p.appearances, p.minutes_played,
                   p.goals, p.assists, p.yellow_cards, p.red_cards,
                   r.team_name
            FROM players p
            LEFT JOIN player_registry_2026 r ON r.canonical_name = p.full_name
            WHERE p.current_club=? AND p.league=? AND p.season=?
              AND NOT EXISTS (
                  SELECT 1 FROM departed_players_blacklist d
                  WHERE lower(d.player_name) = lower(p.full_name)
                    AND lower(d.former_club) = lower(p.current_club)
              )
            """,
            (candidate, candidate_league, SEASON),
        ).fetchall()
        if rows:
            club, league, fetched = candidate, candidate_league, rows
            break
    players = []
    for row in fetched:
        registry_team = row[9]
        if registry_team and registry_team != club:
            continue
        minutes = int(row[4] or 0)
        goals = int(row[5] or 0)
        players.append({
            "name": row[1] or row[0],
            "role": ROLES.get(row[2] or "", row[2] or "—"),
            "apps": int(row[3] or 0),
            "minutes": minutes,
            "goals": goals,
            "assists": int(row[6] or 0),
            "yellow": int(row[7] or 0),
            "red": int(row[8] or 0),
            "g90": (goals * 90 / minutes) if minutes >= 90 and goals else None,
        })
    players.sort(key=lambda item: (item["goals"], item["yellow"], item["assists"], item["red"], item["apps"]), reverse=True)
    shown = [item for item in players if item["goals"] or item["assists"] or item["yellow"] or item["red"]]
    return {
        "club": club,
        "league": league,
        "squad": len(players),
        "shown": shown,
        "goals": sum(item["goals"] for item in players),
        "assists": sum(item["assists"] for item in players),
        "yellow": sum(item["yellow"] for item in players),
        "red": sum(item["red"] for item in players),
    }


def result_letter(match: dict) -> str:
    if match["gf"] > match["ga"]:
        return "V"
    if match["gf"] == match["ga"]:
        return "P"
    return "S"


def money(value) -> str:
    if value is None:
        return ""
    return f"{float(value):.2f}"


def max_rate(row: dict) -> float:
    rates = [rate for rate in (row["home_rate"], row["away_rate"]) if rate is not None]
    return max(rates) if rates else -1.0


def min_rate(row: dict) -> float:
    rates = [rate for rate in (row["home_rate"], row["away_rate"]) if rate is not None]
    return min(rates) if rates else -1.0


def mean_rate(row: dict) -> float:
    rates = [rate for rate in (row["home_rate"], row["away_rate"]) if rate is not None]
    if not rates:
        return -1.0
    return sum(rates) / len(rates)


def frequency_rows(markets: dict, home: dict, away: dict) -> list[dict]:
    under_over = markets.get("UNDER_OVER") or {}
    primo = markets.get("PRIMO_TEMPO") or {}
    mix = markets.get("CHANCE_MIX") or {}
    multi = markets.get("MULTIGOL") or {}
    combo = markets.get("COMBO") or {}
    squad = markets.get("MULTIGOL_SQUADRA") or {}
    gg = markets.get("GOL_NOGOL") or {}

    def over_under(line: str, side: str) -> str:
        return money((under_over.get(line) or {}).get(side))

    def find_primo(fragment: str) -> str:
        for key, value in primo.items():
            if fragment in key:
                return money(value)
        return ""

    def ht_freq(side: dict, test) -> tuple[float | None, str]:
        rows = [match for match in side["matches"] if match["ht_total"] is not None]
        if not rows:
            return None, ""
        hit = sum(1 for match in rows if test(match["ht_total"]))
        return hit / len(rows), f"{hit}/{len(rows)}"

    rows: list[dict] = []

    def add(label: str, price: str, home_freq: tuple[float | None, str], away_freq: tuple[float | None, str]) -> None:
        home_rate, home_text = home_freq
        away_rate, away_text = away_freq
        if home_rate is None and away_rate is None:
            return
        if not price and home_text in {"", "assente"} and away_text in {"", "assente"}:
            return
        rows.append({
            "label": label,
            "price": price or "—",
            "home_text": home_text or "—",
            "away_text": away_text or "—",
            "home_rate": home_rate,
            "away_rate": away_rate,
        })

    def both(test) -> tuple[tuple[float | None, str], tuple[float | None, str]]:
        return freq(home["matches"], test), freq(away["matches"], test)

    add("Over 1.5", over_under("1.5", "Over"), *both(lambda m: m["gf"] + m["ga"] >= 2))
    add("Under 1.5", over_under("1.5", "Under"), *both(lambda m: m["gf"] + m["ga"] <= 1))
    add("Over 2.5", over_under("2.5", "Over"), *both(lambda m: m["gf"] + m["ga"] >= 3))
    add("Under 2.5", over_under("2.5", "Under"), *both(lambda m: m["gf"] + m["ga"] <= 2))
    add("Over 3.5", over_under("3.5", "Over"), *both(lambda m: m["gf"] + m["ga"] >= 4))
    add("Under 3.5", over_under("3.5", "Under"), *both(lambda m: m["gf"] + m["ga"] <= 3))
    add("Gol", money(gg.get("Gol")), *both(lambda m: m["gf"] > 0 and m["ga"] > 0))
    add("No Gol", money(gg.get("NoGol")), *both(lambda m: m["gf"] == 0 or m["ga"] == 0))
    add("MultiGol 1-5", money(multi.get("MultiGol 1-5")), *both(lambda m: 1 <= m["gf"] + m["ga"] <= 5))
    add("MultiGol 2-5", money(multi.get("MultiGol 2-5")), *both(lambda m: 2 <= m["gf"] + m["ga"] <= 5))
    add("MultiGol 1-3", money(multi.get("MultiGol 1-3")), *both(lambda m: 1 <= m["gf"] + m["ga"] <= 3))
    add(
        "MultiGol 1-3 casa",
        money(squad.get("MultiGol 1-3 Casa")),
        freq(home["matches"], lambda m: 1 <= m["gf"] <= 3),
        none_pair(),
    )
    add(
        "MultiGol 1-3 ospite",
        money(squad.get("MultiGol 1-3 Ospite")),
        none_pair(),
        freq(away["matches"], lambda m: 1 <= m["gf"] <= 3),
    )
    add(
        "Chance Mix: X o Gol",
        money(mix.get("Chance Mix: X o Gol")),
        *both(lambda m: m["gf"] == m["ga"] or (m["gf"] > 0 and m["ga"] > 0)),
    )
    add(
        "1X + Over 1.5",
        money(combo.get("1X + Over 1.5")),
        freq(home["matches"], lambda m: m["gf"] >= m["ga"] and m["gf"] + m["ga"] >= 2),
        none_pair(),
    )
    add(
        "X2 + Over 1.5",
        money(combo.get("X2 + Over 1.5")),
        none_pair(),
        freq(away["matches"], lambda m: m["gf"] >= m["ga"] and m["gf"] + m["ga"] >= 2),
    )
    add("Over 0.5 primo tempo", find_primo("Over 0.5"), ht_freq(home, lambda total: total >= 1), ht_freq(away, lambda total: total >= 1))
    add("Under 1.5 primo tempo", find_primo("Under 1.5"), ht_freq(home, lambda total: total <= 1), ht_freq(away, lambda total: total <= 1))
    add("Segna", "", *both(lambda m: m["gf"] >= 1))
    add("Porta inviolata", "", *both(lambda m: m["ga"] == 0))
    if home["shot_rows"] or away["shot_rows"]:
        add(
            "Over 9.5 tiri",
            "",
            freq(home["shot_rows"], lambda m: m["sf"] >= 10),
            freq(away["shot_rows"], lambda m: m["sf"] >= 10),
        )
        add(
            "Over 14.5 tiri",
            "",
            freq(home["shot_rows"], lambda m: m["sf"] >= 15),
            freq(away["shot_rows"], lambda m: m["sf"] >= 15),
        )
    if home["corner_rows"] or away["corner_rows"]:
        add(
            "Over 4.5 corner",
            "",
            freq(home["corner_rows"], lambda m: m["cf"] >= 5),
            freq(away["corner_rows"], lambda m: m["cf"] >= 5),
        )
        add(
            "Over 8.5 corner",
            "",
            freq(home["corner_rows"], lambda m: m["cf"] >= 9),
            freq(away["corner_rows"], lambda m: m["cf"] >= 9),
        )
    rows.sort(key=lambda row: (mean_rate(row), min_rate(row), row["label"]), reverse=True)
    return rows


def quote_cells(markets: dict) -> list[tuple[str, str]]:
    one_x_two = markets.get("1X2") or {}
    dc = markets.get("DOPPIA_CHANCE") or {}
    cells = []
    for label, value in (
        ("1", one_x_two.get("1")),
        ("X", one_x_two.get("X")),
        ("2", one_x_two.get("2")),
        ("1X", dc.get("1X")),
        ("X2", dc.get("X2")),
    ):
        text = money(value)
        if text:
            cells.append((label, text))
    return cells


def split_mean(rows: list[dict], key: str) -> str:
    if not rows:
        return "—"
    return f"{fmt_mean([match[key] for match in rows], 2)} · {len(rows)}"


def average_rows(home: dict, away: dict) -> list[tuple[str, str, str]]:
    def side_mean(side: dict, key: str, digits: int, pool: list[dict] | None = None) -> str:
        rows = side["matches"] if pool is None else pool
        values = [match[key] for match in rows if match.get(key) is not None]
        return fmt_mean(values, digits, len(side["matches"]))

    rows = [
        ("Partite", str(len(home["matches"])), str(len(away["matches"]))),
        ("In casa / in trasferta", f"{len(home['home_rows'])} / {len(home['away_rows'])}", f"{len(away['home_rows'])} / {len(away['away_rows'])}"),
        ("Gol fatti", side_mean(home, "gf", 2), side_mean(away, "gf", 2)),
        ("Gol fatti in casa", split_mean(home["home_rows"], "gf"), split_mean(away["home_rows"], "gf")),
        ("Gol fatti in trasferta", split_mean(home["away_rows"], "gf"), split_mean(away["away_rows"], "gf")),
        ("Gol subiti", side_mean(home, "ga", 2), side_mean(away, "ga", 2)),
        ("Gol subiti in casa", split_mean(home["home_rows"], "ga"), split_mean(away["home_rows"], "ga")),
        ("Gol subiti in trasferta", split_mean(home["away_rows"], "ga"), split_mean(away["away_rows"], "ga")),
        ("xG prodotti", side_mean(home, "xf", 2, home["xg_rows"]), side_mean(away, "xf", 2, away["xg_rows"])),
        ("xG concessi", side_mean(home, "xa", 2, home["xg_rows"]), side_mean(away, "xa", 2, away["xg_rows"])),
        ("Tiri", side_mean(home, "sf", 1, home["shot_rows"]), side_mean(away, "sf", 1, away["shot_rows"])),
        ("Tiri concessi", side_mean(home, "sa", 1, home["shot_rows"]), side_mean(away, "sa", 1, away["shot_rows"])),
        ("Tiri in porta", side_mean(home, "sof", 1, home["sot_rows"]), side_mean(away, "sof", 1, away["sot_rows"])),
        ("Tiri in porta concessi", side_mean(home, "soa", 1, home["sot_rows"]), side_mean(away, "soa", 1, away["sot_rows"])),
        ("Corner", side_mean(home, "cf", 1, home["corner_rows"]), side_mean(away, "cf", 1, away["corner_rows"])),
        ("Corner concessi", side_mean(home, "ca", 1, home["corner_rows"]), side_mean(away, "ca", 1, away["corner_rows"])),
    ]
    return rows


def spotlight(rows: list[dict], home_name: str, away_name: str) -> list[str]:
    items = []
    for row in rows:
        home_rate, away_rate = row["home_rate"], row["away_rate"]
        both_high = (
            home_rate is not None and away_rate is not None
            and home_rate >= HIGH and away_rate >= HIGH
        )
        if both_high:
            if home_rate <= away_rate:
                items.append((home_rate, f"{row['label']} · minimo {row['home_text']}"))
            else:
                items.append((away_rate, f"{row['label']} · minimo {row['away_text']}"))
        elif home_rate is not None and home_rate >= HIGH:
            items.append((home_rate, f"{row['label']} · {home_name} {row['home_text']}"))
        elif away_rate is not None and away_rate >= HIGH:
            items.append((away_rate, f"{row['label']} · {away_name} {row['away_text']}"))
    items.sort(key=lambda item: item[0], reverse=True)
    if not items:
        if not rows or max_rate(rows[0]) < 0:
            return ["—"]
        best = max(rows, key=max_rate)
        side = best["home_text"] if best["home_rate"] == max_rate(best) else best["away_text"]
        return [f"la più alta è {best['label']} {side}"]
    shown = [item[1] for item in items[:5]]
    extra = len(items) - len(shown)
    if extra:
        shown.append(f"altre {extra} sopra il 75%")
    return shown


def rate_cell(text: str, rate: float | None) -> str:
    if rate is None:
        return f"<td class=\"num\">{esc(text)}</td>"
    return f"<td class=\"num {band(rate)}\">{esc(text)} <b>{pct(rate)}</b></td>"


def freq_table(rows: list[dict], home_name: str, away_name: str) -> str:
    body = []
    for row in rows:
        top = " top" if mean_rate(row) >= HIGH else ""
        average = mean_rate(row)
        peak_cell = "<td class=\"num\">—</td>" if average < 0 else f"<td class=\"num {band(average)}\"><b>{pct(average)}</b></td>"
        body.append(
            f"<tr class=\"{top.strip()}\">"
            f"<td>{esc(row['label'])}</td>"
            f"{peak_cell}"
            f"{rate_cell(row['home_text'], row['home_rate'])}"
            f"{rate_cell(row['away_text'], row['away_rate'])}"
            f"<td class=\"num\">{esc(row['price'])}</td>"
            "</tr>"
        )
    if not body:
        body.append("<tr><td colspan=\"5\">Nessun conteggio sul campione.</td></tr>")
    return (
        "<table class=\"freqs\">"
        "<caption>Frequenze sul campione, ordinate per la media delle due squadre. "
        "1X solo sulla colonna di casa, X2 solo su quella ospite.</caption>"
        "<thead><tr>"
        "<th>Statistica</th><th class=\"num\">Media</th>"
        f"<th class=\"num\">{esc(home_name)}</th><th class=\"num\">{esc(away_name)}</th>"
        "<th class=\"num\">Prezzo</th>"
        "</tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def quote_table(cells: list[tuple[str, str]]) -> str:
    if not cells:
        return ""
    head = "".join(f"<th class=\"num\">{esc(label)}</th>" for label, _ in cells)
    body = "".join(f"<td class=\"num\">{esc(price)}</td>" for _, price in cells)
    return (
        "<table class=\"quotes\"><caption>Quote dello snapshot</caption>"
        f"<thead><tr>{head}</tr></thead><tbody><tr>{body}</tr></tbody></table>"
    )


def average_table(home: dict, away: dict) -> str:
    body = "".join(
        f"<tr><td>{esc(label)}</td><td class=\"num\">{esc(left)}</td><td class=\"num\">{esc(right)}</td></tr>"
        for label, left, right in average_rows(home, away)
    )
    return (
        "<table class=\"avgs\"><caption>Medie. «su N» se il dato non copre tutte le partite. "
        "In casa e in trasferta il numero dopo il punto è il campione.</caption>"
        "<thead><tr><th></th>"
        f"<th class=\"num\">{esc(home['netwin'])}</th><th class=\"num\">{esc(away['netwin'])}</th>"
        f"</tr></thead><tbody>{body}</tbody></table>"
    )


def log_table(side: dict) -> str:
    matches = side["matches"]
    columns = [
        ("Data", "date_label"),
        ("Competizione", "league"),
        ("Dove", "venue"),
        ("Incontro", "board"),
        ("Esito", "letter"),
        ("Gol", "result"),
    ]
    optional = [
        ("1° tempo", "ht_line"),
        ("xG", "xg_line"),
        ("Tiri", "shots_line"),
        ("In porta", "sot_line"),
        ("Corner", "corners_line"),
    ]
    for label, key in optional:
        if any(match.get(key) for match in matches):
            columns.append((label, key))
    head = "".join(f"<th>{esc(label)}</th>" for label, _ in columns)
    body = []
    for match in matches:
        cells = []
        for _, key in columns:
            if key == "letter":
                letter = result_letter(match)
                cells.append(f"<td class=\"tag {letter}\">{letter}</td>")
            elif key == "board":
                cells.append(f"<td>{esc(match['board'])}</td>")
            else:
                value = match.get(key) or "—"
                cells.append(f"<td class=\"num\">{esc(value)}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    if not body:
        body.append(f"<tr><td colspan=\"{len(columns)}\">Nessuna partita giocata agganciata.</td></tr>")
    notes = " ".join(side["notes"])
    note = f"<p class=\"meta\">{esc(notes)}</p>" if notes else ""
    return (
        f"<h3>Ultimi incontri · {esc(side['netwin'])}</h3>"
        "<p class=\"meta\">Dalla più recente. Gol, primo tempo, xG, tiri e corner: il primo numero è di questa squadra, il secondo dell’avversario.</p>"
        f"{note}"
        "<div class=\"scroller\"><table class=\"log\">"
        f"<thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )


def count_cell(value: int, high: int, mid: int | None = None) -> str:
    klass = "num"
    if value >= high:
        klass += " hi"
    elif mid is not None and value >= mid:
        klass += " mid"
    return f"<td class=\"{klass}\">{value}</td>"


def rate_player_cell(player: dict) -> str:
    rate = player["g90"]
    if rate is None:
        return "<td class=\"num\">—</td>"
    klass = "num"
    if player["minutes"] >= 270 and rate >= 0.55:
        klass += " hi"
    elif player["minutes"] >= 180 and rate >= 0.40:
        klass += " mid"
    return f"<td class=\"{klass}\">{rate:.2f}</td>"


def player_table(side: dict) -> str:
    squad = side["squad"]
    title = f"<h3>Calciatori · {esc(side['netwin'])}</h3>"
    if not squad["club"]:
        return (
            title
            + "<p class=\"meta\">Rosa 2026/2027 assente in players per questo club. "
            "Falli del singolo assenti in tutto il feed.</p>"
        )
    note = (
        f"<p class=\"meta\">Stagione {esc(SEASON)}, {esc(squad['league'])}, club «{esc(squad['club'])}». "
        f"Rosa {squad['squad']}: {squad['goals']} gol, {squad['assists']} assist, "
        f"{squad['yellow']} {'giallo' if squad['yellow'] == 1 else 'gialli'}, "
        f"{squad['red']} {'rosso' if squad['red'] == 1 else 'rossi'}. "
        "In tabella chi ha almeno un gol, un assist o una sanzione. "
        "Falli del singolo assenti nel feed. Non è una distinta e non è una giocata sul singolo.</p>"
    )
    if not squad["shown"]:
        return title + note + "<p class=\"meta\">Nessun gol, assist o sanzione sulla rosa salvata.</p>"
    body = []
    for player in squad["shown"]:
        body.append(
            "<tr>"
            f"<td>{esc(player['name'])}</td>"
            f"<td>{esc(player['role'])}</td>"
            f"<td class=\"num\">{player['apps']}</td>"
            f"<td class=\"num\">{player['minutes']}</td>"
            f"{count_cell(player['goals'], 3, 2)}"
            f"{count_cell(player['assists'], 3, 2)}"
            f"{rate_player_cell(player)}"
            f"{count_cell(player['yellow'], 3, 2)}"
            f"{count_cell(player['red'], 1)}"
            "</tr>"
        )
    table = (
        "<div class=\"scroller\"><table class=\"squad\">"
        "<thead><tr>"
        "<th>Calciatore</th><th>Ruolo</th><th class=\"num\">Pres.</th><th class=\"num\">Minuti</th>"
        "<th class=\"num\">Gol</th><th class=\"num\">Assist</th><th class=\"num\">Gol/90</th>"
        "<th class=\"num\">Gialli</th><th class=\"num\">Rossi</th>"
        f"</tr></thead><tbody>{''.join(body)}</tbody></table></div>"
    )
    return title + note + table


def article(match: dict, home: dict, away: dict) -> tuple[str, list[str], str]:
    slug = match["match_name"].lower().replace(" ", "-")
    rows = frequency_rows(match["markets"], home, away)
    lines = spotlight(rows, home["netwin"], away["netwin"])
    title = match["match_name"].replace(" vs ", " contro ")
    block = f"""
    <article id="{esc(slug)}">
      <p class="kicker">Champions League · {esc(kickoff_label(match['kickoff']))}</p>
      <h2>{esc(title)}</h2>
      {quote_table(quote_cells(match['markets']))}
      {freq_table(rows, home['netwin'], away['netwin'])}
      {average_table(home, away)}
      {log_table(home)}
      {player_table(home)}
      {log_table(away)}
      {player_table(away)}
    </article>
    """
    return slug, lines, block


def render(stamp: str, matches: list[dict], sides: dict[str, dict]) -> str:
    index_rows = []
    articles = []
    for match in matches:
        home_name, away_name = match["match_name"].split(" vs ", 1)
        slug, lines, block = article(match, sides[home_name], sides[away_name])
        index_rows.append(
            "<tr>"
            f"<td class=\"num\">{esc(kickoff_clock(match['kickoff']))}</td>"
            f"<td><a href=\"#{esc(slug)}\">{esc(home_name)} contro {esc(away_name)}</a></td>"
            f"<td>{'<br>'.join(esc(line) for line in lines)}</td>"
            "</tr>"
        )
        articles.append(block)
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Champions League 21 ottobre 2026 — tabelle</title>
<style>
  :root {{
    --bg: #f4f6f8;
    --paper: #ffffff;
    --ink: #1a1d21;
    --muted: #5c6770;
    --line: #d9e0e6;
    --head: #eef2f5;
    --link: #1a4f86;
    --hi: #dff3e4;
    --hi-ink: #146c36;
    --mid: #fff6dd;
    --mid-ink: #8a5a00;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font: 14px/1.4 "Segoe UI", system-ui, sans-serif;
  }}
  .wrap {{ max-width: 1120px; margin: 0 auto; padding: 24px 16px 64px; }}
  h1 {{ font-size: 26px; font-weight: 650; letter-spacing: -0.02em; margin: 0 0 8px; }}
  h2 {{ font-size: 22px; font-weight: 650; margin: 0 0 8px; }}
  h3 {{ font-size: 16px; margin: 18px 0 4px; }}
  a {{ color: var(--link); }}
  p {{ margin: 0 0 10px; }}
  .kicker {{ color: var(--muted); font-size: 12px; letter-spacing: .04em; text-transform: uppercase; margin: 0 0 4px; }}
  .meta {{ color: var(--muted); font-size: 12px; }}
  .legend {{ color: var(--muted); font-size: 13px; }}
  .swatch {{
    display: inline-block; width: 12px; height: 12px; margin: 0 4px 0 12px; vertical-align: -2px;
    border: 1px solid var(--line);
  }}
  .swatch.hi {{ background: var(--hi); }}
  .swatch.mid {{ background: var(--mid); }}
  article {{
    background: var(--paper);
    border: 1px solid var(--line);
    border-top: 3px solid #1a1d21;
    padding: 16px 14px 8px;
    margin-top: 18px;
  }}
  .scroller {{ overflow-x: auto; margin-bottom: 8px; }}
  table {{ width: 100%; border-collapse: collapse; background: var(--paper); margin: 0 0 8px; }}
  caption {{
    caption-side: top;
    text-align: left;
    font-weight: 650;
    font-size: 14px;
    padding: 12px 0 6px;
  }}
  th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ background: var(--head); color: var(--muted); font-size: 12px; font-weight: 650; }}
  td.num, th.num {{ text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }}
  td.hi {{ background: var(--hi); color: var(--hi-ink); }}
  td.mid {{ background: var(--mid); }}
  tr.top td:first-child {{ font-weight: 700; }}
  table.quotes {{ width: auto; min-width: 320px; }}
  table.log td.num {{ text-align: left; white-space: nowrap; }}
  table.log td:nth-child(4) {{ white-space: normal; }}
  table.squad td:first-child {{ white-space: normal; min-width: 11rem; }}
  .tag {{ font-weight: 700; text-align: center; }}
  table.index td {{ line-height: 1.55; }}
  .tag.V {{ color: var(--hi-ink); }}
  .tag.P {{ color: var(--mid-ink); }}
  .tag.S {{ color: #9b2c2c; }}
  tbody tr:hover td {{ background: #f3f7fb; }}
  tbody tr:hover td.hi {{ background: #d3edd9; }}
  tbody tr:hover td.mid {{ background: #ffefc2; }}
  @media (max-width: 720px) {{
    h1 {{ font-size: 22px; }}
    th, td {{ padding: 5px 6px; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <p class="kicker">BAgent · Champions League</p>
  <h1>21 ottobre 2026, nove partite</h1>
  <p>Frequenza sul campione delle ultime partite agganciate, non una probabilità di modello. Lo sfondo verde è almeno il 75% (sui calciatori: almeno 3 gol, 3 assist o 3 gialli, oppure un rosso). Il giallo va dal 60% al 74% (sui calciatori: 2 gol, 2 assist o 2 gialli). La colonna «Media» è la media delle due percentuali. I calciatori sono i totali di campionato 2026/2027 già in archivio: gol, assist e sanzioni. I falli del singolo non sono nel feed.</p>
  <p class="legend"><i class="swatch hi"></i> almeno 75% <i class="swatch mid"></i> dal 60% al 74%</p>
  <p class="meta">Prezzi da data/netwin_live_odds.json, generato il {esc(stamp)}. Conteggi da data/bagent.db, dopo l’unione delle righe duplicate dello stesso risultato. Questa pagina non propone una selezione.</p>
  <table class="index">
    <caption>Frequenze di almeno il 75% su ciascuna partita</caption>
    <thead><tr><th>Calcio d'inizio</th><th>Partita</th><th>Statistiche più alte</th></tr></thead>
    <tbody>
      {''.join(index_rows)}
    </tbody>
  </table>
  {''.join(articles)}
</div>
</body>
</html>
"""


def main() -> None:
    stamp, matches = load_odds()
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.execute("PRAGMA wal_checkpoint")
    needed = []
    for match in matches:
        home_name, away_name = match["match_name"].split(" vs ", 1)
        needed.extend((home_name, away_name))
    sides = {name: build_side(conn, name) for name in dict.fromkeys(needed)}
    conn.close()
    OUT_PATH.write_text(render(stamp, matches, sides), encoding="utf-8")
    print(f"snapshot {stamp}")
    print(f"partite {len(matches)}")
    for match in matches:
        home_name, away_name = match["match_name"].split(" vs ", 1)
        home, away = sides[home_name], sides[away_name]
        dated = sum(1 for row in home["matches"] if row["iso"])
        print(
            f"{kickoff_clock(match['kickoff'])} {home_name} {len(home['matches'])} date {dated} "
            f"1T {sum(1 for row in home['matches'] if row['ht_line'])} "
            f"| {away_name} {len(away['matches'])} date {sum(1 for row in away['matches'] if row['iso'])}"
        )
    print(OUT_PATH)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Schede partita per la Champions League del 21 ottobre 2026.

Legge i nove incontri in data/netwin_live_odds.json e i tabellini in data/bagent.db.
Non propone una selezione e non calcola un edge.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
import unicodedata
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "bagent.db"
ODDS_PATH = ROOT / "data" / "netwin_live_odds.json"
OUT_PATH = ROOT / "portal" / "ucl_21ott_2026.html"

SKIP_STATUS = {"NS", "incomplete", "canceled", "suspended", "PST"}

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
        return text[9:14]
    return text


def load_odds() -> tuple[str, list[dict]]:
    payload = json.loads(ODDS_PATH.read_text(encoding="utf-8"))
    rows = [
        match for match in payload["matches"]
        if str(match.get("kickoff", "")).startswith("20261021")
        and "champ" in (match.get("tournament") or "").lower()
    ]
    rows.sort(key=lambda match: (match["kickoff"], match["match_name"]))
    return payload.get("timestamp") or "", rows


def load_played(conn: sqlite3.Connection, names: list[str]) -> list[dict]:
    marks = ",".join("?" for _ in names)
    query = f"""
        SELECT id, league, status, date_gmt, home_team, away_team,
               home_goals, away_goals, home_goals_ht, away_goals_ht,
               home_shots, away_shots, home_corners, away_corners,
               home_xg, away_xg
        FROM matches
        WHERE (home_team IN ({marks}) OR away_team IN ({marks}))
          AND home_goals IS NOT NULL AND away_goals IS NOT NULL
          AND COALESCE(status, 'FT') NOT IN ('NS', 'incomplete', 'canceled', 'suspended', 'PST')
        ORDER BY id DESC
    """
    found = []
    for row in conn.execute(query, (*names, *names)):
        found.append({
            "id": row[0],
            "league": row[1] or "",
            "status": row[2],
            "date": row[3],
            "home": row[4],
            "away": row[5],
            "hg": row[6],
            "ag": row[7],
            "hth": row[8],
            "hta": row[9],
            "hs": row[10],
            "aws": row[11],
            "hc": row[12],
            "ac": row[13],
            "hx": row[14],
            "ax": row[15],
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
    return (int(shots), int(corners), int(xg), int(ht), int(bool(row["date"])), row["id"])


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
        best = max(items, key=richness)
        merged = dict(best)
        for other in items:
            for field in ("date", "hth", "hta", "hs", "aws", "hc", "ac", "hx", "ax", "league"):
                if not useful_number(merged.get(field), negative_ok=True) and field in {"hx", "ax", "hth", "hta"}:
                    if merged.get(field) is None and other.get(field) is not None and other.get(field) >= 0:
                        merged[field] = other[field]
                elif field in {"hs", "aws", "hc", "ac"}:
                    if not useful_number(merged.get(field)) and useful_number(other.get(field)):
                        merged[field] = other[field]
                elif field == "date" and not merged.get("date") and other.get("date"):
                    merged["date"] = other["date"]
                elif field == "league" and not merged.get("league") and other.get("league"):
                    merged["league"] = other["league"]
        kept.append(merged)
    kept.sort(key=lambda row: row["id"], reverse=True)
    return kept


def shot_pair(row: dict) -> tuple[int, int] | None:
    if useful_number(row["hs"]) and useful_number(row["aws"]) and row["hs"] > 0 and row["aws"] > 0:
        return (row["hs"], row["aws"])
    return None


def corner_pair(row: dict) -> tuple[int, int] | None:
    if useful_number(row["hc"]) and useful_number(row["ac"]):
        return (row["hc"], row["ac"])
    return None


def repeated(rows: list[dict], pair) -> bool:
    values = [pair(row) for row in rows]
    values = [value for value in values if value is not None]
    return len(values) >= 4 and len(set(values)) == 1


def view(row: dict, names: set[str]) -> dict:
    is_home = row["home"] in names
    pair_shots = shot_pair(row)
    pair_corners = corner_pair(row)
    xg_for = row["hx"] if is_home else row["ax"]
    xg_against = row["ax"] if is_home else row["hx"]
    xg_ok = row["hx"] is not None and row["ax"] is not None and (row["hx"] > 0 or row["ax"] > 0 or pair_shots)
    return {
        "venue": "Casa" if is_home else "Trasferta",
        "opponent": row["away"] if is_home else row["home"],
        "home": row["home"],
        "away": row["away"],
        "hg": row["hg"],
        "ag": row["ag"],
        "gf": row["hg"] if is_home else row["ag"],
        "ga": row["ag"] if is_home else row["hg"],
        "league": row["league"],
        "date": row["date"],
        "ht": f"{row['hth']}-{row['hta']}" if row["hth"] is not None and row["hta"] is not None else "",
        "shots": f"{row['hs']}-{row['aws']}" if pair_shots else "",
        "corners": f"{row['hc']}-{row['ac']}" if pair_corners else "",
        "xg": f"{row['hx']:.2f}-{row['ax']:.2f}" if xg_ok else "",
        "sf": (row["hs"] if is_home else row["aws"]) if pair_shots else None,
        "sa": (row["aws"] if is_home else row["hs"]) if pair_shots else None,
        "cf": (row["hc"] if is_home else row["ac"]) if pair_corners else None,
        "ca": (row["ac"] if is_home else row["hc"]) if pair_corners else None,
        "xf": xg_for if xg_ok else None,
        "xa": xg_against if xg_ok else None,
    }


def mean(values: list[float]) -> float | None:
    if not values:
        return None
    return sum(values) / len(values)


def fmt_mean(values: list[float], digits: int) -> str:
    value = mean(values)
    if value is None:
        return "assente"
    return f"{value:.{digits}f}"


def count(matches: list[dict], test) -> str:
    if not matches:
        return "assente"
    hit = sum(1 for match in matches if test(match))
    return f"{hit} su {len(matches)}"


def series(matches: list[dict], key: str) -> str:
    values = [match[key] for match in matches if match.get(key) is not None and match.get(key) != ""]
    if not values:
        return ""
    if isinstance(values[0], float):
        return " ".join(f"{value:.2f}" for value in values)
    return " ".join(str(value) for value in values)


def build_side(conn: sqlite3.Connection, netwin_name: str) -> dict:
    db_names, canonical = LINKS[netwin_name]
    played = load_played(conn, db_names)
    names = set(db_names)
    shots_repeated = repeated(played, shot_pair)
    corners_repeated = repeated(played, corner_pair)
    sample = [view(row, names) for row in played[:SAMPLE]]
    if shots_repeated:
        for match in sample:
            match["shots"] = ""
            match["sf"] = None
            match["sa"] = None
    if corners_repeated:
        for match in sample:
            match["corners"] = ""
            match["cf"] = None
            match["ca"] = None
    shot_rows = [match for match in sample if match["sf"] is not None]
    corner_rows = [match for match in sample if match["cf"] is not None]
    xg_rows = [match for match in sample if match["xf"] is not None]
    home_rows = [match for match in sample if match["venue"] == "Casa"]
    away_rows = [match for match in sample if match["venue"] == "Trasferta"]
    notes = []
    if netwin_name != canonical:
        notes.append(f"Nome Netwin «{netwin_name}» agganciato a «{canonical}» nel database.")
    if len(played) > len(sample):
        notes.append(f"Ultime {len(sample)} partite distinte, su {len(played)} disponibili.")
    else:
        notes.append(f"{len(sample)} partite distinte.")
    if shots_repeated:
        notes.append("Tiri identici su tutte le righe: colonna esclusa.")
    if corners_repeated:
        notes.append("Corner identici su tutte le righe: colonna esclusa.")
    if not shot_rows and not shots_repeated:
        notes.append("Tiri assenti su queste righe.")
    elif shot_rows and len(shot_rows) != len(sample):
        notes.append(f"Tiri presenti su {len(shot_rows)} delle {len(sample)} partite nel conto.")
    if not xg_rows:
        notes.append("xG assente su queste righe.")
    if any(match["ht"] for match in sample):
        pass
    else:
        notes.append("Primo tempo assente su queste righe.")
    if not any(match["date"] for match in sample):
        notes.append("Data assente su queste righe.")
    if len(sample) < 4:
        notes.append("Campione corto.")
    return {
        "netwin": netwin_name,
        "canonical": canonical,
        "matches": sample,
        "shot_rows": shot_rows,
        "corner_rows": corner_rows,
        "xg_rows": xg_rows,
        "home_rows": home_rows,
        "away_rows": away_rows,
        "available": len(played),
        "notes": notes,
        "shots_repeated": shots_repeated,
        "corners_repeated": corners_repeated,
    }


def result_letter(match: dict) -> str:
    if match["gf"] > match["ga"]:
        return "V"
    if match["gf"] == match["ga"]:
        return "P"
    return "S"


def score_phrase(match: dict) -> str:
    line = f"{match['home']} {match['hg']}-{match['ag']} {match['away']}"
    league = f", {match['league']}" if match["league"] else ""
    return line + league


def reading(home: dict, away: dict, prices: dict) -> str:
    def profile(side: dict) -> str:
        matches = side["matches"]
        if not matches:
            return f"{side['netwin']} non ha partite giocate agganciate nel database."
        leagues = ", ".join(sorted({match["league"] for match in matches if match["league"]}))
        goals = (
            f"gol fatti {fmt_mean([m['gf'] for m in matches], 2)} "
            f"e subiti {fmt_mean([m['ga'] for m in matches], 2)}"
        )
        def scoped(label: str, rows: list[dict], for_key: str, against_key: str, digits: int) -> str:
            if not rows:
                return ""
            scope = f" su {len(rows)} righe" if len(rows) != len(matches) else ""
            return (
                f", {label}{scope} {fmt_mean([m[for_key] for m in rows], digits)} "
                f"e concessi {fmt_mean([m[against_key] for m in rows], digits)}"
            )

        extra = (
            scoped("xG prodotti", side["xg_rows"], "xf", "xa", 2)
            + scoped("tiri", side["shot_rows"], "sf", "sa", 1)
            + scoped("corner", side["corner_rows"], "cf", "ca", 1)
        )
        base = f"{side['netwin']}: {len(matches)} partite ({leagues}), {goals}{extra}."
        if len(matches) <= 4:
            listed = "; ".join(score_phrase(match) for match in matches)
            base += f" Risultati: {listed}."
        return base

    one = prices.get("1")
    over = prices.get("over25")
    bits = [profile(home), profile(away)]
    if home["matches"] and away["matches"]:
        bits.append(
            "Over 2.5 nelle partite già giocate: "
            f"{home['netwin']} {count(home['matches'], lambda m: m['gf'] + m['ga'] >= 3)}, "
            f"{away['netwin']} {count(away['matches'], lambda m: m['gf'] + m['ga'] >= 3)}."
        )
    if over is not None:
        bits.append(f"Nello snapshot Over 2.5 è a {over:.2f}.")
    if one is not None and one <= 1.35:
        bits.append(f"Nello snapshot il segno 1 è a {one:.2f}: il prezzo descrive una favorita netta.")
    elif one is not None:
        bits.append(f"Nello snapshot il segno 1 è a {one:.2f}, il pareggio a {prices['X']:.2f}, il segno 2 a {prices['2']:.2f}.")
    return " ".join(bits)


def flat_prices(markets: dict) -> dict:
    one = (markets.get("1X2") or {}).get("1")
    draw = (markets.get("1X2") or {}).get("X")
    two = (markets.get("1X2") or {}).get("2")
    under_over = markets.get("UNDER_OVER") or {}

    def line(name: str, side: str):
        return (under_over.get(name) or {}).get(side)

    return {
        "1": one, "X": draw, "2": two, "over25": line("2.5", "Over"),
    }


def price_rows(markets: dict, home: dict, away: dict) -> list[tuple[str, str, str, str]]:
    under_over = markets.get("UNDER_OVER") or {}
    primo = markets.get("PRIMO_TEMPO") or {}
    mix = markets.get("CHANCE_MIX") or {}
    multi = markets.get("MULTIGOL") or {}
    combo = markets.get("COMBO") or {}
    squad = markets.get("MULTIGOL_SQUADRA") or {}
    gg = markets.get("GOL_NOGOL") or {}
    dc = markets.get("DOPPIA_CHANCE") or {}
    one_x_two = markets.get("1X2") or {}

    def money(family_value):
        if family_value is None:
            return ""
        return f"{float(family_value):.2f}"

    def over_under(line: str, side: str):
        return money((under_over.get(line) or {}).get(side))

    def find_primo(fragment: str):
        for key, value in primo.items():
            if fragment in key:
                return money(value)
        return ""

    ht_ready = any(match["ht"] for match in home["matches"]) or any(match["ht"] for match in away["matches"])

    def ht_count(side: dict, test) -> str:
        rows = [match for match in side["matches"] if match["ht"]]
        if not rows:
            return "primo tempo assente"
        hit = 0
        for match in rows:
            left, right = match["ht"].split("-")
            if test(int(left) + int(right)):
                hit += 1
        return f"{hit} su {len(rows)}"

    def both(test) -> tuple[str, str]:
        return count(home["matches"], test), count(away["matches"], test)

    rows: list[tuple[str, str, str, str]] = []

    def add(label: str, price: str, home_freq: str = "—", away_freq: str = "—"):
        if price:
            rows.append((label, price, home_freq, away_freq))

    add("1", money(one_x_two.get("1")))
    add("X", money(one_x_two.get("X")))
    add("2", money(one_x_two.get("2")))
    add("1X", money(dc.get("1X")))
    add("X2", money(dc.get("X2")))
    h, a = both(lambda m: m["gf"] + m["ga"] >= 2)
    add("Over 1.5", over_under("1.5", "Over"), h, a)
    h, a = both(lambda m: m["gf"] + m["ga"] <= 1)
    add("Under 1.5", over_under("1.5", "Under"), h, a)
    h, a = both(lambda m: m["gf"] + m["ga"] >= 3)
    add("Over 2.5", over_under("2.5", "Over"), h, a)
    h, a = both(lambda m: m["gf"] + m["ga"] <= 2)
    add("Under 2.5", over_under("2.5", "Under"), h, a)
    h, a = both(lambda m: m["gf"] + m["ga"] >= 4)
    add("Over 3.5", over_under("3.5", "Over"), h, a)
    h, a = both(lambda m: m["gf"] + m["ga"] <= 3)
    add("Under 3.5", over_under("3.5", "Under"), h, a)
    h, a = both(lambda m: m["gf"] > 0 and m["ga"] > 0)
    add("Gol", money(gg.get("Gol")), h, a)
    h, a = both(lambda m: m["gf"] == 0 or m["ga"] == 0)
    add("No Gol", money(gg.get("NoGol")), h, a)
    h, a = both(lambda m: 1 <= m["gf"] + m["ga"] <= 5)
    add("MultiGol 1-5", money(multi.get("MultiGol 1-5")), h, a)
    h, a = both(lambda m: 2 <= m["gf"] + m["ga"] <= 5)
    add("MultiGol 2-5", money(multi.get("MultiGol 2-5")), h, a)
    h, a = both(lambda m: 1 <= m["gf"] + m["ga"] <= 3)
    add("MultiGol 1-3", money(multi.get("MultiGol 1-3")), h, a)
    add(
        "MultiGol 1-3 casa",
        money(squad.get("MultiGol 1-3 Casa")),
        count(home["matches"], lambda m: 1 <= m["gf"] <= 3),
        "—",
    )
    add(
        "MultiGol 1-3 ospite",
        money(squad.get("MultiGol 1-3 Ospite")),
        "—",
        count(away["matches"], lambda m: 1 <= m["gf"] <= 3),
    )
    h, a = both(lambda m: m["gf"] == m["ga"] or (m["gf"] > 0 and m["ga"] > 0))
    add("Chance Mix: X o Gol", money(mix.get("Chance Mix: X o Gol")), h, a)
    add(
        "1X + Over 1.5",
        money(combo.get("1X + Over 1.5")),
        count(home["matches"], lambda m: m["gf"] >= m["ga"] and m["gf"] + m["ga"] >= 2),
        "—",
    )
    add(
        "X2 + Over 1.5",
        money(combo.get("X2 + Over 1.5")),
        "—",
        count(away["matches"], lambda m: m["gf"] >= m["ga"] and m["gf"] + m["ga"] >= 2),
    )
    if ht_ready:
        add("Over 0.5 primo tempo", find_primo("Over 0.5"), ht_count(home, lambda t: t >= 1), ht_count(away, lambda t: t >= 1))
        add("Under 1.5 primo tempo", find_primo("Under 1.5"), ht_count(home, lambda t: t <= 1), ht_count(away, lambda t: t <= 1))
    else:
        add("Over 0.5 primo tempo", find_primo("Over 0.5"), "primo tempo assente", "primo tempo assente")
        add("Under 1.5 primo tempo", find_primo("Under 1.5"), "primo tempo assente", "primo tempo assente")
    return rows


def numbers_table(home: dict, away: dict) -> list[tuple[str, str, str]]:
    def goals(side: dict, key: str, digits: int, rows: list[dict] | None = None) -> str:
        pool = side["matches"] if rows is None else rows
        values = [match[key] for match in pool if match.get(key) is not None]
        if not values:
            return "assente"
        text = fmt_mean(values, digits)
        listed = series(pool, key)
        if listed and key in {"gf", "ga", "sf", "cf", "xf"}:
            text += f"<br><span class=\"series\">{esc(listed)}</span>"
        return text

    def rate(side: dict, test, pool: list[dict] | None = None) -> str:
        return count(pool if pool is not None else side["matches"], test)

    def split(rows: list[dict], key: str) -> str:
        if not rows:
            return "—"
        values = [match[key] for match in rows]
        return f"{fmt_mean(values, 2)} su {len(rows)}"

    rows = [
        ("Partite nel conto", str(len(home["matches"])), str(len(away["matches"]))),
        ("In casa", str(len(home["home_rows"])) or "0", str(len(away["home_rows"])) or "0"),
        ("In trasferta", str(len(home["away_rows"])) or "0", str(len(away["away_rows"])) or "0"),
        ("Gol fatti", goals(home, "gf", 2), goals(away, "gf", 2)),
        ("Gol fatti in casa", split(home["home_rows"], "gf"), split(away["home_rows"], "gf")),
        ("Gol fatti in trasferta", split(home["away_rows"], "gf"), split(away["away_rows"], "gf")),
        ("Gol subiti", goals(home, "ga", 2), goals(away, "ga", 2)),
        ("Gol subiti in casa", split(home["home_rows"], "ga"), split(away["home_rows"], "ga")),
        ("Gol subiti in trasferta", split(home["away_rows"], "ga"), split(away["away_rows"], "ga")),
        ("xG prodotti", goals(home, "xf", 2, home["xg_rows"]), goals(away, "xf", 2, away["xg_rows"])),
        ("xG concessi", goals(home, "xa", 2, home["xg_rows"]), goals(away, "xa", 2, away["xg_rows"])),
        ("Tiri", goals(home, "sf", 1, home["shot_rows"]), goals(away, "sf", 1, away["shot_rows"])),
        ("Tiri concessi", goals(home, "sa", 1, home["shot_rows"]), goals(away, "sa", 1, away["shot_rows"])),
        ("Corner", goals(home, "cf", 1, home["corner_rows"]), goals(away, "cf", 1, away["corner_rows"])),
        ("Corner concessi", goals(home, "ca", 1, home["corner_rows"]), goals(away, "ca", 1, away["corner_rows"])),
        ("Over 1.5", rate(home, lambda m: m["gf"] + m["ga"] >= 2), rate(away, lambda m: m["gf"] + m["ga"] >= 2)),
        ("Over 2.5", rate(home, lambda m: m["gf"] + m["ga"] >= 3), rate(away, lambda m: m["gf"] + m["ga"] >= 3)),
        ("Under 3.5", rate(home, lambda m: m["gf"] + m["ga"] <= 3), rate(away, lambda m: m["gf"] + m["ga"] <= 3)),
        ("Gol entrambe", rate(home, lambda m: m["gf"] > 0 and m["ga"] > 0), rate(away, lambda m: m["gf"] > 0 and m["ga"] > 0)),
        ("Segna", rate(home, lambda m: m["gf"] >= 1), rate(away, lambda m: m["gf"] >= 1)),
        ("Porta inviolata", rate(home, lambda m: m["ga"] == 0), rate(away, lambda m: m["ga"] == 0)),
        ("Vittorie", rate(home, lambda m: m["gf"] > m["ga"]), rate(away, lambda m: m["gf"] > m["ga"])),
        ("Pareggi", rate(home, lambda m: m["gf"] == m["ga"]), rate(away, lambda m: m["gf"] == m["ga"])),
        ("Sconfitte", rate(home, lambda m: m["gf"] < m["ga"]), rate(away, lambda m: m["gf"] < m["ga"])),
    ]
    if home["shot_rows"] or away["shot_rows"]:
        rows.append((
            "Over 9.5 tiri",
            rate(home, lambda m: m["sf"] is not None and m["sf"] >= 10, home["shot_rows"]),
            rate(away, lambda m: m["sf"] is not None and m["sf"] >= 10, away["shot_rows"]),
        ))
        rows.append((
            "Over 14.5 tiri",
            rate(home, lambda m: m["sf"] is not None and m["sf"] >= 15, home["shot_rows"]),
            rate(away, lambda m: m["sf"] is not None and m["sf"] >= 15, away["shot_rows"]),
        ))
    if home["corner_rows"] or away["corner_rows"]:
        rows.append((
            "Over 4.5 corner",
            rate(home, lambda m: m["cf"] is not None and m["cf"] >= 5, home["corner_rows"]),
            rate(away, lambda m: m["cf"] is not None and m["cf"] >= 5, away["corner_rows"]),
        ))
        rows.append((
            "Over 8.5 corner",
            rate(home, lambda m: m["cf"] is not None and m["cf"] >= 9, home["corner_rows"]),
            rate(away, lambda m: m["cf"] is not None and m["cf"] >= 9, away["corner_rows"]),
        ))
    return rows


def log_table(side: dict) -> str:
    body = []
    for match in side["matches"]:
        bits = []
        if match["date"]:
            bits.append(esc(match["date"]))
        bits.append(esc(match["league"]))
        if match["ht"]:
            bits.append("intervallo " + esc(match["ht"]))
        detail = []
        if match["shots"]:
            detail.append("tiri " + esc(match["shots"]))
        if match["corners"]:
            detail.append("corner " + esc(match["corners"]))
        if match["xg"]:
            detail.append("xG " + esc(match["xg"]))
        if not detail:
            detail.append("tiri, corner e xG assenti")
        body.append(
            "<tr>"
            f"<td>{esc(result_letter(match))} · {esc(match['venue'])}</td>"
            f"<td>{esc(match['home'])} {match['hg']}-{match['ag']} {esc(match['away'])}"
            f"<br><span class=\"series\">{' · '.join(bits)}</span></td>"
            f"<td>{' · '.join(detail)}</td>"
            "</tr>"
        )
    if not body:
        body.append("<tr><td colspan=\"3\">Nessuna partita giocata agganciata.</td></tr>")
    return (
        "<table><thead><tr><th>Esito</th><th>Tabellino</th><th>Numeri</th></tr></thead>"
        f"<tbody>{''.join(body)}</tbody></table>"
    )


def side_block(side: dict) -> str:
    notes = "".join(f"<li>{esc(note)}</li>" for note in side["notes"])
    return (
        f"<section><h3>{esc(side['netwin'])}</h3>"
        f"<p class=\"meta\">Storico «{esc(side['canonical'])}»</p>"
        f"<ul class=\"notes\">{notes}</ul>"
        f"{log_table(side)}</section>"
    )


def article(match: dict, home: dict, away: dict) -> str:
    slug = esc(match["match_name"].lower().replace(" ", "-"))
    markets = match["markets"]
    prices = flat_prices(markets)
    text = reading(home, away, prices)
    price_body = "".join(
        "<tr>"
        f"<td>{esc(label)}</td><td class=\"num\">{esc(price)}</td>"
        f"<td class=\"num\">{home_freq if '<' in home_freq else esc(home_freq)}</td>"
        f"<td class=\"num\">{away_freq if '<' in away_freq else esc(away_freq)}</td>"
        "</tr>"
        for label, price, home_freq, away_freq in price_rows(markets, home, away)
    )
    number_body = "".join(
        f"<tr><td>{esc(label)}</td><td class=\"num\">{left}</td><td class=\"num\">{right}</td></tr>"
        for label, left, right in numbers_table(home, away)
    )
    return f"""
    <article id="{slug}">
      <p class="kicker">Champions League · {esc(kickoff_label(match['kickoff']))}</p>
      <h2>{esc(match['match_name'].replace(' vs ', ' contro '))}</h2>
      <p>{esc(text)}</p>
      <h3>Prezzi dello snapshot</h3>
      <p class="meta">Il conteggio è sulle partite già giocate da quella squadra. Una combo 1X usa solo la colonna di casa, una combo X2 solo quella ospite.</p>
      <table>
        <thead><tr><th>Mercato</th><th>Prezzo</th><th>{esc(home['netwin'])}</th><th>{esc(away['netwin'])}</th></tr></thead>
        <tbody>{price_body}</tbody>
      </table>
      <h3>Numeri affiancati</h3>
      <table>
        <thead><tr><th></th><th>{esc(home['netwin'])}</th><th>{esc(away['netwin'])}</th></tr></thead>
        <tbody>{number_body}</tbody>
      </table>
      <h3>Tabellini</h3>
      <div class="pair">{side_block(home)}{side_block(away)}</div>
    </article>
    """


def render(stamp: str, matches: list[dict], sides: dict[str, dict]) -> str:
    nav = []
    articles = []
    for match in matches:
        home_name, away_name = match["match_name"].split(" vs ", 1)
        slug = match["match_name"].lower().replace(" ", "-")
        nav.append(
            f"<li><a href=\"#{esc(slug)}\">{esc(kickoff_clock(match['kickoff']))} {esc(home_name)} contro {esc(away_name)}</a></li>"
        )
        articles.append(article(match, sides[home_name], sides[away_name]))
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Champions League 21 ottobre 2026 — schede partita</title>
<style>
  :root {{
    --bg: #f3f0e8;
    --paper: #fffdf8;
    --ink: #1d1a16;
    --muted: #5e584e;
    --line: #e2d9cc;
    --link: #1f4b82;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    background: var(--bg);
    color: var(--ink);
    font: 17px/1.5 Georgia, "Iowan Old Style", "Palatino Linotype", serif;
  }}
  .wrap {{ max-width: 980px; margin: 0 auto; padding: 28px 16px 72px; }}
  h1 {{ font-size: 28px; font-weight: 600; letter-spacing: -0.03em; margin: 0 0 8px; }}
  h2 {{ font-size: 24px; font-weight: 600; margin: 0 0 8px; }}
  h3 {{ font-size: 16px; margin: 18px 0 6px; font-family: "Segoe UI", sans-serif; }}
  a {{ color: var(--link); }}
  .kicker, .meta, nav, table, .warn, .notes {{ font-family: "Segoe UI", sans-serif; }}
  .kicker {{ color: var(--muted); font-size: 12px; letter-spacing: .05em; text-transform: uppercase; margin: 0 0 4px; }}
  .meta {{ color: var(--muted); font-size: 13px; margin: 0 0 8px; }}
  .warn {{ background: #f6e7c3; border: 1px solid #e0cf9c; padding: 12px 14px; font-size: 14px; line-height: 1.45; }}
  nav ul {{ padding-left: 18px; }}
  nav li {{ margin: 4px 0; font-size: 15px; }}
  article {{
    background: var(--paper);
    border: 1px solid var(--line);
    padding: 18px 16px 8px;
    margin-top: 18px;
  }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin: 0 0 8px; }}
  th, td {{ text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line); vertical-align: top; }}
  th {{ color: var(--muted); font-weight: 600; }}
  .num {{ font-variant-numeric: tabular-nums; }}
  .series {{ color: var(--muted); font-size: 12px; }}
  .pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
  .notes {{ margin: 0 0 8px; padding-left: 18px; color: var(--muted); font-size: 13px; }}
  @media (max-width: 800px) {{
    .pair {{ grid-template-columns: 1fr; }}
    h1 {{ font-size: 24px; }}
  }}
</style>
</head>
<body>
<div class="wrap">
  <p class="kicker">BAgent · lettura partita per partita</p>
  <h1>Champions League, 21 ottobre 2026</h1>
  <p>Nove partite. Per ciascuna: tabellini agganciati nel database, medie su quel campione, e prezzi dello snapshot accanto al conteggio della statistica corrispondente.</p>
  <p class="warn">Prezzi da <span class="num">data/netwin_live_odds.json</span>, generato il {esc(stamp)}. Oggi è il 21 ottobre: lo snapshot ha circa venti ore. I conteggi vengono da <span class="num">data/bagent.db</span>, dopo aver unito le righe duplicate dello stesso risultato. Questa pagina non propone una selezione.</p>
  <nav><ul>{''.join(nav)}</ul></nav>
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
        print(
            f"{kickoff_clock(match['kickoff'])} {home_name} {len(home['matches'])} "
            f"tiri {len(home['shot_rows'])} | {away_name} {len(away['matches'])} tiri {len(away['shot_rows'])}"
        )
    print(OUT_PATH)


if __name__ == "__main__":
    main()

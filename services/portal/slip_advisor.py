"""Chiede una schedina e tiene, per ogni partita, il mercato migliore.

Le quote e gli xG arrivano dal feed. Se mancano, la partita esce.
Il testo spiega perché quel mercato sta sopra gli altri: non è il
certificato completo del validatore (classifica, H2H, rassegna).
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from services.analysis.combo_book_search import find_hidden_gems
from services.football.sixth_sense.lambda_context import MatchContext

ROME = ZoneInfo("Europe/Rome")
MAX_SELECTIONS = 3

_BOOK = {
    "Over 1.5": "odds_ft_over15",
    "Over 2.5": "odds_ft_over25",
    "Under 2.5": "odds_ft_under25",
    "Under 3.5": "odds_ft_under35",
}

_BANNED = (
    "serie b",
    "serie c",
    "2. bundesliga",
    "championship",
    "league one",
    "league two",
    "eerste",
    "primera nacional",
    "prim b",
    "ligue 2",
    "segunda",
    "tennis",
    "atp",
    "wta",
    "challenger",
    "women",
    "womens",
)

_ALLOWED = (
    "italy serie a",
    "england premier league",
    "spain la liga",
    "spain primera",
    "germany bundesliga",
    "france ligue 1",
    "portugal primeira",
    "portugal liga",
    "netherlands eredivisie",
    "scotland premiership",
    "belgium jupiler",
    "belgium pro league",
    "denmark superliga",
    "norway eliteserien",
    "sweden allsvenskan",
    "greece super league",
    "turkey super",
    "switzerland super",
    "brazil serie a",
    "argentina liga profesional",
    "champions league",
    "europa league",
    "conference league",
    "uefa nations league",
)


def league_allowed(name: str) -> bool:
    text = (name or "").lower()
    if not text or any(ban in text for ban in _BANNED):
        return False
    return any(allow in text for allow in _ALLOWED)


def advise_records(
    records: list[dict],
    now: datetime,
    context: MatchContext | None = None,
    query: str = "",
) -> dict:
    """Una selezione per partita, al massimo tre, ordinate per edge."""
    moment = _aware(now)
    flags = context or MatchContext()
    picked: list[dict] = []
    discarded: list[dict] = []
    asked = _lines(query)
    seen = 0
    for record in records:
        if asked and not _wanted(record, asked):
            continue
        reason = _reject_record(record, moment)
        if reason == "lega fuori perimetro" and not asked:
            continue
        seen += 1
        if reason:
            discarded.append({"match": _name(record), "reason": reason})
            continue
        choice = _best_market(record, flags)
        if choice is None:
            discarded.append({"match": _name(record), "reason": "nessun mercato nello sweet spot"})
            continue
        picked.append(choice)
    picked.sort(key=lambda row: row["_edge"], reverse=True)
    selections = picked[:MAX_SELECTIONS]
    for row in selections:
        row.pop("_edge", None)
    product = 1.0
    for row in selections:
        product *= float(row["odd"])
    message = _empty_message(bool(asked), seen, discarded) if not selections else ""
    return {
        "title": "Schedina richiesta",
        "message": message,
        "count": len(selections),
        "total_odds": f"{product:.2f}" if selections else "—",
        "selections": selections,
        "discarded": discarded[:8],
        "note": (
            "Mercato migliore sugli xG prematch FootyStats e sulle quote del feed, "
            "con i flag di sesto senso indicati. Non sostituisce il certificato completo "
            "del validatore: classifica, scontri diretti e rassegna stampa restano fuori."
        ),
    }


def _empty_message(asked: bool, seen: int, discarded: list[dict]) -> str:
    if asked and seen == 0:
        return "Nessuna partita del feed corrisponde ai nomi indicati."
    if seen == 0:
        return "Nel feed di questa data non ci sono partite di prima divisione ancora da giocare."
    reasons = {row["reason"] for row in discarded}
    if reasons == {"quote assenti nel feed"}:
        return "Le partite ci sono, ma il feed non ha ancora le quote."
    if reasons == {"xG prematch non certificati"}:
        return "Partita trovata, ma FootyStats non ha gli xG prematch: senza quelli non calcolo un mercato."
    if reasons == {"partita rinviata"}:
        return "Le partite trovate sono rinviate."
    if reasons == {"nessun mercato nello sweet spot"}:
        return "Nessun mercato nello sweet spot per le partite ammesse."
    return "Nessuna selezione. " + "; ".join(sorted(reasons))


def context_from_flags(flags: dict | None) -> MatchContext:
    raw = flags or {}
    return MatchContext(
        slow_start=bool(raw.get("slow_start")),
        rotation_risk=bool(raw.get("rotation")),
        low_motivation_home=bool(raw.get("low_motivation_home")),
        low_motivation_away=bool(raw.get("low_motivation_away")),
        corto_muso_home=bool(raw.get("corto_muso_home")),
        corto_muso_away=bool(raw.get("corto_muso_away")),
    )


def records_from_feed(rows: list[dict], leagues: dict[int, str]) -> list[dict]:
    records = []
    for row in rows:
        league = leagues.get(int(row.get("competition_id") or row.get("season") or 0), "")
        kickoff = _kickoff(row.get("date_unix"))
        odds = {}
        for market, field in _BOOK.items():
            price = _positive(row.get(field))
            if price is not None:
                odds[market] = price
        records.append(
            {
                "home": str(row.get("home_name") or ""),
                "away": str(row.get("away_name") or ""),
                "league": league,
                "kickoff": kickoff,
                "xg_home": _positive(row.get("team_a_xg_prematch")),
                "xg_away": _positive(row.get("team_b_xg_prematch")),
                "odds": odds,
                "status": str(row.get("status") or ""),
            }
        )
    return records


def _best_market(record: dict, context: MatchContext) -> dict | None:
    result = find_hidden_gems(
        record["xg_home"],
        record["xg_away"],
        record["odds"],
        context,
    )
    if not result.ranked:
        return None
    best = result.ranked[0]
    notes = list(result.notes)
    if not notes:
        notes.append("Nessun flag di sesto senso: i gol attesi restano quelli FootyStats.")
    notes.append(
        f"Migliore nello sweet spot: quota {best.book_odd:.2f}, "
        f"fair {best.fair_odd:.2f}, probabilità {best.probability:.1%}, edge {best.edge:+.1%}."
    )
    when = record["kickoff"].astimezone(ROME).strftime("%d/%m %H:%M") if record.get("kickoff") else "—"
    return {
        "match": _name(record),
        "league": record["league"],
        "when": when,
        "market": best.market,
        "odd": f"{best.book_odd:.2f}",
        "probability": f"{best.probability:.1%}",
        "fair_odd": f"{best.fair_odd:.2f}",
        "edge": f"{best.edge:+.1%}",
        "motivations": notes,
        "_edge": best.edge,
    }


def _reject_record(record: dict, now: datetime) -> str | None:
    status = (record.get("status") or "").lower()
    if status in {"canceled", "cancelled", "postponed", "abandoned"}:
        return "partita rinviata"
    if not league_allowed(record.get("league") or ""):
        return "lega fuori perimetro"
    kickoff = record.get("kickoff")
    if kickoff is None or kickoff <= now:
        return "kickoff assente o già passato"
    if not record.get("xg_home") or not record.get("xg_away"):
        return "xG prematch non certificati"
    if not record.get("odds"):
        return "quote assenti nel feed"
    return None


_ALIASES = {
    "italia": "italy",
    "belgio": "belgium",
    "francia": "france",
    "spagna": "spain",
    "germania": "germany",
    "portogallo": "portugal",
    "olanda": "netherlands",
    "paesi bassi": "netherlands",
    "inghilterra": "england",
    "turchia": "turkey",
    "svizzera": "switzerland",
    "scozia": "scotland",
    "galles": "wales",
    "irlanda": "ireland",
    "brasile": "brazil",
    "croazia": "croatia",
    "austria": "austria",
    "polonia": "poland",
    "ucraina": "ukraine",
    "danimarca": "denmark",
    "svezia": "sweden",
    "norvegia": "norway",
    "grecia": "greece",
    "serbia": "serbia",
}


def rows_on_date(rows: list[dict], date_str: str) -> list[dict]:
    kept = []
    for row in rows:
        kick = _kickoff(row.get("date_unix"))
        if kick is not None and kick.strftime("%Y-%m-%d") == date_str:
            kept.append(row)
    return kept


def _canon(text: str) -> str:
    cleaned = " ".join(text.lower().replace("-", " ").split())
    return _ALIASES.get(cleaned, cleaned)


def _wanted(record: dict, lines: list[str]) -> bool:
    blob = f"{_canon(record.get('home') or '')} {_canon(record.get('away') or '')}"
    for line in lines:
        parts = [part.strip() for part in line.replace(" contro ", " vs ").split(" vs ") if part.strip()]
        if len(parts) >= 2:
            left, right = _canon(parts[0]), _canon(parts[1])
            if left and right and left in blob and right in blob:
                return True
        elif _canon(line) in blob:
            return True
    return False


def _lines(query: str) -> list[str]:
    return [line.strip().lower() for line in (query or "").splitlines() if line.strip()]


def _name(record: dict) -> str:
    return f"{record.get('home') or '—'} vs {record.get('away') or '—'}"


def _kickoff(value: object) -> datetime | None:
    try:
        stamp = int(value)
    except (TypeError, ValueError):
        return None
    if stamp <= 0:
        return None
    return datetime.fromtimestamp(stamp, tz=timezone.utc).astimezone(ROME)


def _positive(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number <= 0:
        return None
    return number


def _aware(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=ROME)
    return moment.astimezone(ROME)

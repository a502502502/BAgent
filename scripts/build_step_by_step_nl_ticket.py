"""Nations League di oggi: una selezione per partita, probabilità dal motore.

I cataloghi più vecchi di 12 ore non si usano. Corner, cartellini e props
non entrano da questo script.
Validazione hard-gate tramite StrictTicketPipeline e audit Groq Cloud (openai/gpt-oss-120b).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from services.analysis.match_market_optimizer import MatchMarketOptimizer
from services.analysis.snai_goal_book import MAX_AGE_HOURS, best_goal_pick, catalog_age_hours, goal_odds_from_catalog
from services.betting.netwin_cache_reader import CachedMatch
from services.betting.strict_ticket_pipeline import MarketCandidate, StrictTicketPipeline

CEST = timezone(timedelta(hours=2))
TODAY = "2026-10-06"
OUT = ROOT / "reports" / "tickets" / "ticket_nations_league_passo_passo.json"
SOURCES = [
    ROOT / "reports" / "snai" / "2026-10-06-sera",
    ROOT / "reports" / "snai_nl" / "catalog",
    ROOT / "reports" / "snai" / "2026-10-06-fino-16",
    ROOT / "reports" / "snai",
]


def _catalogs() -> list[dict]:
    found: dict[str, dict] = {}
    for folder in SOURCES:
        if not folder.exists():
            continue
        for path in folder.glob("*.json"):
            if path.name in {"index.json", "picks.json"}:
                continue
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                continue
            catalog = raw
            catalog["_path"] = str(path)
            kickoff = catalog.get("kickoff_time") or ""
            match = catalog.get("match") or ""
            if TODAY not in kickoff or " - " not in match or "GIORNATA" in match:
                continue
            competition = str(catalog.get("competition") or "")
            in_daytime_folder = path.parent.name.startswith("2026-10-06")
            if in_daytime_folder and "nations" not in competition.lower():
                continue
            previous = found.get(match)
            if previous is None or (catalog_age_hours(catalog) or 99) < (catalog_age_hours(previous) or 99):
                found[match] = catalog
    return list(found.values())


def main() -> None:
    now = datetime.now(CEST)
    optimizer = MatchMarketOptimizer()
    picks = []
    skipped = []
    for catalog in _catalogs():
        age = catalog_age_hours(catalog, now)
        match = catalog["match"]
        if age is None or age > MAX_AGE_HOURS:
            skipped.append({"match": match, "reason": "catalogo più vecchio di 12 ore"})
            continue
        kickoff = datetime.strptime(catalog["kickoff_time"], "%Y-%m-%d %H:%M CEST").replace(tzinfo=CEST)
        if kickoff <= now:
            skipped.append({"match": match, "reason": "calcio d'inizio già passato"})
            continue
        home, away = match.split(" - ", 1)
        odds = goal_odds_from_catalog(catalog)
        cached = CachedMatch(
            match_name=f"{home.strip()} vs {away.strip()}",
            home_team=home.strip(),
            away_team=away.strip(),
            tournament="Nations League",
            kickoff=catalog["kickoff_time"],
            odds_dict={key: odds[key] for key in ("1", "X", "2", "Under 2.5", "Over 2.5") if key in odds},
        )
        xg_home, xg_away, _rho, source, _hn, _an = optimizer.lambdas_for(cached)
        pick = best_goal_pick(xg_home, xg_away, catalog)
        if pick is None:
            skipped.append({"match": match, "reason": "nessun mercato gol legale"})
            continue
        picks.append({
            "match": match,
            "kickoff_time": catalog["kickoff_time"],
            "market": pick.market,
            "odds": pick.book_odd,
            "probability": round(pick.probability, 3),
            "fair_odd": round(pick.fair_odd, 2),
            "edge": round(pick.edge, 3),
            "score": round(pick.score, 3),
            "verdict": pick.verdict,
            "xg_home": round(xg_home, 2),
            "xg_away": round(xg_away, 2),
            "lambda_source": source,
        })

    legs = sorted(picks, key=lambda row: row["score"], reverse=True)[:4]

    # Validazione con StrictTicketPipeline e GroqAuditor
    candidates = []
    for leg in legs:
        home, away = leg["match"].split(" - ", 1)
        c = MarketCandidate(
            match_name=f"{home.strip()} vs {away.strip()}",
            tournament="UEFA Nations League",
            market_name=leg["market"],
            bookmaker_odd=leg["odds"],
            sixth_sense_analysis=f"Match Nations League. xG {leg['xg_home']:.2f} vs {leg['xg_away']:.2f}. Fonte {leg['lambda_source']}.",
            xg_home=leg["xg_home"],
            xg_away=leg["xg_away"],
            kickoff_time=leg["kickoff_time"],
        )
        candidates.append(c)

    pipeline = StrictTicketPipeline()
    report = pipeline.validate_ticket(
        candidates,
        current_bankroll=100.0,
        ticket_title="Nations League 06/10/2026 - 4 Selezioni Certificate",
        enable_cloud_audit=True,
    )

    tot_odd = 1.0
    joint_p = 1.0
    for leg in legs:
        tot_odd *= leg["odds"]
        joint_p *= leg["probability"]

    tot_odd = round(tot_odd, 2)
    joint_p = round(joint_p, 3)
    joint_edge = round(joint_p * tot_odd - 1.0, 3)

    cloud_audit = report.cloud_audit or {}
    groq_approved = bool(cloud_audit.get("approved"))
    is_playable = bool(report.passed and groq_approved)

    # Stake 2.50 su bankroll 100 se EV congiunto e' negativo, altrimenti stake del validatore (max 2.50)
    stake = 2.50 if joint_edge <= 0 else min(report.recommended_stake, 2.50)

    payload = {
        "playable": is_playable,
        "name": "Schedina Nations League 4 Eventi Certificata (06/10/2026)",
        "generated_at": now.strftime("%Y-%m-%d %H:%M CEST"),
        "date_target": TODAY,
        "stake_eur": stake,
        "bankroll_reference": 100.0,
        "total_odds": tot_odd,
        "joint_probability": joint_p,
        "joint_edge": joint_edge,
        "potential_return_eur": round(stake * tot_odd, 2),
        "validator_passed": report.passed,
        "groq_verdict": "APPROVATA" if groq_approved else "BOCCIATA",
        "groq_audit_report": cloud_audit.get("critique", ""),
        "legs": legs,
        "skipped": skipped,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"gambe {len(legs)} | scartate {len(skipped)} | quota {tot_odd} | giocabile {is_playable}")
    for row in legs:
        print(f"{row['kickoff_time']} {row['match']} {row['market']} @{row['odds']} p={row['probability']}")


if __name__ == "__main__":
    main()

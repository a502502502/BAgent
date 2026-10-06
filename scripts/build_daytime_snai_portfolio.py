"""Portafoglio diurno: solo partite nel perimetro, con probabilità del motore.

U19, U21, U23, riserve, seconde divisioni e coppe minori non entrano.
La probabilità non si scrive a mano.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.analysis.match_market_optimizer import MatchMarketOptimizer
from services.analysis.snai_goal_book import MAX_AGE_HOURS, best_goal_pick, catalog_age_hours, goal_odds_from_catalog
from services.betting.netwin_cache_reader import CachedMatch

CEST = timezone(timedelta(hours=2))
OUT_OF_SCOPE = (
    "u19", "u21", "u23", "u20", "riserv", "reserve",
    "ii divisione", "iii divisione", "iv divisione", "vi divisione", "vii divisione",
    "league one", "league two", "vietnam", "bangladesh", "bengal", "albania",
    "segunda", "druga", "amichevol",
)
CATALOG = ROOT / "reports" / "snai" / "2026-10-06-fino-16"
OUT = ROOT / "reports" / "tickets" / "ticket_snai_daytime_45matches_portfolio.json"


def _out(match: str, competition: str) -> str | None:
    text = f"{match} {competition}".lower()
    for token in OUT_OF_SCOPE:
        if token in text:
            return f"fuori perimetro ({token})"
    return None


def main() -> None:
    now = datetime.now(CEST)
    index = json.loads((CATALOG / "index.json").read_text(encoding="utf-8"))
    optimizer = MatchMarketOptimizer()
    kept = []
    skipped = []
    for item in index:
        if item.get("error"):
            skipped.append({"match": item.get("match"), "reason": item["error"]})
            continue
        reason = _out(item.get("match") or "", item.get("competition") or "")
        kickoff = datetime.strptime(item["kickoff_time"], "%Y-%m-%d %H:%M CEST").replace(tzinfo=CEST)
        if reason:
            skipped.append({"match": item["match"], "reason": reason})
            continue
        if kickoff <= now:
            skipped.append({"match": item["match"], "reason": "calcio d'inizio già passato"})
            continue
        catalog = json.loads((ROOT / item["file"]).read_text(encoding="utf-8"))
        age = catalog_age_hours(catalog, now)
        if age is None or age > MAX_AGE_HOURS:
            skipped.append({"match": item["match"], "reason": "catalogo SNAI non fresco"})
            continue
        home, away = item["match"].split(" - ", 1)
        odds = goal_odds_from_catalog(catalog)
        match = CachedMatch(
            match_name=f"{home.strip()} vs {away.strip()}",
            home_team=home.strip(),
            away_team=away.strip(),
            tournament="Nations League" if "nations" in item["competition"].lower() else item["competition"],
            kickoff=item["kickoff_time"],
            odds_dict={key: odds[key] for key in ("1", "X", "2", "Under 2.5", "Over 2.5") if key in odds},
        )
        xg_home, xg_away, _rho, source, _hn, _an = optimizer.lambdas_for(match)
        if source not in {"dixon-coles", "poisson-shrinkage", "baseline-sanity", "baseline"}:
            skipped.append({"match": item["match"], "reason": f"lambda non certificata ({source})"})
            continue
        pick = best_goal_pick(xg_home, xg_away, catalog)
        if pick is None:
            skipped.append({"match": item["match"], "reason": "nessun mercato gol legale"})
            continue
        kept.append({
            "match": item["match"],
            "kickoff_time": item["kickoff_time"],
            "competition": item["competition"],
            "market": pick.market,
            "odds": pick.book_odd,
            "probability": round(pick.probability, 3),
            "fair_odd": pick.fair_odd,
            "edge": pick.edge,
            "score": pick.score,
            "verdict": pick.verdict,
            "xg_home": round(xg_home, 2),
            "xg_away": round(xg_away, 2),
            "lambda_source": source,
        })
    payload = {
        "playable": False,
        "reason": "Nessuna multipla: il validatore non certifica una selezione isolata di questo script.",
        "generated_at": now.strftime("%Y-%m-%d %H:%M CEST"),
        "selections": kept,
        "skipped": skipped,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"selezioni {len(kept)} | scartate {len(skipped)}")
    for row in kept:
        print(f"{row['kickoff_time']} {row['match']} {row['market']} @{row['odds']} p={row['probability']}")


if __name__ == "__main__":
    main()

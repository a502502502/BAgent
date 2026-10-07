"""
scripts/build_step_by_step_07ott_ticket.py — Schedina di Prova di Oggi (07/10/2026) con Nuovo Motore.

Legge i cataloghi scaricati da Cursor in reports/snai/2026-10-07,
applica MatchMarketOptimizer.lambdas_for, estrae le selezioni legali tramite best_goal_pick
(Regola #80, niente 1X2 secchi, niente Under 2.5/3.5 secchi),
valida con StrictTicketPipeline e sottopone ad audit Groq Cloud (openai/gpt-oss-120b).
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
from services.analysis.snai_goal_book import (
    best_goal_pick,
    catalog_age_hours,
    goal_odds_from_catalog,
)
from services.betting.netwin_cache_reader import CachedMatch
from services.betting.strict_ticket_pipeline import MarketCandidate, StrictTicketPipeline

CEST = timezone(timedelta(hours=2))
TODAY = "2026-10-07"
OUT = ROOT / "reports" / "tickets" / "ticket_07ott_prova_nuovo_motore.json"
SNAI_DIR = ROOT / "reports" / "snai" / "2026-10-07"


def load_today_catalogs(now: datetime) -> list[dict]:
    catalogs = []
    if not SNAI_DIR.exists():
        return catalogs

    for p in sorted(SNAI_DIR.glob("match--*.json")):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        data["_path"] = str(p)
        match = data.get("match") or ""
        kickoff_str = data.get("kickoff_time") or ""
        if not match or " - " not in match:
            continue
        try:
            k_dt = datetime.strptime(kickoff_str, "%Y-%m-%d %H:%M CEST").replace(tzinfo=CEST)
            if k_dt <= now:
                continue  # Gara già iniziata
        except Exception:
            continue
        catalogs.append(data)
    return catalogs


def main() -> int:
    now = datetime.now(CEST)
    optimizer = MatchMarketOptimizer()

    catalogs = load_today_catalogs(now)
    print(f"Cataloghi disponibili di oggi (calcio d'inizio futuro): {len(catalogs)}")

    picks = []
    skipped = []

    for cat in catalogs:
        match = cat["match"]
        k_str = cat["kickoff_time"]
        home, away = match.split(" - ", 1)
        odds = goal_odds_from_catalog(cat)
        cached = CachedMatch(
            match_name=f"{home.strip()} vs {away.strip()}",
            home_team=home.strip(),
            away_team=away.strip(),
            tournament=cat.get("competition") or "Oggi 07/10",
            kickoff=k_str,
            odds_dict={k: odds[k] for k in ("1", "X", "2", "Under 2.5", "Over 2.5") if k in odds},
        )
        xg_h, xg_a, _rho, source, _hn, _an = optimizer.lambdas_for(cached)
        pick = best_goal_pick(xg_h, xg_a, cat)

        if pick is None:
            skipped.append({"match": match, "reason": "nessun mercato gol legale"})
            continue

        picks.append({
            "match": match,
            "competition": cat.get("competition") or "SNAI Slate 07/10",
            "kickoff_time": k_str,
            "market": pick.market,
            "odds": pick.book_odd,
            "probability": round(pick.probability, 3),
            "fair_odd": round(pick.fair_odd, 2),
            "edge": round(pick.edge, 3),
            "score": round(pick.score, 3),
            "verdict": pick.verdict,
            "xg_home": round(xg_h, 2),
            "xg_away": round(xg_a, 2),
            "lambda_source": source,
        })

    # Ordina per score decrescente e prendi max 4 selezioni indipendenti
    legs = sorted(picks, key=lambda row: row["score"], reverse=True)[:4]

    if not legs:
        print("Nessuna gamba selezionata per il ticket.")
        return 1

    # Validazione tramite StrictTicketPipeline e GroqAuditor
    candidates = []
    for leg in legs:
        home, away = leg["match"].split(" - ", 1)
        c = MarketCandidate(
            match_name=f"{home.strip()} vs {away.strip()}",
            tournament=leg["competition"],
            market_name=leg["market"],
            bookmaker_odd=leg["odds"],
            sixth_sense_analysis=f"Gara di oggi. xG {leg['xg_home']:.2f} vs {leg['xg_away']:.2f}. Fonte {leg['lambda_source']}.",
            xg_home=leg["xg_home"],
            xg_away=leg["xg_away"],
            kickoff_time=leg["kickoff_time"],
        )
        candidates.append(c)

    pipeline = StrictTicketPipeline()
    report = pipeline.validate_ticket(
        candidates,
        current_bankroll=100.0,
        ticket_title="Schedina di Prova Nuovo Motore (07/10/2026)",
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

    # Stake fisso 2.50 EUR su bankroll 100 se EV congiunto è negativo, altrimenti stake del validatore (max 2.50)
    stake = 2.50 if joint_edge <= 0 else min(report.recommended_stake, 2.50)

    payload = {
        "playable": is_playable,
        "name": "Schedina di Prova Nuovo Motore SNAI (07/10/2026)",
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

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n" + "=" * 80)
    print("SCHEDINA DI PROVA GENERATA CON IL NUOVO MOTORE (07/10/2026)")
    print("=" * 80)
    print(f"Stato: {'GIOCABILE (PLAYABLE)' if is_playable else 'NON OPERATIVA (PLAYABLE FALSE)'}")
    print(f"Quota Totale: {tot_odd} | P Congiunta: {joint_p*100:.1f}% | Edge: {joint_edge*100:+.1f}% | Stake: {stake:.2f} EUR")
    print(f"Verdetto Groq: {payload['groq_verdict']}")
    print("-" * 80)
    for idx, leg in enumerate(legs, 1):
        print(f"Leg {idx}: {leg['match']}")
        print(f"  Calcio d'inizio: {leg['kickoff_time']}")
        print(f"  Mercato: {leg['market']} @ {leg['odds']}")
        print(f"  Modello: P={leg['probability']*100:.1f}% | Fair={leg['fair_odd']} | Edge={leg['edge']*100:+.1f}% | xG={leg['xg_home']} vs {leg['xg_away']}")
        print("-" * 80)

    print(f"File salvato in: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

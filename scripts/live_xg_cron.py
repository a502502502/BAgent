#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scripts/live_xg_cron.py — Scanner & Cron Real-Time Statistiche e xG Live (Flashscore Ninja).

Architettura:
1. Scarica il tabellone live da FlashscoreLiveEngine (f_1_0_1_it_1) in ~0.3s.
2. Filtra le partite del perimetro (escludendo giovanili, amichevoli, riserve, femminile).
3. Arricchisce in parallelo (ThreadPoolExecutor) ogni match live con il feed telemetrico
   `df_st_1_<match_id>` (xG live, Tiri Totali, Tiri in Porta, Corner, Cartellini).
4. Incrocia i dati con gli xG pre-match certificati in `data/bagent.db` e calcola:
   - ΔxG Live = xG_live - Gol_attuali (misura la compressione statistica / sottoprestazione)
   - λ_residuo ibrido (Poisson condizionato ai minuti restanti + ritmo xG/minuto + rossi)
   - P(≥1 gol residuo), P(Squadra segna ancora), P(≤1 gol residuo / Under Lock)
5. Valuta i 4 Trigger Quantitativi Live xG:
   - TRIGGER A: 0-0 High-xG Unlock (35'-72', 0-0 con xG_tot ≥ 1.35 o assedio balistico)
   - TRIGGER B: Assedio Squadra con Deficit ΔxG ≥ +0.85 (15'-78', sotto o pari ma dominante)
   - TRIGGER C: Pressione Finale / Compressione xG (62'-85', scarto ≤ 1 gol e ΔxG_tot ≥ +1.15)
   - TRIGGER D: Blocco Tattico Under Lock (48'-75', xG_tot ≤ 0.55 e SOT ≤ 2)
6. Salva i segnali in `data/live_xg_signals.json` e invia alert Telegram deduplicati
   (stake max 3% bankroll come da GEMINI.md).

Uso:
  .venv/bin/python scripts/live_xg_cron.py                  # Esecuzione singola (cron / CLI)
  .venv/bin/python scripts/live_xg_cron.py --telegram       # Invia anche su Telegram se ci sono trigger
  .venv/bin/python scripts/live_xg_cron.py --loop --interval 180  # Daemon continuo ogni 3 minuti
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import sqlite3
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.football.external.sources.flashscore_live import FlashscoreLiveEngine, _feed_int, _feed_minute
from services.telegram.telegram_sentinel import TelegramSentinel

DB_PATH = ROOT / "data" / "bagent.db"
SIGNALS_PATH = ROOT / "data" / "live_xg_signals.json"
ALERT_CACHE_PATH = ROOT / "data" / "live_xg_alert_cache.json"

EXCLUDED_TOKENS = (
    "u17", "u18", "u19", "u20", "u21", "u23",
    "women", "donne", "femminile", " (w)", " w ",
    "riserve", "reserve", "youth", "primavera", "amichevol",
)


@dataclass
class LiveXGMatchReport:
    match_id: str
    league: str
    home: str
    away: str
    minute: int
    status: str
    home_goals: int
    away_goals: int
    ht_score: str
    home_xg: Optional[float]
    away_xg: Optional[float]
    total_xg: Optional[float]
    delta_xg_home: Optional[float]
    delta_xg_away: Optional[float]
    delta_xg_total: Optional[float]
    home_shots: int
    away_shots: int
    home_sot: int
    away_sot: int
    home_corners: int
    away_corners: int
    home_yellow: int
    away_yellow: int
    home_red: int
    away_red: int
    pre_xg_home: float
    pre_xg_away: float
    lambda_rem_home: float
    lambda_rem_away: float
    lambda_rem_total: float
    prob_at_least_1_more_goal: float
    prob_home_next_goal: float
    prob_away_next_goal: float
    prob_max_1_more_goal: float


@dataclass
class LiveXGSignal:
    match_id: str
    league: str
    match_name: str
    minute: int
    score: str
    trigger_code: str
    trigger_label: str
    recommended_market: str
    min_fair_odds: float
    prob_estimate: float
    confidence: str
    xg_summary: str
    stats_summary: str
    rationale: str
    max_stake_pct: float = 3.0
    created_at: str = ""


def _is_valid_senior_match(row: Dict[str, Any]) -> bool:
    blob = f"{row.get('league', '')} {row.get('home', '')} {row.get('away', '')}".lower()
    return not any(tok in blob for tok in EXCLUDED_TOKENS)


def _load_prematch_xg_lookup(db_path: Path) -> Dict[str, Tuple[float, float]]:
    """Carica (xg_for, xg_against) per squadra da team_telemetry_2026 in data/bagent.db."""
    lookup: Dict[str, Tuple[float, float]] = {}
    if not db_path.exists():
        return lookup
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA wal_checkpoint(PASSIVE);")
        cur.execute(
            """
            SELECT LOWER(team_name), AVG(xg_for), AVG(xg_against)
            FROM team_telemetry_2026
            GROUP BY LOWER(team_name)
            """
        )
        for name, xgf, xga in cur.fetchall():
            if name and xgf is not None and xga is not None:
                lookup[str(name).strip()] = (float(xgf), float(xga))
        conn.close()
    except Exception:
        pass
    return lookup


def _resolve_team_prematch_xg(
    home: str,
    away: str,
    lookup: Dict[str, Tuple[float, float]],
) -> Tuple[float, float]:
    """Stima xG pre-match di casa e trasferta dallo storico 2026 o media neutra (1.35, 1.12)."""
    def _find(team_name: str) -> Optional[Tuple[float, float]]:
        t = team_name.lower().strip()
        if t in lookup:
            return lookup[t]
        for k, val in lookup.items():
            if t in k or k in t:
                return val
        return None

    h_stats = _find(home)
    a_stats = _find(away)
    if h_stats and a_stats:
        pre_h = max(0.55, min(2.80, (h_stats[0] + a_stats[1]) / 2.0 * 1.06))
        pre_a = max(0.45, min(2.50, (a_stats[0] + h_stats[1]) / 2.0 * 0.94))
        return round(pre_h, 2), round(pre_a, 2)
    if h_stats:
        return round(h_stats[0], 2), round(h_stats[1], 2)
    if a_stats:
        return round(a_stats[1], 2), round(a_stats[0], 2)
    return 1.35, 1.12


def _compute_hybrid_residual_lambdas(
    minute: int,
    home_xg: Optional[float],
    away_xg: Optional[float],
    home_shots: int,
    away_shots: int,
    home_sot: int,
    away_sot: int,
    home_red: int,
    away_red: int,
    pre_xg_home: float,
    pre_xg_away: float,
) -> Tuple[float, float]:
    """
    Calcola (lambda_residuo_home, lambda_residuo_away) combinando:
    - 30% aspettativa pre-match residua
    - 70% ritmo xG live osservato (o proxy balistico tiri/SOT se xG non presente)
    - aggiustamento cartellini rossi
    """
    eff_min = max(8, min(92, minute))
    rem_fraction = max(0.03, (94.0 - eff_min) / 90.0)

    if home_xg is not None and away_xg is not None:
        live_pace_h = (home_xg / eff_min) * 90.0
        live_pace_a = (away_xg / eff_min) * 90.0
    else:
        # Proxy balistico se il campionato non espone xG ma solo Tiri e SOT
        est_xg_h = home_sot * 0.30 + max(0, home_shots - home_sot) * 0.06
        est_xg_a = away_sot * 0.30 + max(0, away_shots - away_sot) * 0.06
        live_pace_h = (est_xg_h / eff_min) * 90.0
        live_pace_a = (est_xg_a / eff_min) * 90.0

    # Peso crescente al dato live col passare dei minuti (dal 40% al 15' fino al 78% dopo il 60')
    w_live = min(0.78, max(0.40, eff_min / 85.0))
    w_pre = 1.0 - w_live

    blended_90_h = w_pre * pre_xg_home + w_live * live_pace_h
    blended_90_a = w_pre * pre_xg_away + w_live * live_pace_a

    lam_h = blended_90_h * rem_fraction
    lam_a = blended_90_a * rem_fraction

    # Fattore espulsioni
    if home_red > away_red:
        lam_h *= 0.68
        lam_a *= 1.28
    elif away_red > home_red:
        lam_a *= 0.68
        lam_h *= 1.28

    return round(max(0.04, lam_h), 3), round(max(0.04, lam_a), 3)


def evaluate_live_triggers(report: LiveXGMatchReport) -> List[LiveXGSignal]:
    """Valuta i 4 Trigger Quantitativi Live xG su una singola partita arricchita."""
    signals: List[LiveXGSignal] = []
    m = report.minute
    if m < 12 or m > 87:
        return signals

    match_name = f"{report.home} vs {report.away}"
    score_str = f"{report.home_goals}-{report.away_goals}"
    tot_goals = report.home_goals + report.away_goals
    tot_shots = report.home_shots + report.away_shots
    tot_sot = report.home_sot + report.away_sot

    xg_h = report.home_xg
    xg_a = report.away_xg
    xg_tot = report.total_xg
    d_xg_h = report.delta_xg_home
    d_xg_a = report.delta_xg_away
    d_xg_tot = report.delta_xg_total

    xg_str = (
        f"xG Live {xg_h:.2f} - {xg_a:.2f} (Tot {xg_tot:.2f} | ΔxG {d_xg_tot:+.2f})"
        if xg_h is not None and xg_a is not None and xg_tot is not None and d_xg_tot is not None
        else f"xG Proxy (Pre {report.pre_xg_home:.2f}-{report.pre_xg_away:.2f})"
    )
    stats_str = (
        f"Tiri {report.home_shots}-{report.away_shots} (SOT {report.home_sot}-{report.away_sot}) | "
        f"Corner {report.home_corners}-{report.away_corners} | "
        f"Rosso {report.home_red}-{report.away_red}"
    )
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # -------------------------------------------------------------------------
    # TRIGGER A: 0-0 HIGH-xG UNLOCK (Min 35' - 72', Punteggio 0-0)
    # -------------------------------------------------------------------------
    if report.home_goals == 0 and report.away_goals == 0 and 35 <= m <= 72:
        high_xg_00 = (xg_tot is not None and xg_tot >= 1.30) or (
            xg_tot is not None and xg_tot >= 1.05 and tot_sot >= 5 and tot_shots >= 14
        )
        if high_xg_00 and report.prob_at_least_1_more_goal >= 0.64:
            p_est = report.prob_at_least_1_more_goal
            fair_q = round(1.0 / max(0.05, p_est), 2)
            # Se una squadra concentra ≥ 70% degli xG, segnala anche Over 0.5 Squadra
            if xg_h is not None and xg_h >= 0.95 and report.home_sot >= 3:
                mkt = f"Over 0.5 Live (o Over 0.5 {report.home} Live)"
            elif xg_a is not None and xg_a >= 0.95 and report.away_sot >= 3:
                mkt = f"Over 0.5 Live (o Over 0.5 {report.away} Live)"
            else:
                mkt = "Over 0.5 Gol Totale Live"
            signals.append(
                LiveXGSignal(
                    match_id=report.match_id,
                    league=report.league,
                    match_name=match_name,
                    minute=m,
                    score=score_str,
                    trigger_code="TRIGGER_A_00_UNLOCK",
                    trigger_label="🔓 TRIGGER A — 0-0 High-xG Unlock",
                    recommended_market=mkt,
                    min_fair_odds=max(1.35, round(fair_q * 1.05, 2)),
                    prob_estimate=round(p_est * 100, 1),
                    confidence="ALTA" if (xg_tot or 0) >= 1.60 else "MEDIA-ALTA",
                    xg_summary=xg_str,
                    stats_summary=stats_str,
                    rationale=(
                        f"Match bloccato sullo 0-0 al {m}' ma con {xg_tot:.2f} xG già prodotti "
                        f"e {tot_sot} tiri nello specchio. λ residuo = {report.lambda_rem_total:.2f} "
                        f"(P ≥ 1 gol = {p_est*100:.1f}%)."
                    ),
                    created_at=now_iso,
                )
            )

    # -------------------------------------------------------------------------
    # TRIGGER B: ASSEDIO SQUADRA CON DEFICIT ΔxG ≥ +0.85 (Min 15' - 78')
    # -------------------------------------------------------------------------
    if 15 <= m <= 78 and xg_h is not None and xg_a is not None:
        # Caso 1: Casa sotto o in pareggio ma in forte credito xG
        if (
            report.home_goals <= report.away_goals
            and d_xg_h is not None
            and d_xg_h >= 0.85
            and xg_h >= 1.05
            and (report.home_sot >= 3 or report.home_shots >= 9)
            and report.home_red == 0
        ):
            p_h = report.prob_home_next_goal
            fair_q = round(1.0 / max(0.05, p_h), 2)
            mkt = (
                f"Over {report.home_goals}.5 Gol {report.home} Live / 1X Live"
                if report.home_goals < report.away_goals
                else f"Over {report.home_goals}.5 Gol {report.home} Live (Prossimo Gol 1)"
            )
            signals.append(
                LiveXGSignal(
                    match_id=report.match_id,
                    league=report.league,
                    match_name=match_name,
                    minute=m,
                    score=score_str,
                    trigger_code="TRIGGER_B_HOME_SIEGE",
                    trigger_label=f"🔥 TRIGGER B — Assedio {report.home} (ΔxG +{d_xg_h:.2f})",
                    recommended_market=mkt,
                    min_fair_odds=max(1.45, round(fair_q * 1.05, 2)),
                    prob_estimate=round(p_h * 100, 1),
                    confidence="ALTA" if d_xg_h >= 1.15 else "MEDIA-ALTA",
                    xg_summary=xg_str,
                    stats_summary=stats_str,
                    rationale=(
                        f"{report.home} sul {score_str} al {m}' ma domina con {xg_h:.2f} xG "
                        f"(ΔxG +{d_xg_h:.2f}), {report.home_shots} tiri ({report.home_sot} SOT) e "
                        f"{report.home_corners} corner. P({report.home} segna ancora) = {p_h*100:.1f}%."
                    ),
                    created_at=now_iso,
                )
            )

        # Caso 2: Trasferta sotto o in pareggio ma in forte credito xG
        if (
            report.away_goals <= report.home_goals
            and d_xg_a is not None
            and d_xg_a >= 0.85
            and xg_a >= 1.05
            and (report.away_sot >= 3 or report.away_shots >= 9)
            and report.away_red == 0
        ):
            p_a = report.prob_away_next_goal
            fair_q = round(1.0 / max(0.05, p_a), 2)
            mkt = (
                f"Over {report.away_goals}.5 Gol {report.away} Live / X2 Live"
                if report.away_goals < report.home_goals
                else f"Over {report.away_goals}.5 Gol {report.away} Live (Prossimo Gol 2)"
            )
            signals.append(
                LiveXGSignal(
                    match_id=report.match_id,
                    league=report.league,
                    match_name=match_name,
                    minute=m,
                    score=score_str,
                    trigger_code="TRIGGER_B_AWAY_SIEGE",
                    trigger_label=f"🔥 TRIGGER B — Assedio {report.away} (ΔxG +{d_xg_a:.2f})",
                    recommended_market=mkt,
                    min_fair_odds=max(1.45, round(fair_q * 1.05, 2)),
                    prob_estimate=round(p_a * 100, 1),
                    confidence="ALTA" if d_xg_a >= 1.15 else "MEDIA-ALTA",
                    xg_summary=xg_str,
                    stats_summary=stats_str,
                    rationale=(
                        f"{report.away} sul {score_str} al {m}' ma domina con {xg_a:.2f} xG "
                        f"(ΔxG +{d_xg_a:.2f}), {report.away_shots} tiri ({report.away_sot} SOT) e "
                        f"{report.away_corners} corner. P({report.away} segna ancora) = {p_a*100:.1f}%."
                    ),
                    created_at=now_iso,
                )
            )

    # -------------------------------------------------------------------------
    # TRIGGER C: PRESSIONE FINALE / DEFICIT xG ESTREMO (Min 62' - 85')
    # -------------------------------------------------------------------------
    if (
        62 <= m <= 85
        and abs(report.home_goals - report.away_goals) <= 1
        and d_xg_tot is not None
        and d_xg_tot >= 1.10
        and report.prob_at_least_1_more_goal >= 0.55
    ):
        p_goal = report.prob_at_least_1_more_goal
        fair_q = round(1.0 / max(0.05, p_goal), 2)
        line = tot_goals + 0.5
        signals.append(
            LiveXGSignal(
                match_id=report.match_id,
                league=report.league,
                match_name=match_name,
                minute=m,
                score=score_str,
                trigger_code="TRIGGER_C_LATE_PRESSURE",
                trigger_label=f"⚡ TRIGGER C — Compressione xG Finale (ΔxG +{d_xg_tot:.2f})",
                recommended_market=f"Over {line:.1f} Gol Live",
                min_fair_odds=max(1.50, round(fair_q * 1.05, 2)),
                prob_estimate=round(p_goal * 100, 1),
                confidence="ALTA" if d_xg_tot >= 1.45 else "MEDIA-ALTA",
                xg_summary=xg_str,
                stats_summary=stats_str,
                rationale=(
                    f"Partita in bilico ({score_str}) al {m}' con deficit complessivo "
                    f"ΔxG = +{d_xg_tot:.2f} ({xg_tot:.2f} xG prodotti contro {tot_goals} gol). "
                    f"P(Over {line:.1f} Live) = {p_goal*100:.1f}%."
                ),
                created_at=now_iso,
            )
        )

    # -------------------------------------------------------------------------
    # TRIGGER D: BLOCCO TATTICO / UNDER LOCK (Min 48' - 76')
    # -------------------------------------------------------------------------
    if (
        48 <= m <= 76
        and xg_tot is not None
        and xg_tot <= 0.55
        and tot_sot <= 2
        and report.home_red == 0
        and report.away_red == 0
        and report.prob_max_1_more_goal >= 0.80
    ):
        p_under = report.prob_max_1_more_goal
        fair_q = round(1.0 / max(0.05, p_under), 2)
        line = tot_goals + 1.5 if m < 68 else tot_goals + 0.5
        signals.append(
            LiveXGSignal(
                match_id=report.match_id,
                league=report.league,
                match_name=match_name,
                minute=m,
                score=score_str,
                trigger_code="TRIGGER_D_UNDER_LOCK",
                trigger_label=f"🧊 TRIGGER D — Under Lock (xG Tot {xg_tot:.2f})",
                recommended_market=f"Under {line:.1f} Gol Live",
                min_fair_odds=max(1.28, round(fair_q * 1.04, 2)),
                prob_estimate=round(p_under * 100, 1),
                confidence="ALTA",
                xg_summary=xg_str,
                stats_summary=stats_str,
                rationale=(
                    f"Ritmo offensivo nullo al {m}' ({score_str}): soli {xg_tot:.2f} xG totali "
                    f"e {tot_sot} tiri nello specchio. λ residuo = {report.lambda_rem_total:.2f} "
                    f"(P ≤ 1 gol residuo = {p_under*100:.1f}%)."
                ),
                created_at=now_iso,
            )
        )

    return signals


def _load_alert_cache() -> Dict[str, float]:
    if not ALERT_CACHE_PATH.exists():
        return {}
    try:
        return json.loads(ALERT_CACHE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_alert_cache(cache: Dict[str, float]) -> None:
    now_ts = time.time()
    cleaned = {k: v for k, v in cache.items() if now_ts - v < 7200}
    ALERT_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ALERT_CACHE_PATH.write_text(json.dumps(cleaned, indent=2), encoding="utf-8")


def scan_live_xg_once(send_telegram: bool = False, cooldown_sec: int = 1200) -> Tuple[List[LiveXGMatchReport], List[LiveXGSignal]]:
    t0 = time.perf_counter()
    engine = FlashscoreLiveEngine()
    all_rows = engine.fetch_feed()
    live_rows = [
        r for r in all_rows
        if r.get("status_code") in engine.LIVE_STATUS and _is_valid_senior_match(r)
    ]

    pre_lookup = _load_prematch_xg_lookup(DB_PATH)

    def _enrich_row(row: Dict[str, Any]) -> Optional[LiveXGMatchReport]:
        mid = str(row.get("match_id") or "")
        h_goals = _feed_int(row.get("home_score"))
        a_goals = _feed_int(row.get("away_score"))
        if h_goals is None or a_goals is None:
            return None
        minute = _feed_minute(str(row.get("period") or ""), str(row.get("status_code") or ""))
        st = engine.fetch_match_stats(mid)

        xg_h = st.get("home_xg")
        xg_a = st.get("away_xg")
        tot_xg = round(xg_h + xg_a, 2) if (xg_h is not None and xg_a is not None) else None
        d_xg_h = round(xg_h - h_goals, 2) if xg_h is not None else None
        d_xg_a = round(xg_a - a_goals, 2) if xg_a is not None else None
        d_xg_tot = round(tot_xg - (h_goals + a_goals), 2) if tot_xg is not None else None

        h_shots = int(st.get("home_shots") or 0)
        a_shots = int(st.get("away_shots") or 0)
        h_sot = int(st.get("home_sot") or 0)
        a_sot = int(st.get("away_sot") or 0)
        h_cor = int(st.get("home_corners") or 0)
        a_cor = int(st.get("away_corners") or 0)
        h_yel = int(st.get("home_yellow") or _feed_int(row.get("home_yellow")) or 0)
        a_yel = int(st.get("away_yellow") or _feed_int(row.get("away_yellow")) or 0)
        h_red = int(_feed_int(row.get("home_red")) or 0)
        a_red = int(_feed_int(row.get("away_red")) or 0)

        pre_h, pre_a = _resolve_team_prematch_xg(row["home"], row["away"], pre_lookup)
        lam_h, lam_a = _compute_hybrid_residual_lambdas(
            minute=minute,
            home_xg=xg_h,
            away_xg=xg_a,
            home_shots=h_shots,
            away_shots=a_shots,
            home_sot=h_sot,
            away_sot=a_sot,
            home_red=h_red,
            away_red=a_red,
            pre_xg_home=pre_h,
            pre_xg_away=pre_a,
        )
        lam_tot = round(lam_h + lam_a, 3)
        p_at_least_1 = 1.0 - math.exp(-lam_tot)
        p_h_next = 1.0 - math.exp(-lam_h)
        p_a_next = 1.0 - math.exp(-lam_a)
        p_max_1 = (1.0 + lam_tot) * math.exp(-lam_tot)

        return LiveXGMatchReport(
            match_id=mid,
            league=row.get("league", ""),
            home=row["home"],
            away=row["away"],
            minute=minute,
            status=row.get("status", ""),
            home_goals=h_goals,
            away_goals=a_goals,
            ht_score=row.get("ht_score", ""),
            home_xg=xg_h,
            away_xg=xg_a,
            total_xg=tot_xg,
            delta_xg_home=d_xg_h,
            delta_xg_away=d_xg_a,
            delta_xg_total=d_xg_tot,
            home_shots=h_shots,
            away_shots=a_shots,
            home_sot=h_sot,
            away_sot=a_sot,
            home_corners=h_cor,
            away_corners=a_cor,
            home_yellow=h_yel,
            away_yellow=a_yel,
            home_red=h_red,
            away_red=a_red,
            pre_xg_home=pre_h,
            pre_xg_away=pre_a,
            lambda_rem_home=lam_h,
            lambda_rem_away=lam_a,
            lambda_rem_total=lam_tot,
            prob_at_least_1_more_goal=round(p_at_least_1, 4),
            prob_home_next_goal=round(p_h_next, 4),
            prob_away_next_goal=round(p_a_next, 4),
            prob_max_1_more_goal=round(p_max_1, 4),
        )

    reports: List[LiveXGMatchReport] = []
    if live_rows:
        with ThreadPoolExecutor(max_workers=10) as pool:
            for rep in pool.map(_enrich_row, live_rows):
                if rep is not None:
                    reports.append(rep)

    # Ordina mettendo in cima le partite con xG live disponibili e |ΔxG| maggiore
    reports.sort(
        key=lambda r: (
            r.total_xg is not None,
            abs(r.delta_xg_total or 0.0),
            (r.home_shots + r.away_shots),
        ),
        reverse=True,
    )

    signals: List[LiveXGSignal] = []
    for rep in reports:
        signals.extend(evaluate_live_triggers(rep))

    elapsed = time.perf_counter() - t0
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Salva snapshot JSON per dashboard / audit
    SIGNALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "scanned_at": now_str,
        "elapsed_seconds": round(elapsed, 2),
        "live_matches_count": len(reports),
        "signals_count": len(signals),
        "signals": [asdict(s) for s in signals],
        "live_telemetry": [asdict(r) for r in reports if r.total_xg is not None or (r.home_shots + r.away_shots) > 0],
    }
    SIGNALS_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # Stampa cruscotto terminale
    print("=" * 105)
    print(f"📡 BAGENT LIVE xG & TELEMETRY SCANNER — {now_str} ({elapsed:.2f}s) | Match Live: {len(reports)}")
    print("=" * 105)

    active_with_stats = [r for r in reports if r.total_xg is not None or (r.home_shots + r.away_shots) > 0]
    if not active_with_stats:
        print("Nessuna partita live con telemetria xG/Tiri attiva in questo istante.")
    else:
        print(
            f"{'MIN':<5} | {'PARTITA':<36} | {'GOL':<5} | {'xG LIVE (H-A)':<15} | "
            f"{'ΔxG':<7} | {'TIRI (SOT)':<13} | {'COR':<5} | {'P(≥1G)':<6}"
        )
        print("-" * 105)
        for r in active_with_stats:
            min_lbl = f"{r.minute}'" if r.status != "Intervallo" else "HT"
            match_lbl = f"{r.home} - {r.away}"[:36]
            score_lbl = f"{r.home_goals}-{r.away_goals}"
            if r.home_xg is not None and r.away_xg is not None:
                xg_lbl = f"{r.home_xg:.2f} - {r.away_xg:.2f}"
                dxg_lbl = f"{r.delta_xg_total:+.2f}"
            else:
                xg_lbl = "n/d (solo tiri)"
                dxg_lbl = "  -  "
            shots_lbl = f"{r.home_shots}-{r.away_shots} ({r.home_sot}-{r.away_sot})"
            cor_lbl = f"{r.home_corners}-{r.away_corners}"
            p1_lbl = f"{r.prob_at_least_1_more_goal*100:.0f}%"
            print(
                f"{min_lbl:<5} | {match_lbl:<36} | {score_lbl:<5} | {xg_lbl:<15} | "
                f"{dxg_lbl:<7} | {shots_lbl:<13} | {cor_lbl:<5} | {p1_lbl:<6}"
            )

    print("\n" + "=" * 105)
    if not signals:
        print("🟡 NESSUN TRIGGER LIVE ATTIVO IN QUESTO MINUTO (Soglie di sicurezza xG/SOT rispettate).")
    else:
        print(f"🚨 {len(signals)} SEGNALI LIVE xG ATTIVATI (Stake Max: 3.0% Bankroll — Regola Live GEMINI.md):")
        print("-" * 105)
        for s in signals:
            print(f"  {s.trigger_label}")
            print(f"  ⚽ {s.match_name} ({s.league}) — Minuto {s.minute}' | Risultato: {s.score}")
            print(f"  📊 {s.xg_summary} | {s.stats_summary}")
            print(f"  🎯 Mercato: {s.recommended_market} | Quota Minima Fair (+5%): @{s.min_fair_odds:.2f} | Stima P: {s.prob_estimate:.1f}% [{s.confidence}]")
            print(f"  💡 Motivo: {s.rationale}")
            print("-" * 105)

    # Notifica Telegram con deduplicazione anti-spam
    if send_telegram and signals:
        cache = _load_alert_cache()
        now_ts = time.time()
        new_signals = []
        for s in signals:
            cache_key = f"{s.match_id}::{s.trigger_code}"
            if now_ts - cache.get(cache_key, 0.0) >= cooldown_sec:
                new_signals.append(s)
                cache[cache_key] = now_ts
        if new_signals:
            sentinel = TelegramSentinel()
            lines = ["🚨 *BAGENT LIVE xG SNIPER* 🚨\n"]
            for s in new_signals:
                lines.append(
                    f"*{s.trigger_label}*\n"
                    f"⚽ *{s.match_name}* ({s.minute}' — `{s.score}`)\n"
                    f"📊 `{s.xg_summary}`\n"
                    f"🎯 *{s.recommended_market}* (Quota min `@ {s.min_fair_odds:.2f}` | P `{s.prob_estimate:.1f}%`)\n"
                    f"💰 Stake max: `{s.max_stake_pct:.1f}%` bankroll\n"
                )
            sentinel._send_raw("\n".join(lines))
            _save_alert_cache(cache)

    return reports, signals


def main() -> None:
    parser = argparse.ArgumentParser(description="BAgent Live xG & Telemetry Cron Scanner")
    parser.add_argument("--telegram", action="store_true", help="Invia alert Telegram sui nuovi trigger live")
    parser.add_argument("--loop", action="store_true", help="Esegui in loop continuo")
    parser.add_argument("--interval", type=int, default=180, help="Intervallo di scansione in secondi (default: 180s)")
    parser.add_argument("--demo", action="store_true", help="Simula i 4 Trigger Quantitativi Live xG per verifica")
    args = parser.parse_args()

    if args.demo:
        demo_reports = [
            LiveXGMatchReport(
                match_id="demo1", league="SERIE A", home="Inter", away="Torino",
                minute=54, status="2° Tempo", home_goals=0, away_goals=0, ht_score="0-0",
                home_xg=1.42, away_xg=0.31, total_xg=1.73, delta_xg_home=1.42, delta_xg_away=0.31, delta_xg_total=1.73,
                home_shots=14, away_shots=3, home_sot=6, away_sot=1, home_corners=7, away_corners=1,
                home_yellow=1, away_yellow=2, home_red=0, away_red=0, pre_xg_home=1.85, pre_xg_away=0.75,
                lambda_rem_home=0.92, lambda_rem_away=0.22, lambda_rem_total=1.14,
                prob_at_least_1_more_goal=0.680, prob_home_next_goal=0.601, prob_away_next_goal=0.197, prob_max_1_more_goal=0.683,
            ),
            LiveXGMatchReport(
                match_id="demo2", league="PREMIER LEAGUE", home="Arsenal", away="Fulham",
                minute=61, status="2° Tempo", home_goals=0, away_goals=1, ht_score="0-1",
                home_xg=1.88, away_xg=0.29, total_xg=2.17, delta_xg_home=1.88, delta_xg_away=-0.71, delta_xg_total=1.17,
                home_shots=16, away_shots=2, home_sot=7, away_sot=1, home_corners=9, away_corners=0,
                home_yellow=1, away_yellow=3, home_red=0, away_red=0, pre_xg_home=2.05, pre_xg_away=0.70,
                lambda_rem_home=0.88, lambda_rem_away=0.18, lambda_rem_total=1.06,
                prob_at_least_1_more_goal=0.654, prob_home_next_goal=0.585, prob_away_next_goal=0.165, prob_max_1_more_goal=0.713,
            ),
        ]
        for r in demo_reports:
            for s in evaluate_live_triggers(r):
                print(f"{s.trigger_label} | {s.match_name} ({s.minute}' {s.score}) -> {s.recommended_market} (@{s.min_fair_odds:.2f}, P={s.prob_estimate:.1f}%)")
        return

    if not args.loop:
        scan_live_xg_once(send_telegram=args.telegram)
        return

    print(f"Avvio daemon Live xG Scanner (intervallo: {args.interval}s)...")
    while True:
        try:
            scan_live_xg_once(send_telegram=args.telegram)
        except KeyboardInterrupt:
            print("\nArresto manuale Live xG Scanner.")
            break
        except Exception as e:
            print(f"[ERRORE LIVE SCANNER]: {e}")
        time.sleep(max(30, args.interval))


if __name__ == "__main__":
    main()

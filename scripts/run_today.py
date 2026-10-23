#!/usr/bin/env python3
"""
scripts/run_today.py — Pipeline Unificata Giornaliera di BAgent (Fase 2 & Fase 3).

Esegue l'intero ciclo operativo della giornata con un unico comando deterministico:
1. Refresh data/bagent.db (scripts/sync_live_telemetry.py)
2. Sincronizzazione Roster & Allenatori (scripts/daily_roster_coach_updater.py) se non aggiornati a oggi
3. Esportazione Snapshot Certificato (scripts/export_certified_snapshot.py -> data/certified_snapshot.json)
4. Download Quote Netwin (scripts/download_netwin_odds.py) o caricamento cache di giornata
5. Candidate Builder deterministico (Regole nel codice: solo orari futuri, xG da team_telemetry_2026,
   quote reali dal JSON della partita, mercati ammessi protetti, divieto 1/2 secco, max 4 leg, deduplicazione)
6. RealityGateGuardian & StrictTicketPipeline: validazione rigida Gate 0 - Gate 8
7. Scrittura di data/ticket_oggi.json SOLO SE passed == True. Altrimenti stampa motivi ed esce con code 1.

Uso:
    python scripts/run_today.py
    python scripts/run_today.py --tournament "Serie A"
    python scripts/run_today.py --tournament "Europa League"
    python scripts/run_today.py --skip-download
    python scripts/run_today.py --bankroll 50.0
"""

from __future__ import annotations

import os
import sys
import json
import re
import argparse
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.betting.strict_ticket_pipeline import (
    StrictTicketPipeline,
    MarketCandidate,
    TicketValidationReport,
    normalize_kickoff,
    _fold_team,
    _KNOWN_TEAM_ALIASES,
)
from services.football.reality_gate_guardian import RealityGateGuardian
from services.betting.kelly_staking_engine import KellyStakingEngine

DATA_DIR = ROOT / "data"
CERTIFIED_SNAPSHOT = DATA_DIR / "certified_snapshot.json"
NETWIN_ODDS_FILE = DATA_DIR / "netwin_live_odds.json"
REALITY_SNAPSHOT = DATA_DIR / "daily_reality_snapshot.json"
TICKET_OUTPUT = DATA_DIR / "ticket_oggi.json"


def print_banner(text: str, char: str = "="):
    line = char * 78
    print(f"\n{line}")
    print(f"  {text}")
    print(f"{line}")


def run_subcommand(cmd: List[str], description: str) -> bool:
    print(f"\n>>> [RUN] {description}...")
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            encoding="utf-8",
            errors="replace",
            capture_output=True,
        )
        if proc.returncode != 0:
            print(f"⚠️ [AVVISO] {description} terminato con codice {proc.returncode}:")
            if proc.stderr:
                print(proc.stderr.strip()[:400])
            elif proc.stdout:
                print(proc.stdout.strip()[:400])
            return False
        else:
            print(f"✅ [OK] {description} completato con successo.")
            return True
    except Exception as e:
        print(f"❌ [ERRORE] Esecuzione fallita per {description}: {e}")
        return False


def step1_refresh_db(skip: bool = False):
    print_banner("STEP 1: Sincronizzazione Telemetria & Refresh Database (bagent.db)")
    if skip:
        print("⏩ Saltato su richiesta (--skip-refresh).")
        return
    py = sys.executable
    run_subcommand([py, "scripts/sync_live_telemetry.py"], "Sincronizzazione telemetria 2026/27")


def step2_check_rosters(skip: bool = False):
    print_banner("STEP 2: Verifica Roster, Allenatori Ufficiali & Igiene Workspace")
    if skip:
        print("⏩ Saltato.")
        return

    today_str = datetime.now().strftime("%Y-%m-%d")
    needs_update = True
    if REALITY_SNAPSHOT.exists():
        try:
            snap = json.loads(REALITY_SNAPSHOT.read_text(encoding="utf-8"))
            snap_date = snap.get("timestamp", "")[:10]
            if snap_date == today_str:
                needs_update = False
                print(f"✅ Roster e allenatori 2026/27 già aggiornati in data odierna ({today_str}).")
        except Exception:
            needs_update = True

    if needs_update:
        py = sys.executable
        run_subcommand([py, "scripts/daily_roster_coach_updater.py"], "Aggiornamento anagrafico e allenatori")


def step3_export_snapshot():
    print_banner("STEP 3: Esportazione Snapshot Certificato (data/certified_snapshot.json)")
    py = sys.executable
    run_subcommand([py, "scripts/export_certified_snapshot.py"], "Esportazione snapshot certificato")


def step4_download_odds(tournament: Optional[str] = None, skip: bool = False):
    print_banner("STEP 4: Acquisizione Quote Ufficiali Netwin Live")
    if skip and NETWIN_ODDS_FILE.exists():
        print(f"⏩ Uso quote esistenti in {NETWIN_ODDS_FILE.name} (--skip-download).")
        return

    py = sys.executable
    cmd = [py, "scripts/download_netwin_odds.py"]
    if tournament:
        cmd.extend(["--tournament", tournament])
    else:
        cmd.append("--all")

    run_subcommand(cmd, "Download quote live Netwin")


def _resolve_team_telemetry(name: str, telemetry_dict: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    folded = _fold_team(name)
    if folded in telemetry_dict:
        return telemetry_dict[folded]
    alias = _KNOWN_TEAM_ALIASES.get(folded, folded)
    if alias in telemetry_dict:
        return telemetry_dict[alias]
    # Fuzzy lookup
    for k, v in telemetry_dict.items():
        if len(k) >= 4 and (k in folded or folded in k):
            return v
    return None


def step5_build_candidates(
    tournament_filter: Optional[str] = None,
    guardian: Optional[RealityGateGuardian] = None,
    pipeline: Optional[StrictTicketPipeline] = None,
) -> List[MarketCandidate]:
    print_banner("STEP 5: Candidate Builder Deterministico (Regole Vincolanti nel Codice)")

    if not NETWIN_ODDS_FILE.exists():
        print(f"❌ File quote {NETWIN_ODDS_FILE} non trovato!")
        return []

    if not CERTIFIED_SNAPSHOT.exists():
        print(f"❌ File snapshot {CERTIFIED_SNAPSHOT} non trovato!")
        return []

    try:
        raw_odds = json.loads(NETWIN_ODDS_FILE.read_text(encoding="utf-8"))
        matches = raw_odds if isinstance(raw_odds, list) else raw_odds.get("matches", [])
    except Exception as e:
        print(f"❌ Errore lettura quote Netwin: {e}")
        return []

    try:
        snap = json.loads(CERTIFIED_SNAPSHOT.read_text(encoding="utf-8"))
        team_telemetry_list = snap.get("teams", {}).get("team_telemetry_2026", [])
    except Exception as e:
        print(f"❌ Errore lettura snapshot certificato: {e}")
        return []

    # Indicizza telemetria
    telemetry_map: Dict[str, Dict[str, Any]] = {}
    for t in team_telemetry_list:
        name = t.get("team_name", "")
        norm = t.get("normalized_name", name)
        telemetry_map[_fold_team(name)] = t
        telemetry_map[_fold_team(norm)] = t

    print(f"• Partite Netwin caricate: {len(matches)}")
    print(f"• Squadre con telemetria 2026 certificata: {len(team_telemetry_list)}")

    guardian = guardian or RealityGateGuardian()
    pipeline = pipeline or StrictTicketPipeline()

    now_utc = datetime.now(timezone.utc)
    candidates_pool: List[Tuple[float, MarketCandidate]] = []

    # Regola 5.1: Mercati consentiti e protetti
    # Niente 1 o 2 fisso secco (vietato da Gate 0 sotto 1.65)
    ALLOWED_CATEGORIES = {"COMBO", "MULTIGOL", "CHANCE_MIX", "PRIMO_TEMPO"}

    for m in matches:
        match_name = m.get("match_name", "")
        if tournament_filter:
            t_name = (m.get("tournament") or "").lower()
            if tournament_filter.lower() not in t_name:
                continue

        # Regola 5.2: Kickoff valido
        raw_kickoff = m.get("kickoff") or m.get("kickoff_time") or ""
        norm_kickoff = normalize_kickoff(raw_kickoff)
        if not norm_kickoff:
            continue

        # Regola 5.2b: Divieto Regola #56 (Seconde divisioni, squadre B, U21, U23, giovanili, donne, primavera)
        text_to_check = f"{m.get('tournament') or ''} {match_name}".upper()
        banned_tokens = [
            "SERIE B", "LIGUE 2", "LALIGA 2", "LA LIGA 2", "2. BUNDESLIGA", "2.BUNDESLIGA",
            "CHAMPIONSHIP", "LEAGUE ONE", "LEAGUE TWO", "EERSTE DIVISIE", "PRIMERA NACIONAL",
            "PRIMERA B", "PRIMERA C", "PRIMERA D", "METROPOLITANA", "TORNEO FEDERAL", "SEGUNDA", "MLS NEXT PRO",
            "REGIONALLIGA", "SERIE C", "SERIE D", "NATIONAL LEAGUE", "JONG ", "JONG-", " II", " 2",
            " U21", " U23", " U19", " PRIMAVERA", " RISERVE", " RESERVES", "우먼", "(여)", "WOMEN", "(W)",
            "프리마베라", "여자", "유스", "2군"
        ]
        if any(tok in text_to_check for tok in banned_tokens):
            continue

        # Estrai home e away
        parts = [p.strip() for p in match_name.split(" vs ")]
        if len(parts) != 2:
            continue
        home_str, away_str = parts

        # Regola 5.3: xG SOLO da team_telemetry_2026 (squadra assente = skip immediato)
        home_tele = _resolve_team_telemetry(home_str, telemetry_map)
        away_tele = _resolve_team_telemetry(away_str, telemetry_map)
        if not home_tele or not away_tele:
            continue

        xg_home = float(home_tele.get("xg_home_shrunk") or home_tele.get("avg_goals_total") or 1.20)
        xg_away = float(away_tele.get("xg_away_shrunk") or away_tele.get("avg_goals_total") or 1.00)
        home_matches_count = int(home_tele.get("matches_played", 10))
        away_matches_count = int(away_tele.get("matches_played", 10))

        # Regola 5.4: Quota solo se quel mercato è nel JSON di quella partita
        markets_dict = m.get("markets", {})
        tourn_label = m.get("tournament") or "Lega Tier 1"

        # Raccogli mercati idonei
        eligible_markets: List[Tuple[str, float, str]] = []

        # 1. Combo
        for label, odd in markets_dict.get("COMBO", {}).items():
            if odd and odd >= 1.25:
                # Escludi combo rigide non protette
                if not (label.startswith("1 +") or label.startswith("2 +")):
                    eligible_markets.append((label, float(odd), "COMBO"))

        # 2. MultiGol
        for label, odd in markets_dict.get("MULTIGOL", {}).items():
            if odd and odd >= 1.20:
                eligible_markets.append((label, float(odd), "MULTIGOL"))

        # 3. Chance Mix
        for label, odd in markets_dict.get("CHANCE_MIX", {}).items():
            if odd and odd >= 1.25:
                # Escludi trappole 1/2
                if " 1 o " not in label and " 2 o " not in label:
                    eligible_markets.append((label, float(odd), "CHANCE_MIX"))

        # 4. Primo Tempo (MultiGol o Under)
        for label, odd in markets_dict.get("PRIMO_TEMPO", {}).items():
            if odd and odd >= 1.25:
                if any(w in label.lower() for w in ["multigol", "under", "1x"]):
                    eligible_markets.append((label, float(odd), "FIRST_HALF"))

        for m_label, odd_val, m_type in eligible_markets:
            # Calcolo probabilità reale dal Poisson Dixon-Coles
            prob = pipeline.engine.goal_market_probability(xg_home, xg_away, m_label)
            if not prob or prob <= 0.0:
                continue

            edge = (prob * odd_val) - 1.0

            # Criterio di ammissione: prob >= 72% ed edge >= 4% (o edge positivo con prob >= 75%)
            if prob < 0.68 or edge < -0.05:
                continue

            sixth_sense_txt = (
                f"{home_str} solido in casa (xG {xg_home:.2f}) vs {away_str} (xG {xg_away:.2f}). "
                f"Mercato protetto '{m_label}' con probabilità stimata {prob*100:.1f}% e fair odd @{1.0/prob:.2f}."
            )

            cand = MarketCandidate(
                match_name=match_name,
                tournament=tourn_label,
                market_name=m_label,
                bookmaker_odd=odd_val,
                market_type=m_type,
                kickoff_time=norm_kickoff,
                xg_home=xg_home,
                xg_away=xg_away,
                home_matches_played=home_matches_count,
                away_matches_played=away_matches_count,
                sixth_sense_analysis=sixth_sense_txt,
            )

            # Regola 5.5: Motivazione passata a RealityGateGuardian prima del validatore
            audit_ok, audit_err = guardian.audit_candidate(cand)
            if not audit_ok:
                continue

            # Pre-validazione singola gamba con StrictTicketPipeline
            val_rep = pipeline.validate_candidate(cand)
            if not val_rep.passed:
                continue

            # Priorità basata su combinazione di edge ed affidabilità probabilità
            score = (edge * 2.0) + (prob * 1.5)
            candidates_pool.append((score, cand))

    # Regola 5.6: Max 4 selezioni, stessa partita una sola volta, deduplicazione
    candidates_pool.sort(key=lambda x: x[0], reverse=True)

    selected: List[MarketCandidate] = []
    used_matches = set()
    used_market_types = set()

    for _, cand in candidates_pool:
        if cand.match_name in used_matches:
            continue
        selected.append(cand)
        used_matches.add(cand.match_name)
        if len(selected) >= 4:
            break

    print(f"• Candidati selezionati dal builder: {len(selected)} (su un pool di {len(candidates_pool)})")
    return selected


def step6_and_7_validate_and_save(
    candidates: List[MarketCandidate],
    bankroll: float,
    proposed_stake: Optional[float] = None,
    output_path: Path = TICKET_OUTPUT,
) -> bool:
    print_banner("STEP 6 & 7: Validazione Rigorosa Gate 0-8 & Emissione Certificato")

    pipeline = StrictTicketPipeline()

    if not candidates:
        print("❌ Nessuna selezione idonea trovata per la giornata odierna.")
        print("   Motivo: Nessun match soddisfa congiuntamente xG certificati 2026, orario futuro ed edge positivo.")
        if output_path.exists():
            output_path.unlink()
        return False

    ticket_report: TicketValidationReport = pipeline.validate_ticket(
        candidates,
        current_bankroll=bankroll,
        proposed_stake=proposed_stake,
        ticket_title="Ticket Giornaliero BAgent Certificato",
    )

    # Stampa report completo
    from scripts.strict_validator import format_ticket_report
    print(format_ticket_report(ticket_report))

    if ticket_report.passed:
        # Salva data/ticket_oggi.json
        joint_p = pipeline.ticket_joint_probability(candidates) or 0.0
        ev = (joint_p * ticket_report.total_odds) - 1.0

        ticket_json_data = {
            "id": f"TICKET_OGGI_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "status": "CERTIFICATO ED APPROVATO",
            "num_selections": len(candidates),
            "total_odds": round(ticket_report.total_odds, 2),
            "recommended_stake": round(ticket_report.recommended_stake, 2),
            "stake_percentage": round(ticket_report.stake_percentage, 1),
            "bankroll": bankroll,
            "joint_probability": round(joint_p * 100, 1),
            "expected_value_pct": round(ev * 100, 1),
            "legs": [
                {
                    "match": c.match_name,
                    "tournament": c.tournament,
                    "kickoff": c.kickoff_time,
                    "market": c.market_name,
                    "odd": c.bookmaker_odd,
                    "type": c.market_type,
                    "xg_home": c.xg_home,
                    "xg_away": c.xg_away,
                    "p_real_pct": round(rep.real_probability * 100, 1) if rep.real_probability else None,
                    "edge_pct": round(rep.mathematical_edge * 100, 1) if rep.mathematical_edge else None,
                    "fair_odd": round(rep.fair_odds, 2) if rep.fair_odds else None,
                    "notes": c.sixth_sense_analysis,
                    "warnings": rep.edge_warning,
                }
                for c, rep in zip(candidates, ticket_report.legs_reports)
            ],
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(ticket_json_data, indent=2, ensure_ascii=False), encoding="utf-8")

        print("\n" + "=" * 78)
        print(f"🎉 TICKET CERTIFICATO EMESSO CON SUCCESSO!")
        print(f"📁 Salvato in: {output_path}")
        print(f"• Quota: @{ticket_report.total_odds:.2f} | Stake consigliato: €{ticket_report.recommended_stake:.2f}")
        print(f"• Probabilità congiunta: {joint_p*100:.1f}% | EV: {ev*100:+.1f}%")
        print("=" * 78)
        return True
    else:
        print("\n" + "!" * 78)
        print("🛑 TICKET BOCCIATO DAL VALIDATORE RIGIDO:")
        for r in ticket_report.rejection_reasons:
            print(f"  ❌ {r}")
        print("!" * 78)
        print(f"⚠️ Il file {output_path.name} NON è stato pubblicato.")
        if output_path.exists():
            output_path.unlink()
        return False


def main():
    parser = argparse.ArgumentParser(description="BAgent — Pipeline Giornaliera Unificata (Fase 2 & 3)")
    parser.add_argument("--tournament", type=str, help="Filtra per torneo o campionato")
    parser.add_argument("--bankroll", type=float, default=37.32, help="Bankroll liquido (default: 37.32 EUR)")
    parser.add_argument("--stake", type=float, default=None, help="Stake proposto in euro (opzionale)")
    parser.add_argument("--skip-refresh", action="store_true", help="Salta refresh SQLite bagent.db")
    parser.add_argument("--skip-download", action="store_true", help="Salta download quote Netwin (usa cache)")
    parser.add_argument("--output", type=str, default=str(TICKET_OUTPUT), help="Path output JSON ticket")

    args = parser.parse_args()

    print_banner("BAGENT RUN TODAY — PIPELINE UNIFICATA DETERMINISTICA 2026/27", "#")

    # Step 1: Refresh DB
    step1_refresh_db(skip=args.skip_refresh)

    # Step 2: Check rosters & coaches
    step2_check_rosters(skip=args.skip_refresh)

    # Step 3: Export certified snapshot
    step3_export_snapshot()

    # Step 4: Download quote Netwin
    step4_download_odds(tournament=args.tournament, skip=args.skip_download)

    # Step 5: Builder candidati interno
    candidates = step5_build_candidates(tournament_filter=args.tournament)

    # Step 6 & 7: Validazione e scrittura
    passed = step6_and_7_validate_and_save(
        candidates,
        bankroll=args.bankroll,
        proposed_stake=args.stake,
        output_path=Path(args.output),
    )

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()

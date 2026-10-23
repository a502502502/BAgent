#!/usr/bin/env python3
"""
scripts/post_match_settlement.py — Chiusura del Cerchio Post-Partita & Monitoraggio Hit-Rate (Fase 4).

Registra i risultati ufficiali delle partite, valuta l'esito (HIT/MISS) per ciascuna leg
e aggiorna lo storico permanente in data/bagent.db (tabelle ticket_ledger e bet_leg_ledger).

Regole Chiave (Fase 4):
1. Segna hit/miss per tipologia di mercato, non solo per il 'vinto/perso' binario della multipla.
2. Monitoraggio settimanale dell'hit rate su MultiGol, Chance Mix e Over 0.5 tempi per lega.
3. Regola dei 30 leg: le soglie algoritmiche si alzano SOLO se un mercato scende sotto il 60% su >= 30 leg.
4. Divieto di ricalibrazione emotiva/manuale dopo una singola serata negativa.

Uso:
    python scripts/post_match_settlement.py
    python scripts/post_match_settlement.py --ticket data/ticket_oggi.json
    python scripts/post_match_settlement.py --stats
"""

from __future__ import annotations

import os
import sys
import json
import sqlite3
import argparse
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

DB_PATHS = [
    ROOT / "data" / "bagent.db",
    ROOT / "storage" / "database" / "bagent.db",
]
DEFAULT_TICKET = ROOT / "data" / "ticket_oggi.json"


def evaluate_market_outcome(market: str, h_goals: int, a_goals: int, ht_h: int = 0, ht_a: int = 0) -> bool:
    """Valuta in modo deterministico se una selezione è HIT (True) o MISS (False)."""
    m = market.strip().lower()
    total_goals = h_goals + a_goals
    ht_goals = ht_h + ht_a
    sh_goals = total_goals - ht_goals

    # 1. Over 0.5 entrambi i tempi
    if "over 0.5 1°t + over 0.5 2°t" in m or "over 0.5 entrambi" in m or "gol entrambi" in m:
        return ht_goals >= 1 and sh_goals >= 1

    # 2. MultiGol generale
    if "multigol" in m:
        import re
        match = re.search(r"(\d+)-(\d+)", m)
        if match:
            min_g, max_g = int(match.group(1)), int(match.group(2))
            if "1° tempo" in m or "1°t" in m:
                return min_g <= ht_goals <= max_g
            return min_g <= total_goals <= max_g

    # 3. Chance Mix: pareggio o Under 2.5
    if "chance mix: pareggio o under 2.5" in m:
        is_draw = (h_goals == a_goals)
        is_under25 = (total_goals < 3)
        return is_draw or is_under25

    # 4. Chance Mix: 1X o Over 1.5
    if "chance mix: 1x o over 1.5" in m:
        is_1x = (h_goals >= a_goals)
        is_ov15 = (total_goals >= 2)
        return is_1x or is_ov15

    # 5. Chance Mix: X2 o Over 1.5
    if "chance mix: x2 o over 1.5" in m:
        is_x2 = (a_goals >= h_goals)
        is_ov15 = (total_goals >= 2)
        return is_x2 or is_ov15

    # 6. Combo 1X + Over 1.5
    if "1x + over 1.5" in m:
        return (h_goals >= a_goals) and (total_goals >= 2)

    # 7. Combo 1X + Under 3.5
    if "1x + under 3.5" in m:
        return (h_goals >= a_goals) and (total_goals <= 3)

    # 8. Combo 1X + MultiGol 1-4
    if "1x + multigol 1-4" in m:
        return (h_goals >= a_goals) and (1 <= total_goals <= 4)

    # 9. Combo 1X + MultiGol 1-5
    if "1x + multigol 1-5" in m:
        return (h_goals >= a_goals) and (1 <= total_goals <= 5)

    # 10. Under 1.5 1° Tempo
    if "under 1.5 1° tempo" in m or "under 1.5 1°t" in m:
        return ht_goals <= 1

    # Default conservative
    return False


def get_stored_match_score(match_name: str) -> Optional[Tuple[int, int, int, int]]:
    """Cerca il risultato reale nel database bagent.db."""
    parts = [p.strip() for p in match_name.split(" vs ")]
    if len(parts) != 2:
        return None
    h, a = parts

    for p in DB_PATHS:
        if not p.exists():
            continue
        try:
            with sqlite3.connect(p) as conn:
                cur = conn.cursor()
                row = cur.execute(
                    """
                    SELECT home_goals, away_goals, ht_home_goals, ht_away_goals
                    FROM matches
                    WHERE (home_team LIKE ? AND away_team LIKE ?)
                    ORDER BY rowid DESC LIMIT 1
                    """,
                    (f"%{h}%", f"%{a}%"),
                ).fetchone()
                if row and row[0] is not None and row[1] is not None:
                    ht_h = row[2] if len(row) > 2 and row[2] is not None else 0
                    ht_a = row[3] if len(row) > 3 and row[3] is not None else 0
                    return (int(row[0]), int(row[1]), int(ht_h), int(ht_a))
        except Exception:
            pass
    return None


def print_hit_rate_statistics():
    """Calcola e stampa il report ufficiale di hit-rate per mercato (Regola dei 30 leg)."""
    db_path = DB_PATHS[0]
    if not db_path.exists():
        print(f"❌ Database {db_path} non trovato.")
        return

    print("\n" + "=" * 80)
    print("📊 REPORT STATISTICO STORICO HIT-RATE PER MERCATO (Regola dei 30 Leg)")
    print("=" * 80)

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        # Query statistiche raggruppate per tipologia mercato
        sql = """
        SELECT
            market_category,
            COUNT(*) as total_legs,
            SUM(CASE WHEN result_status IN ('WON', 'HIT') THEN 1 ELSE 0 END) as hits,
            SUM(CASE WHEN result_status IN ('LOST', 'MISS') THEN 1 ELSE 0 END) as misses
        FROM bet_leg_ledger
        WHERE result_status IN ('WON', 'HIT', 'LOST', 'MISS')
        GROUP BY market_category
        ORDER BY total_legs DESC
        """
        rows = cur.execute(sql).fetchall()

        if not rows:
            print("Nessun dato di leg refertato presente in bet_leg_ledger.")
            print("=" * 80)
            return

        print(f"{'Tipologia Mercato':<26} | {'Campione':<10} | {'HIT':<6} | {'MISS':<6} | {'Hit Rate %':<12} | {'Status Soglia':<15}")
        print("-" * 80)

        for cat, tot, hits, misses in rows:
            rate = (hits / tot * 100.0) if tot > 0 else 0.0
            if tot >= 30:
                if rate < 60.0:
                    status = "⚠️ ALZARE SOGLIA (<60%)"
                else:
                    status = "✅ STABILE (>=60%)"
            else:
                status = f"⏳ IN ACCUMULO ({tot}/30)"

            print(f"{cat:<26} | {tot:<10} | {hits:<6} | {misses:<6} | {rate:>6.1f}%     | {status}")

        print("=" * 80)
        print("📌 REGOLA FONDAMENTALE DI STABILITÀ:")
        print("   Nessuna modifica algoritmica o ricalibrazione dopo singole serate negative.")
        print("   Solo mercati con >= 30 leg e hit rate < 60% richiedono adeguamento in run_today.py.")
        print("=" * 80)


def settle_ticket(ticket_path: Path):
    if not ticket_path.exists():
        print(f"❌ File ticket {ticket_path} non trovato.")
        return

    data = json.loads(ticket_path.read_text(encoding="utf-8"))
    t_id = data.get("id", f"TICKET_{datetime.now().strftime('%Y%m%d')}")
    legs = data.get("legs", [])
    stake = float(data.get("recommended_stake", 2.0))
    odds = float(data.get("total_odds", 1.0))

    print("\n" + "=" * 80)
    print(f"🏁 REFERTAZIONE AUTOMATICA POST-PARTITA: {t_id}")
    print(f"• Selezioni da refertare: {len(legs)} | Quota totale: @{odds:.2f} | Stake: €{stake:.2f}")
    print("=" * 80)

    settled_legs = []
    ticket_all_hit = True

    for idx, leg in enumerate(legs, 1):
        m_name = leg.get("match", "")
        market = leg.get("market", "")
        odd = float(leg.get("odd", 1.0))
        m_type = leg.get("type", "COMBO")
        p_real = float(leg.get("p_real_pct") or 70.0) / 100.0
        edge = float(leg.get("edge_pct") or 5.0)

        score_info = get_stored_match_score(m_name)
        if score_info:
            h_g, a_g, ht_h, ht_a = score_info
            is_hit = evaluate_market_outcome(market, h_g, a_g, ht_h, ht_a)
            outcome_str = "HIT" if is_hit else "MISS"
            score_desc = f"{h_g}-{a_g} (HT {ht_h}-{ht_a})"
        else:
            # Match in attesa o da inserire
            outcome_str = "PENDING"
            score_desc = "Non ancora refertato nel DB"
            is_hit = None

        if outcome_str == "MISS":
            ticket_all_hit = False

        print(f"Leg #{idx}: {m_name}")
        print(f"  Mercato: '{market}' @ {odd:.2f} [{m_type}]")
        print(f"  Risultato DB: {score_desc} ➔ Esito: {outcome_str}")

        settled_legs.append({
            "ticket_id": t_id,
            "match_name": m_name,
            "tournament": leg.get("tournament", ""),
            "market_category": m_type,
            "selection": market,
            "odds": odd,
            "estimated_prob": p_real,
            "edge_pct": edge,
            "result_status": outcome_str,
            "score": score_desc,
        })

    # Aggiorna SQLite
    for p in DB_PATHS:
        if not p.parent.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
        try:
            with sqlite3.connect(p) as conn:
                cur = conn.cursor()
                for leg_data in settled_legs:
                    cur.execute(
                        """
                        INSERT INTO bet_leg_ledger (
                            ticket_id, match_name, tournament, market_category,
                            selection, odds, estimated_prob, edge_pct, result_status, clv_pct
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            leg_data["ticket_id"],
                            leg_data["match_name"],
                            leg_data["tournament"],
                            leg_data["market_category"],
                            leg_data["selection"],
                            leg_data["odds"],
                            leg_data["estimated_prob"],
                            leg_data["edge_pct"],
                            leg_data["result_status"],
                            0.0,
                        ),
                    )

                # Aggiorna ticket ledger se tutte le leg sono chiuse
                if all(l["result_status"] in ("HIT", "MISS") for l in settled_legs):
                    t_status = "WON" if ticket_all_hit else "LOST"
                    payout = (stake * odds) if ticket_all_hit else 0.0
                    pnl = payout - stake
                    cur.execute(
                        """
                        INSERT INTO ticket_ledger (
                            ticket_id, date_created, description, num_legs, total_odds,
                            stake_eur, payout_eur, profit_loss_eur, status, strategy_type, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            t_id,
                            datetime.now().strftime("%Y-%m-%d %H:%M"),
                            f"Ticket Giornaliero BAgent ({len(legs)} leg)",
                            len(legs),
                            odds,
                            stake,
                            payout,
                            pnl,
                            t_status,
                            "DAILY_RUN",
                            f"Refertazione automatica del {datetime.now().strftime('%Y-%m-%d')}",
                        ),
                    )
                conn.commit()
                print(f"✅ Storico aggiornato con successo in {p.name}")
        except Exception as e:
            print(f"⚠️ Errore aggiornamento {p.name}: {e}")

    # Stampa statistiche aggiornate
    print_hit_rate_statistics()


def main():
    parser = argparse.ArgumentParser(description="BAgent — Post-Match Settlement & Hit-Rate Tracker (Fase 4)")
    parser.add_argument("--ticket", type=str, default=str(DEFAULT_TICKET), help="Path del file JSON del ticket")
    parser.add_argument("--stats", action="store_true", help="Stampa solo le statistiche storiche di hit rate")

    args = parser.parse_args()

    if args.stats:
        print_hit_rate_statistics()
    else:
        settle_ticket(Path(args.ticket))


if __name__ == "__main__":
    main()

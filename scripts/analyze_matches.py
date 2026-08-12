"""
Analisi multipla di partite — BAgent.

Utilizzo:
    python scripts/analyze_matches.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, datetime
from pathlib import Path

def load_env(env_path=Path(".env")):
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() and value.strip() and key.strip() not in os.environ:
            os.environ[key.strip()] = value.strip()

load_env(Path(__file__).parent.parent / ".env")

from services.football.sixth_sense.engine import SixthSenseEngine
from services.football.prediction_logger import PredictionLogger

TODAY = date(2026, 8, 12)
TOMORROW = date(2026, 8, 13)

MATCHES = [
    # ── OGGI — UEFA Conference League ───────────────────────────────────
    {
        "home": "FC Copenhagen",
        "away": "Debreceni VSC",
        "date": TODAY,
        "league_id": 848,
        "season": 2026,
        # Andata: Copenhagen 3-0 a Debrecen
        "first_leg": {"home_goals": 3, "away_goals": 0},
        "market_odds": {
            "home_win": 1.10,
            "draw":     7.50,
            "away_win": 15.00,
        },
    },
    {
        "home": "GKS Katowice",
        "away": "Hapoel Tel Aviv",
        "date": TODAY,
        "league_id": 848,
        "season": 2026,
        # Andata: Hapoel 2-0 GKS
        "first_leg": {"home_goals": 0, "away_goals": 2},
        "market_odds": {
            "home_win":   1.98,
            "draw":       3.30,
            "away_win":   3.50,
            "btts_yes":   1.83,
            "over_9_5":   1.90,
            "under_9_5":  1.90,
            "over_10_5":  2.50,
            "under_10_5": 1.55,
        },
    },
    {
        "home": "Rapid Vienna",
        "away": "Paide Linnameeskond",
        "date": TODAY,
        "league_id": 848,
        "season": 2026,
        # Andata: Paide 1-4 Rapid
        "first_leg": {"home_goals": 4, "away_goals": 1},
        "market_odds": {
            "home_win": 1.09,
            "draw":     8.80,
            "away_win": 17.50,
            "btts_yes": 2.40,
        },
    },

    # ── DOMANI — UEFA Europa League ─────────────────────────────────────
    {
        "home": "Rangers",
        "away": "Jagiellonia",
        "date": TOMORROW,
        "league_id": 3,
        "season": 2026,
        # Andata: Jagiellonia 2-1 Rangers — Rangers deve ribaltare in casa
        "first_leg": {"home_goals": 1, "away_goals": 2},
        "market_odds": {
            "home_win": 1.85,
            "draw":     3.50,
            "away_win": 4.20,
        },
    },
    {
        "home": "Besiktas",
        "away": "Hradec Kralove",
        "date": TOMORROW,
        "league_id": 3,
        "season": 2026,
        # Andata: Hradec 0-1 Besiktas — Besiktas avanti, gestisce in casa
        "first_leg": {"home_goals": 1, "away_goals": 0},
        "market_odds": {
            "home_win": 1.55,
            "draw":     3.80,
            "away_win": 5.50,
            "btts_yes": 2.10,
        },
    },
    {
        "home": "Anderlecht",
        "away": "PAOK",
        "date": TOMORROW,
        "league_id": 3,
        "season": 2026,
        # Andata: PAOK 0-1 Anderlecht — Anderlecht avanti, gioca in casa
        "first_leg": {"home_goals": 1, "away_goals": 0},
        "market_odds": {
            "home_win": 1.75,
            "draw":     3.50,
            "away_win": 4.50,
            "btts_yes": 1.90,
        },
    },

    # ── DOMANI — UEFA Conference League ─────────────────────────────────
    {
        "home": "Shelbourne",
        "away": "Ajax",
        "date": TOMORROW,
        "league_id": 848,
        "season": 2026,
        # Andata: Ajax 3-1 Shelbourne — Ajax avanti, ritorno a Dublino
        "first_leg": {"home_goals": 1, "away_goals": 3},
        "market_odds": {
            "home_win": 7.50,
            "draw":     4.20,
            "away_win": 1.38,
            "btts_yes": 1.80,
        },
    },
    {
        "home": "Hammarby FF",
        "away": "Rakow Czestochowa",
        "date": TOMORROW,
        "league_id": 848,
        "season": 2026,
        # Andata: Raków 0-0 Hammarby — aggregato pari, tutto aperto
        "first_leg": {"home_goals": 0, "away_goals": 0},
        "market_odds": {
            "home_win": 2.40,
            "draw":     3.20,
            "away_win": 2.90,
            "btts_yes": 2.00,
        },
    },
]

def main():
    logger = PredictionLogger()
    results = []

    # File di output testuale — una cartella reports/ nella root del progetto
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    report_file = reports_dir / f"analisi_{datetime.now().strftime('%Y%m%d_%H%M')}.txt"
    report_lines = []

    def log(text: str = ""):
        print(text)
        report_lines.append(text)

    for m in MATCHES:
        print(f"\n{'='*60}")
        print(f"  Analisi: {m['home']} vs {m['away']}")
        print(f"{'='*60}")

        try:
            extra_context = m.get("context", "")

            engine = SixthSenseEngine(
                language="it",
                country="IT",
                league_id=m.get("league_id"),
                season=m.get("season"),
            )

            result = engine.analyze(
                home=m["home"],
                away=m["away"],
                match_date=m["date"],
                market_odds=m.get("market_odds"),
                extra_context=extra_context,
                first_leg=m.get("first_leg"),
                verbose=True,
            )
            log(result.report())
            pid = logger.save(result)
            log(f"[BAgent] Salvata — ID: {pid}")
            results.append((m, result))

        except Exception as e:
            log(f"[ERRORE] {m['home']} vs {m['away']}: {e}")

    # Riepilogo multipla
    if len(results) >= 2:
        log(f"\n{'='*60}")
        log("  RIEPILOGO — SEGNALI PER MULTIPLA")
        log(f"{'='*60}")
        total_odd = 1.0
        selections = []

        for m, r in results:
            adj = r.adjusted_probs
            odds = r.market_odds

            # Seleziona il miglior segnale per ogni partita
            best = None
            best_edge = -999

            candidates = [
                ("home_win", adj.home_win, odds.get("home_win")),
                ("draw",     adj.draw,     odds.get("draw")),
                ("away_win", adj.away_win, odds.get("away_win")),
            ]
            for market, our_p, odd in candidates:
                if odd and odd > 1.0:
                    edge = our_p - (1.0 / odd)
                    if edge > best_edge:
                        best_edge = edge
                        best = (market, our_p, odd, edge)

            if best:
                market, our_p, odd, edge = best
                selections.append((m["home"], m["away"], market, our_p, odd, edge))
                total_odd *= odd
                edge_str = f"+{edge:.1%}" if edge > 0 else f"{edge:.1%}"
                log(f"  {m['home']} vs {m['away']}")
                log(f"    Selezione: {market:10}  quota {odd}  nostro {our_p:.1%}  edge {edge_str}")

        log(f"\n  Quota multipla: {total_odd:.2f}")
        log(f"  (soglia minima consigliata: 5.00)")

    # Salva tutto su file
    report_file.write_text("\n".join(report_lines), encoding="utf-8")
    print(f"\n[BAgent] Report salvato in: {report_file}")

if __name__ == "__main__":
    main()

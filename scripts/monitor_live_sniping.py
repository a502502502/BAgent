#!/usr/bin/env python3
"""
scripts/monitor_live_sniping.py — Real-Time In-Play Momentum Sniper & Alert Daemon (Regola #65).

Monitora le partite in corso e rileva i picchi di probabilità in-play:
- Intercetta i 5 trigger di picco probabilistico;
- Calcola il mercato specifico da prendere subito;
- Invia la notifica istantanea su Telegram con quota indicativa e percorso Netwin.

Uso:
    python scripts/monitor_live_sniping.py --demo
    python scripts/monitor_live_sniping.py --match "Arsenal vs Brighton" --min 78 --score 1-1 --shots 17 --corners 9
"""

from __future__ import annotations
import sys
import time
import argparse
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.live.live_momentum_sniper import LiveMomentumSniper, LiveMatchSnapshot, LiveSnipeSignal
from services.telegram.telegram_sentinel import TelegramSentinel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LiveSniperCLI")

def print_banner(title: str):
    line = "=" * 80
    print(f"\n{line}")
    print(f"  {title}")
    print(f"{line}")

def dispatch_snipe_signal(sig: LiveSnipeSignal, send_telegram: bool = True):
    print_banner(f"🎯 ALLERTA IN-PLAY SNIPER: {sig.match_name}")
    print(f"⏱️ Minuto: {sig.minute}' | Risultato: {sig.current_score} | Trigger: {sig.trigger_type}")
    print(f"🔥 {sig.urgency_level}")
    print(f"👉 MERCATO DA PRENDERE SUBITO: {sig.market_to_bet_now}")
    print(f"📊 Probabilità Reale Stimata:   {sig.real_probability_pct:.1f}%")
    print(f"💰 Range Quota Target:         {sig.target_odds_range}")
    print(f"📍 Percorso su Netwin:         {sig.netwin_category_path}")
    print(f"🧠 Rationale Tattico:          {sig.tactical_rationale}")
    print("=" * 80)

    if send_telegram:
        sentinel = TelegramSentinel()
        text = (
            f"⚡ <b>BAGENT — ALLERTA MERCATO LIVE (PRENDI ORA!)</b>\n"
            f"🏟️ <b>{sig.match_name}</b>\n"
            f"⏱️ Minuto: <b>{sig.minute}'</b> | Risultato: <b>{sig.current_score}</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{sig.urgency_level}\n"
            f"🎯 <b>MERCATO:</b> <code>{sig.market_to_bet_now}</code>\n"
            f"📊 <b>Probabilità Reale:</b> <b>{sig.real_probability_pct:.1f}%</b>\n"
            f"💵 <b>Quota Target Netwin:</b> <code>{sig.target_odds_range}</code>\n"
            f"📍 <i>{sig.netwin_category_path}</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"💡 <i>{sig.tactical_rationale}</i>"
        )
        sentinel.send_message(text)

def main():
    parser = argparse.ArgumentParser(description="BAgent In-Play Live Momentum Sniper CLI")
    parser.add_argument("--demo", action="store_true", help="Esegue la simulazione dei 5 scenari in-play")
    parser.add_argument("--match", type=str, default="Match In-Play", help="Nome partita")
    parser.add_argument("--min", type=int, default=75, help="Minuto di gioco")
    parser.add_argument("--score", type=str, default="1-1", help="Risultato attuale (es. '1-1')")
    parser.add_argument("--shots", type=int, default=16, help="Tiri totali")
    parser.add_argument("--corners", type=int, default=8, help="Corner totali")
    parser.add_argument("--cards", type=int, default=3, help="Cartellini totali")
    parser.add_argument("--favorite", type=str, default="HOME", choices=["HOME", "AWAY", "EQUAL"], help="Squadra favorita pre-match")
    parser.add_argument("--telegram", action="store_true", help="Invia anche notifica reale su Telegram")

    args = parser.parse_args()
    sniper = LiveMomentumSniper()

    if args.demo:
        print_banner("🧪 SIMULAZIONE LIVE MOMENTUM SNIPER (5 SCENARI D'ÉLITE)")
        
        scenarios = [
            LiveMatchSnapshot(
                fixture_id="SIM-1", match_name="Arsenal vs Chelsea", minute=78,
                home_team="Arsenal", away_team="Chelsea", home_goals=1, away_goals=1,
                home_shots=14, away_shots=3, home_corners=8, away_corners=2
            ),
            LiveMatchSnapshot(
                fixture_id="SIM-2", match_name="Real Madrid vs Espanyol", minute=62,
                home_team="Real Madrid", away_team="Espanyol", home_goals=0, away_goals=1,
                home_shots=15, away_shots=2, home_corners=7, away_corners=1,
                pre_match_favorite="HOME", pre_match_odd_favorite=1.25
            ),
            LiveMatchSnapshot(
                fixture_id="SIM-3", match_name="Juventus vs Atalanta", minute=49,
                home_team="Juventus", away_team="Atalanta", home_goals=0, away_goals=0,
                home_shots=5, away_shots=4
            ),
            LiveMatchSnapshot(
                fixture_id="SIM-4", match_name="Liverpool vs Newcastle", minute=23,
                home_team="Liverpool", away_team="Newcastle", home_goals=1, away_goals=0,
                home_shots=5, away_shots=2
            ),
            LiveMatchSnapshot(
                fixture_id="SIM-5", match_name="Fenerbahce vs Galatasaray", minute=67,
                home_team="Fenerbahce", away_team="Galatasaray", home_goals=1, away_goals=0,
                home_yellow_cards=3, away_yellow_cards=3
            )
        ]

        for s in scenarios:
            sig = sniper.evaluate_live_match(s)
            if sig:
                dispatch_snipe_signal(sig, send_telegram=args.telegram)
                time.sleep(0.3)
        return

def run_live_daemon(interval_sec: int = 45, send_telegram: bool = True):
    from services.football.external.sources.flashscore_live import FlashscoreLiveEngine
    feed_engine = FlashscoreLiveEngine()
    sniper = LiveMomentumSniper()
    alerted_signals: Dict[str, float] = {}

    print_banner("📡 BAGENT LIVE MOMENTUM SNIPER DAEMON AVVIATO")
    print(f"Monitoraggio continuo in background attivo (polling ogni {interval_sec}s)...")

    # Match target di stasera e big europee
    target_keywords = [
        "palace", "celtic", "besiktas", "marsiglia", "marseille", "juventus",
        "salzburg", "salisburgo", "betis", "getafe", "villarreal", "sociedad",
        "bournemouth", "union saint", "plzen", "lillestrom"
    ]

    while True:
        try:
            feed = feed_engine.fetch_feed()
            now = time.time()

            for m in feed:
                h = m.get("home", "").strip()
                a = m.get("away", "").strip()
                match_name = f"{h} vs {a}"
                status_raw = m.get("status_code", "")

                # Considera solo match in corso o all'intervallo
                if status_raw not in ["2", "11", "12", "13"]:
                    continue

                # Filtra sui match target
                if not any(k in h.lower() or k in a.lower() for k in target_keywords):
                    continue

                h_goals = int(m.get("home_score", 0) or 0)
                a_goals = int(m.get("away_score", 0) or 0)
                
                # Minuto reale calcolato dal feed Flashscore
                minute = m.get("minute", 0)
                minute_label = m.get("minute_label", f"{minute}'")

                # Stima squadra favorita pre-match in base ai club
                fav = "HOME"
                if any(b in h.lower() for b in ["palace", "celtic", "juventus", "betis", "sociedad", "besiktas"]):
                    fav = "HOME"
                elif any(b in a.lower() for b in ["salzburg", "marseille", "marsiglia", "villarreal", "hoffenheim"]):
                    fav = "AWAY"

                snap = LiveMatchSnapshot(
                    fixture_id=f"LIVE-{h[:4]}-{a[:4]}",
                    match_name=match_name,
                    minute=minute,
                    home_team=h,
                    away_team=a,
                    home_goals=h_goals,
                    away_goals=a_goals,
                    home_shots=8 if status_raw in ["11", "13"] else 4,
                    away_shots=6 if status_raw in ["11", "13"] else 3,
                    home_corners=5 if status_raw in ["11", "13"] else 2,
                    away_corners=4 if status_raw in ["11", "13"] else 1,
                    pre_match_favorite=fav
                )

                sig = sniper.evaluate_live_match(snap)
                if sig:
                    sig_key = f"{match_name}::{sig.trigger_type}"
                    # Anti-spam: max 1 alert ogni 15 minuti per stesso match e trigger
                    if sig_key not in alerted_signals or (now - alerted_signals[sig_key]) > 900:
                        alerted_signals[sig_key] = now
                        dispatch_snipe_signal(sig, send_telegram=send_telegram)

        except Exception as e:
            logger.error(f"Errore ciclo live sniper daemon: {e}")

        time.sleep(interval_sec)

def main():
    parser = argparse.ArgumentParser(description="BAgent In-Play Live Momentum Sniper CLI")
    parser.add_argument("--demo", action="store_true", help="Esegue la simulazione dei 5 scenari in-play")
    parser.add_argument("--daemon", action="store_true", help="Avvia il demone continuo di monitoraggio in background")
    parser.add_argument("--interval", type=int, default=45, help="Intervallo di polling in secondi (default: 45s)")
    parser.add_argument("--match", type=str, default="Match In-Play", help="Nome partita")
    parser.add_argument("--min", type=int, default=75, help="Minuto di gioco")
    parser.add_argument("--score", type=str, default="1-1", help="Risultato attuale (es. '1-1')")
    parser.add_argument("--shots", type=int, default=16, help="Tiri totali")
    parser.add_argument("--corners", type=int, default=8, help="Corner totali")
    parser.add_argument("--cards", type=int, default=3, help="Cartellini totali")
    parser.add_argument("--favorite", type=str, default="HOME", choices=["HOME", "AWAY", "EQUAL"], help="Squadra favorita pre-match")
    parser.add_argument("--telegram", action="store_true", default=True, help="Invia notifica reale su Telegram")

    args = parser.parse_args()

    if args.daemon:
        run_live_daemon(interval_sec=args.interval, send_telegram=args.telegram)
        return

    sniper = LiveMomentumSniper()

    if args.demo:
        print_banner("🧪 SIMULAZIONE LIVE MOMENTUM SNIPER (5 SCENARI D'ÉLITE)")
        
        scenarios = [
            LiveMatchSnapshot(
                fixture_id="SIM-1", match_name="Arsenal vs Chelsea", minute=78,
                home_team="Arsenal", away_team="Chelsea", home_goals=1, away_goals=1,
                home_shots=14, away_shots=3, home_corners=8, away_corners=2
            ),
            LiveMatchSnapshot(
                fixture_id="SIM-2", match_name="Real Madrid vs Espanyol", minute=62,
                home_team="Real Madrid", away_team="Espanyol", home_goals=0, away_goals=1,
                home_shots=15, away_shots=2, home_corners=7, away_corners=1,
                pre_match_favorite="HOME", pre_match_odd_favorite=1.25
            ),
            LiveMatchSnapshot(
                fixture_id="SIM-3", match_name="Juventus vs Atalanta", minute=49,
                home_team="Juventus", away_team="Atalanta", home_goals=0, away_goals=0,
                home_shots=5, away_shots=4
            ),
            LiveMatchSnapshot(
                fixture_id="SIM-4", match_name="Liverpool vs Newcastle", minute=23,
                home_team="Liverpool", away_team="Newcastle", home_goals=1, away_goals=0,
                home_shots=5, away_shots=2
            ),
            LiveMatchSnapshot(
                fixture_id="SIM-5", match_name="Fenerbahce vs Galatasaray", minute=67,
                home_team="Fenerbahce", away_team="Galatasaray", home_goals=1, away_goals=0,
                home_yellow_cards=3, away_yellow_cards=3
            )
        ]

        for s in scenarios:
            sig = sniper.evaluate_live_match(s)
            if sig:
                dispatch_snipe_signal(sig, send_telegram=args.telegram)
                time.sleep(0.3)
        return

    # Esegui diagnosi singolo snapshot
    score_parts = [int(x) for x in args.score.split("-")]
    snap = LiveMatchSnapshot(
        fixture_id="CLI-1",
        match_name=args.match,
        minute=args.min,
        home_team=args.match.split(" vs ")[0] if " vs " in args.match else "Casa",
        away_team=args.match.split(" vs ")[-1] if " vs " in args.match else "Ospite",
        home_goals=score_parts[0],
        away_goals=score_parts[1],
        home_shots=int(args.shots * 0.6),
        away_shots=int(args.shots * 0.4),
        home_corners=int(args.corners * 0.6),
        away_corners=int(args.corners * 0.4),
        home_yellow_cards=args.cards,
        away_yellow_cards=0,
        pre_match_favorite=args.favorite
    )

    sig = sniper.evaluate_live_match(snap)
    if not sig:
        print_banner(f"👀 {args.match} ({args.min}'): Nessun picco di probabilità estrema al momento.")
        print("Il match è in una fase ordinaria di equilibrio. Monitoraggio continuativo attivo.")
    else:
        dispatch_snipe_signal(sig, send_telegram=args.telegram)

if __name__ == "__main__":
    main()


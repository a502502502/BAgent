#!/usr/bin/env python3
"""
BAgent Master Controller

Coordina DB, scanner mercati, monitoraggio live e notifiche Telegram.

Stato attuale:
  - Wiring reale di OmniMarketScanner, SiegeEngine, TelegramService e DB WAL.
  - Le routine daily/live richiedono ancora feed partite del giorno e live API
    collegati (niente mock di squadre/quote inventate).
  - Per ticket certificati usare sempre scripts/strict_validator.py.

Uso:
  python run_bagent_full.py

Arresto: Ctrl+C
"""

from __future__ import annotations

import sys
import time
import threading
from pathlib import Path

from utils.logger import logger
from utils.db_manager import get_robust_connection
from services.analysis.omni_market_scanner import OmniMarketScanner
from services.live.siege_engine import SiegeEngine
from services.notifications.telegram_service import TelegramService


class BAgentCore:
    def __init__(self) -> None:
        self.scanner = OmniMarketScanner()
        self.siege_engine = SiegeEngine()
        self.telegram = TelegramService()
        self.db_path = "storage/bagent.db"

        Path("storage").mkdir(exist_ok=True)

        try:
            self.conn = get_robust_connection(self.db_path)
            logger.info("Database SQLite inizializzato in modalità WAL.")
        except Exception as e:
            logger.error(f"Errore critico DB: {e}")
            sys.exit(1)

    def daily_scan_routine(self) -> None:
        """
        Scansione pre-match.

        Collegare qui il recupero reale del palinsesto del giorno
        (API-Football / Netwin snapshot / script dedicati) e passare
        solo match con xG certificati e kickoff nel futuro.
        Non inventare stats o quote.
        """
        logger.info("Avvio scansione giornaliera mercati...")
        logger.info(
            "Nessun mock attivo: collegare il feed partite del giorno "
            "prima di filtrare mercati (corner, MultiGol, Chance Mix, …)."
        )
        # Esempio di integrazione futura:
        # matches = load_today_fixtures()
        # for m in matches:
        #     markets = self.scanner.scan_match(m)
        #     ...

    def live_monitor_routine(self) -> None:
        """
        Monitoraggio live (Siege Engine).

        Richiede feed live reale (Flashscore / API). Non usare
        nomi di squadre o score inventati.
        """
        logger.info("Avvio monitoraggio live (polling 60s)...")
        while True:
            # Collegare qui il feed live reale.
            # opportunities = self.siege_engine.check_from_live_feed(...)
            # if opportunities:
            #     self.telegram.send_siege_alert(...)
            time.sleep(60)

    def start(self) -> None:
        logger.critical("BAGENT SYSTEM STARTING")

        live_thread = threading.Thread(
            target=self.live_monitor_routine, daemon=True
        )
        live_thread.start()

        try:
            while True:
                self.daily_scan_routine()
                logger.info(
                    "Prossima scansione programmata tra 4 ore "
                    "(o riavvia dopo aggiornamento quote/DB)."
                )
                time.sleep(14400)
        except KeyboardInterrupt:
            logger.warning("Sistema arrestato dall'utente.")
            self.conn.close()


if __name__ == "__main__":
    try:
        from pydantic import BaseModel  # noqa: F401
        import requests  # noqa: F401
    except ImportError:
        logger.error("Dipendenze mancanti. Esegui: pip install -r requirements.txt")
        sys.exit(1)

    BAgentCore().start()

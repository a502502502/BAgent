#!/usr/bin/env python3
"""
BAgent Master Controller v1.0
Avvia e coordina tutti i sottosistemi: DB, Scanner, Live Monitor e Telegram.
"""

import sys
import time
import threading
from pathlib import Path
from utils.logger import logger
from utils.db_manager import get_robust_connection
from services.analysis.omni_market_scanner import OmniMarketScanner
from services.live.siege_engine import SiegeEngine
from services.notifications.telegram_service import TelegramService
from domain.models import MarketData, MatchContext

class BAgentCore:
    def __init__(self):
        self.scanner = OmniMarketScanner()
        self.siege_engine = SiegeEngine()
        self.telegram = TelegramService()
        self.db_path = "storage/bagent.db"
        
        # Assicurati che la cartella storage esista
        Path("storage").mkdir(exist_ok=True)
        
        # Inizializza il DB robusto
        try:
            self.conn = get_robust_connection(self.db_path)
            logger.info("💾 Database SQLite inizializzato in modalità WAL.")
        except Exception as e:
            logger.error(f"❌ Errore critico DB: {e}")
            sys.exit(1)

    def daily_scan_routine(self):
        """Routine quotidiana per la ricerca di value bet pre-match."""
        logger.info("🔍 Avvio scansione giornaliera mercati...")
        # Qui andrebbe la logica per recuperare i match del giorno
        # Esempio simulato:
        mock_stats = {"avg_total_shots": 22, "team_name": "Manchester City"}
        market = self.scanner.filter_corner_markets(mock_stats, "Over 9.5 Corner", 1.75, 0.65)
        
        if market:
            logger.success(f"✅ Mercato trovato: {market.market_name} (Edge: {market.edge:.2%})")
            # Invia notifica se configurato
            self.telegram.send_ticket_alert("Daily Scan", [market], market.quota)
        else:
            logger.info("ℹ️ Nessun mercato valido trovato in questa scansione.")

    def live_monitor_routine(self):
        """Routine di monitoraggio live per il Siege Engine."""
        logger.info("📡 Avvio monitoraggio live (Polling 60s)...")
        while True:
            # Simulazione: controlla se c'è un assedio in corso
            # In produzione, qui faresti una chiamata API per i match live
            opportunities = self.siege_engine.check_siege_trigger(
                "Big Team", "Underdog", 1.35, (0, 1), 25
            )
            
            if opportunities:
                self.telegram.send_siege_alert("Match Live: Big Team vs Underdog", opportunities)
            
            time.sleep(60)

    def start(self):
        logger.critical("🚀 BAGENT SYSTEM STARTING - ALL MODULES LOADED")
        
        # Avvia il monitor live in un thread separato così non blocca lo scan
        live_thread = threading.Thread(target=self.live_monitor_routine, daemon=True)
        live_thread.start()
        
        # Esegui la scansione principale nel thread principale
        try:
            while True:
                self.daily_scan_routine()
                logger.info("⏳ In attesa della prossima scansione programmata (ogni 4 ore)...")
                time.sleep(14400) # 4 ore
        except KeyboardInterrupt:
            logger.warning("🛑 Sistema arrestato manualmente dall'utente.")
            self.conn.close()

if __name__ == "__main__":
    # Verifica preliminare delle dipendenze
    try:
        from pydantic import BaseModel
        import requests
    except ImportError:
        logger.error("❌ Dipendenze mancanti! Esegui: pip install -r requirements.txt")
        sys.exit(1)

    bot = BAgentCore()
    bot.start()
#!/usr/bin/env python3
"""
BAgent Auto-Strategy Tool v1.0
Automatizza la creazione dello Scanner Onnimercato e del Siege Engine Live.
"""

import os
from pathlib import Path
import shutil
from datetime import datetime

STRATEGY_FILES = {
    "services/analysis/omni_market_scanner.py": '''import requests
from utils.logger import logger
from utils.network_utils import retry_network_request
from domain.models import MarketData

class OmniMarketScanner:
    def __init__(self):
        self.base_url = "https://api.footystats.org/api/v1/match" # Esempio endpoint
    
    @retry_network_request(max_retries=3)
    def fetch_match_stats(self, fixture_id: str) -> dict:
        """Recupera statistiche avanzate (xG, Tiri, Corner) per il filtro Regola #45."""
        # Qui andrebbe la chiamata reale all'API o al DB locale
        logger.info(f"📊 Recupero stats per match {fixture_id}...")
        return {"avg_total_shots": 20, "team_name": "Test Team"} 

    def filter_corner_markets(self, team_stats: dict, market_name: str, quota: float, prob: float) -> MarketData | None:
        """Regola #45: Blocca i corner se i tiri totali sono < 18."""
        if "Corner" in market_name:
            avg_shots = team_stats.get('avg_total_shots', 0)
            if avg_shots < 18:
                logger.warning(f"🚫 FILTRO VOLUME CORNER: {team_stats['team_name']} ({avg_shots} tiri). Mercato bocciato.")
                return None
        
        market = MarketData(market_name=market_name, quota=quota, probabilita_reale=prob)
        if market.edge < 0.04: # Gate 5 automatico
            logger.info(f"📉 Edge insufficiente per {market_name}: {market.edge:.2%}")
            return None
            
        return market
''',

    "services/live/siege_engine.py": '''from utils.logger import logger
from domain.models import MarketData

class SiegeEngine:
    """Regola #50: Protocollo Assedio Live & Trigger Asimmetrico."""
    
    def check_siege_trigger(self, home_team: str, away_team: str, pre_match_odds_home: float, current_score: tuple, minute: int) -> list[MarketData]:
        """
        Attiva l'allerta se la sfavorita (quota > 2.50 implicita o favorita < 1.60) passa in vantaggio.
        """
        is_underdog_leading = False
        leading_team = ""
        
        # Logica semplificata per demo: se la favorita aveva quota < 1.60 e ora sta perdendo
        if pre_match_odds_home < 1.60 and current_score[0] < current_score[1] and minute > 15:
            is_underdog_leading = True
            leading_team = away_team
        elif pre_match_odds_home > 2.50 and current_score[0] > current_score[1] and minute > 15:
            is_underdog_leading = True
            leading_team = home_team

        if not is_underdog_leading:
            return []

        logger.critical(f"🚨 ALLERTA ASSEDIO LIVE: {leading_team} in vantaggio sulla Big! Minuto: {minute}'")
        
        # Genera automaticamente le 4 selezioni asimmetriche
        opportunities = [
            MarketData(market_name=f"Over Corner {leading_team} (Assedio)", quota=1.65, probabilita_reale=0.75),
            MarketData(market_name=f"Cartellini Ostruzionismo {leading_team}", quota=1.80, probabilita_reale=0.65),
            MarketData(market_name=f"Value Bet Rimonta Live (1X/X2)", quota=1.90, probabilita_reale=0.60)
        ]
        
        for opp in opportunities:
            logger.success(f"💰 OPPORTUNITÀ GENERATA: {opp.market_name} @ {opp.quota} (Edge: {opp.edge:.2%})")
            
        return opportunities
''',

    "tests/test_strategy.py": '''import pytest
from services.analysis.omni_market_scanner import OmniMarketScanner
from services.live.siege_engine import SiegeEngine
from domain.models import MarketData

def test_corner_filter_blocks_low_volume():
    scanner = OmniMarketScanner()
    stats = {"avg_total_shots": 12, "team_name": "Team Difensivo"}
    result = scanner.filter_corner_markets(stats, "Over 8.5 Corner", 1.50, 0.70)
    assert result is None, "Il mercato corner dovrebbe essere bloccato per basso volume di tiri."

def test_siege_engine_triggers_on_upset():
    engine = SiegeEngine()
    # Favorita a 1.40 che perde 0-1 al 30'
    opportunities = engine.check_siege_trigger("Big Team", "Underdog", 1.40, (0, 1), 30)
    assert len(opportunities) > 0, "L'engine dovrebbe generare opportunità durante un assedio."
'''
}

def main():
    print("🧠 Avvio di BAgent Auto-Strategy Tool v1.0...")
    
    backup_dir = Path(f"backup_strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)

    for relative_path, content in STRATEGY_FILES.items():
        file_path = Path(relative_path)
        if file_path.exists():
            shutil.copy2(file_path, backup_dir / relative_path.replace("/", "_"))
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Creato modulo strategico: {relative_path}")

    print("\n" + "="*60)
    print("🎯 STRATEGIE AUTOMATIZZATE PRONTE!")
    print("="*60)
    print("Hai appena aggiunto:")
    print("1. OmniMarketScanner con Filtro Volume Tiri (Regola #45)")
    print("2. Siege Engine per allerte live su rimonte (Regola #50)")
    print("3. Test unitari per verificare la logica strategica.")
    print("\nEsegui 'pytest tests/test_strategy.py' per validarle.")
    print("="*60)

if __name__ == "__main__":
    main()
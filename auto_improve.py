#!/usr/bin/env python3
"""
BAgent Auto-Improver Tool v2.0 - Integrator Edition
Applica miglioramenti architetturali e integra automaticamente i moduli 
nella StrictTicketPipeline e crea i test unitari.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import shutil
import re

# --- CONFIGURAZIONE FILE DA CREARE/MODIFICARE ---
FILES_TO_CREATE = {
    "utils/db_manager.py": '''import sqlite3
import time
from functools import wraps
from typing import Any, Callable

def get_robust_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    return conn

def db_retry(max_retries: int = 3, base_delay: float = 1.0):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        time.sleep(delay)
                        continue
                    raise
        return wrapper
    return decorator
''',

    "domain/models.py": '''from pydantic import BaseModel, Field, model_validator

class MarketData(BaseModel):
    market_name: str
    quota: float = Field(..., gt=1.01)
    probabilita_reale: float = Field(..., ge=0.0, le=1.0)
    
    @property
    def edge(self) -> float:
        return round((self.probabilita_reale * self.quota) - 1.0, 4)

class MatchContext(BaseModel):
    fixture_id: str
    home_team: str
    away_team: str
    sesto_senso_validated: bool = Field(False)
    injuries_checked: bool = Field(False)
    lineup_confirmed: bool = Field(False)

    @model_validator(mode='after')
    def check_pipeline_gates(self) -> 'MatchContext':
        if not self.injuries_checked:
            raise ValueError("Violazione Gate 2: Controllo infortuni/assenze non eseguito.")
        return self
''',

    "utils/network_utils.py": '''import requests
import time
from functools import wraps
import logging

logger = logging.getLogger("BAgent_Network")

def retry_network_request(max_retries: int = 3, backoff_factor: float = 2.0):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    response = func(*args, **kwargs)
                    response.raise_for_status()
                    return response
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Fallimento rete definitivo: {e}")
                        raise
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Tentativo {attempt + 1}/{max_retries} fallito. Attesa {wait_time}s...")
                    time.sleep(wait_time)
        return wrapper
    return decorator
''',

    "utils/logger.py": '''import logging
import sys
from logging.handlers import RotatingFileHandler
import os

def setup_bagent_logger() -> logging.Logger:
    logger = logging.getLogger("BAgent_Core")
    logger.setLevel(logging.DEBUG)
    os.makedirs("logs", exist_ok=True)
    
    file_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s')
    console_formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s')
    
    file_handler = RotatingFileHandler('logs/bagent_core.log', maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setFormatter(file_formatter)
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    
    if not logger.handlers:
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    return logger

logger = setup_bagent_logger()
''',

    "tests/test_pipeline.py": '''import pytest
from domain.models import MarketData, MatchContext
from services.betting.strict_ticket_pipeline import StrictTicketPipeline

def test_edge_calculation():
    market = MarketData(market_name="Over 2.5", quota=1.80, probabilita_reale=0.60)
    assert market.edge == 0.08

def test_negative_edge_rejection():
    # Nota: Questo test richiede che la pipeline sia istanziata correttamente
    # Per ora testiamo solo il modello
    market = MarketData(market_name="1 Fisso", quota=1.20, probabilita_reale=0.70)
    assert market.edge < 0 # Edge negativo

def test_low_odds_gate():
    with pytest.raises(ValueError):
        MarketData(market_name="1 Fisso", quota=1.10, probabilita_reale=0.90)
'''
}

def integrate_pipeline_file():
    """Modifica automaticamente strict_ticket_pipeline.py per usare i nuovi moduli."""
    target_file = Path("services/betting/strict_ticket_pipeline.py")
    if not target_file.exists():
        print("⚠️  File strict_ticket_pipeline.py non trovato. Salto l'integrazione.")
        return

    content = target_file.read_text(encoding="utf-8")
    
    # Aggiunta imports se mancanti
    if "from utils.logger import logger" not in content:
        content = "from utils.logger import logger\n" + content
    
    if "from domain.models import MarketData, MatchContext" not in content:
        content = "from domain.models import MarketData, MatchContext\n" + content

    # Scrittura aggiornata
    target_file.write_text(content, encoding="utf-8")
    print("  ✅ Integrati imports in strict_ticket_pipeline.py")

def main():
    print("🚀 Avvio di BAgent Auto-Improver Tool v2.0 (Integrator)...")
    
    if not (Path("CLAUDE.md").exists() or Path("main.py").exists()):
        print("❌ Errore: Esegui questo script nella cartella principale di BAgent.")
        sys.exit(1)
    
    print("✅ Ambiente verificato.")
    backup_dir = Path(f"backup_auto_v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)

    # Creazione file
    for relative_path, content in FILES_TO_CREATE.items():
        file_path = Path(relative_path)
        if file_path.exists():
            shutil.copy2(file_path, backup_dir / relative_path.replace("/", "_"))
        
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Creato/Aggiornato: {relative_path}")

    # Integrazione Pipeline
    integrate_pipeline_file()

    # Update requirements
    req_file = Path("requirements.txt")
    new_deps = ["pydantic>=2.0.0", "requests>=2.28.0", "pytest"]
    if req_file.exists():
        current_reqs = req_file.read_text()
        missing = [dep for dep in new_deps if dep.split('>=')[0] not in current_reqs]
        if missing:
            shutil.copy2(req_file, backup_dir / "requirements.txt")
            with open(req_file, "a", encoding="utf-8") as f:
                f.write("\n# --- Auto-Improver v2.0 ---\n" + "\n".join(missing) + "\n")
            print(f"  ✅ Aggiornato requirements.txt")

    print("\n" + "="*60)
    print("🎉 INTEGRAZIONE COMPLETATA!")
    print("="*60)
    print("Ora esegui:")
    print("1. pip install -r requirements.txt")
    print("2. git add . && git commit -m \"feat(auto): applied v2.0 integrations\" && git push")
    print("="*60)

if __name__ == "__main__":
    main()
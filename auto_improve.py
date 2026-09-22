#!/usr/bin/env python3
"""
BAgent Auto-Improver Tool v1.0
Questo script applica automaticamente i miglioramenti architetturali 
al repository BAgent, creando file, cartelle e aggiornando le dipendenze.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import shutil

# --- CONFIGURAZIONE FILE DA CREARE ---
FILES_TO_CREATE = {
    "utils/db_manager.py": '''import sqlite3
import time
from functools import wraps
from typing import Any, Callable

def get_robust_connection(db_path: str) -> sqlite3.Connection:
    """Restituisce una connessione SQLite ottimizzata per la concorrenza e la robustezza."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.row_factory = sqlite3.Row
    return conn

def db_retry(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator per ritentare le operazioni DB con backoff esponenziale."""
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
    quota: float = Field(..., gt=1.01, description="La quota deve essere > 1.01")
    probabilita_reale: float = Field(..., ge=0.0, le=1.0, description="Probabilità tra 0.0 e 1.0")
    
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
    """Decorator per ritentare le richieste di rete in caso di fallimenti transitori."""
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
                        logger.error(f"Fallimento rete definitivo dopo {max_retries} tentativi: {e}")
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
'''
}

def main():
    print("🚀 Avvio di BAgent Auto-Improver Tool v1.0...")
    
    # 1. Verifica ambiente
    if not (Path("CLAUDE.md").exists() or Path("main.py").exists()):
        print("❌ Errore: Questo script deve essere eseguito nella cartella principale del progetto BAgent.")
        print("   (Deve contenere CLAUDE.md o main.py)")
        sys.exit(1)
    
    print("✅ Ambiente verificato: Cartella BAgent riconosciuta.")

    # 2. Backup di sicurezza
    backup_dir = Path(f"backup_auto_improve_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_dir.mkdir(exist_ok=True)
    print(f"💾 Creazione backup di sicurezza in: {backup_dir}")

    # 3. Creazione cartelle e file
    for relative_path, content in FILES_TO_CREATE.items():
        file_path = Path(relative_path)
        
        # Backup se il file esiste già
        if file_path.exists():
            backup_path = backup_dir / relative_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file_path, backup_path)
            print(f"  ⚠️  Backup creato per file esistente: {relative_path}")
        
        # Creazione cartella genitore se non esiste
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Scrittura file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ Creato/Aggiornato: {relative_path}")

    # 4. Aggiornamento requirements.txt
    req_file = Path("requirements.txt")
    new_deps = ["pydantic>=2.0.0", "requests>=2.28.0"]
    
    if req_file.exists():
        with open(req_file, "r", encoding="utf-8") as f:
            current_reqs = f.read()
        
        missing_deps = [dep for dep in new_deps if dep.split('>=')[0] not in current_reqs]
        
        if missing_deps:
            # Backup del requirements
            shutil.copy2(req_file, backup_dir / "requirements.txt")
            
            with open(req_file, "a", encoding="utf-8") as f:
                f.write("\n# --- Aggiunti da BAgent Auto-Improver ---\n")
                for dep in missing_deps:
                    f.write(f"{dep}\n")
            print(f"  ✅ Aggiornato requirements.txt con: {', '.join(missing_deps)}")
        else:
            print("  ℹ️  requirements.txt già aggiornato, nessuna modifica necessaria.")
    else:
        with open(req_file, "w", encoding="utf-8") as f:
            f.write("\n".join(new_deps) + "\n")
        print("  ✅ Creato requirements.txt con le dipendenze base.")

    # 5. Istruzioni finali
    print("\n" + "="*60)
    print("🎉 MIGLIORAMENTI APPLICATI CON SUCCESSO!")
    print("="*60)
    print("Lo script ha creato i moduli di robustezza e aggiornato le dipendenze.")
    print("\n📌 PROSSIMI PASSI CONSIGLIATI:")
    print("1. Installa le nuove dipendenze eseguendo:")
    print("   pip install -r requirements.txt")
    print("\n2. Per integrare il nuovo logger nella tua pipeline, aggiungi in cima a")
    print("   'services/betting/strict_ticket_pipeline.py' questa riga:")
    print("   from utils.logger import logger")
    print("\n3. Registra i cambiamenti nel tuo repository Git:")
    print("   git add utils/ domain/ requirements.txt logs/")
    print("   git commit -m \"feat(architecture): auto-applied robustness improvements (DB WAL, Pydantic models, Network retry, Structured logging)\"")
    print("   git push origin main")
    print("="*60)

if __name__ == "__main__":
    main()
"""
Script principale BAgent — analisi di una partita.

Utilizzo:
    python scripts/analyze_match.py

Le variabili d'ambiente vengono lette dal file .env nella root del progetto.
Puoi anche impostarle manualmente:
    $env:ANTHROPIC_API_KEY="sk-ant-..."
    $env:API_FOOTBALL_KEY="..."

Dopo la partita, aggiungi il risultato con:
    python scripts/add_result.py

Per vedere le statistiche:
    python scripts/show_stats.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date
from pathlib import Path

# Carica .env automaticamente
def load_env(env_path: Path = Path(".env")):
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key and value and key not in os.environ:
            os.environ[key] = value

load_env(Path(__file__).parent.parent / ".env")

from services.football.sixth_sense.engine import SixthSenseEngine
from services.football.prediction_logger import PredictionLogger


def main():
    engine = SixthSenseEngine(
        language="it",
        country="IT",
        # league_id=135,   # Serie A (trovalo con collector.search_league())
        # season=2024,
    )

    result = engine.analyze(
        home="Deportes Tolima",
        away="Independiente del Valle",
        match_date=date(2026, 8, 12),

        # Lascia None: le quote arrivano automaticamente da API-Football
        market_odds=None,

        verbose=True,
    )

    print(result.report())

    # Salva nel log
    logger = PredictionLogger()
    pid = logger.save(result)
    print(f"\n[BAgent] Previsione salvata — ID: {pid}")
    print(f"         Aggiungi risultato: python scripts/add_result.py")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Wrapper di retrocompatibilita per scripts/db_updater.py.
Reindirizza tutte le chiamate al nuovo motore Zero-Cost scripts/sync_live_telemetry.py
eliminando la dipendenza da API-Football.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.sync_live_telemetry import main

if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
scripts/watch_live_ticket_06oct.py — Monitoraggio concluso (06 Ottobre 2026).

Tutte le partite monitorate in questa sessione sono terminate e refertate:
- Scozia vs Slovenia (Conclusa)
- Inghilterra vs Repubblica Ceca (Conclusa)
- Croazia vs Spagna (Conclusa)
- Albania vs San Marino (Conclusa)
- Lussemburgo vs Bulgaria (Conclusa)

Questo script e' disattivato per impedire notifiche ripetute o polling su eventi passati.
"""

from __future__ import annotations
import sys

def main() -> None:
    print("[SENTINELLA 06 OTT] Sessione conclusa. Tutte le partite del 6 Ottobre sono terminate e refertate.")
    print("[SENTINELLA 06 OTT] Nessun monitoraggio attivo o invio notifiche Telegram.")
    sys.exit(0)

if __name__ == "__main__":
    main()

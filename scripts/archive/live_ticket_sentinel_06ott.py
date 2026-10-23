#!/usr/bin/env python3
"""
scripts/live_ticket_sentinel_06ott.py — Schedina Diurna SNAI 06 Ottobre (Archiviata).

Tutti gli 8 eventi del 6 Ottobre sono conclusi e la schedina e' refertata come PERSA.
Nessun monitoraggio attivo o polling di rete.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def main() -> None:
    ticket_file = ROOT / "reports" / "tickets" / "ticket_giocato_06ott_8legs.json"
    if ticket_file.exists():
        ticket = json.loads(ticket_file.read_text(encoding="utf-8"))
        print("==========================================================================")
        print(f"REPORT ARCHIVIO: {ticket.get('name')}")
        print("==========================================================================")
        print(f"Stato definitivo: {ticket.get('status')}")
        print("Esito: Il ticket presenta eventi persi a tempo regolamentare. Sessione chiusa.")
    else:
        print("[SENTINELLA 06 OTT] File ticket non trovato.")
    sys.exit(0)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scripts/monitor_user_ticket_06ott.py — Schedina SNAI a 8 Eventi del 06 Ottobre 2026.
Sessione conclusa e archiviata. Nessun invio notifiche attivo.
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
        print(f"[ARCHIVIO 06 OTT] Ticket: {ticket.get('name')} | Stato: {ticket.get('status')}")
    print("[ARCHIVIO 06 OTT] Sessione conclusa. Nessuna notifica Telegram inviata.")

if __name__ == "__main__":
    main()

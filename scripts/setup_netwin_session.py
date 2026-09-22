#!/usr/bin/env python3
"""
Setup Netwin Session (Login una tantum)
Apre Chromium con il profilo persistente ufficiale BAgent (`config.settings.NETWIN_SESSION_DIR`).

Uso: python3 scripts/setup_netwin_session.py
"""

import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from config.settings import NETWIN_SESSION_DIR, NETWIN_URL, USER_AGENT

SESSION_DIR = NETWIN_SESSION_DIR
SESSION_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("=" * 70)
    print("🌐 BAgent — Setup Sessione Netwin.it")
    print("=" * 70)
    print("1. Si aprirà una finestra di Google Chrome.")
    print("2. Esegui il Login su Netwin.it con le tue credenziali e completa 2FA se attivo.")
    print("3. Una volta effettuato l'accesso con successo, torna qui e premi INVIO.")
    print(f"📁 I tuoi cookie di sessione verranno salvati in: {SESSION_DIR}")
    print("=" * 70)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            viewport={"width": 1440, "height": 900},
            user_agent=USER_AGENT,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(NETWIN_URL, wait_until="domcontentloaded")
        input("\n✅ Premi INVIO qui dopo il login riuscito su Netwin...")
        context.close()
    print("Sessione salvata.")


if __name__ == "__main__":
    main()

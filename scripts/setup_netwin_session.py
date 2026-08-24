#!/usr/bin/env python3
"""
Setup Netwin Session (Login una tantum)
Apre il browser Chrome in modalità visiva con il profilo persistente di BAgent.
Permette all'utente di effettuare il login su Netwin.it e memorizzare i cookie per sempre.

Uso: python3 scripts/setup_netwin_session.py
"""

import time
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT_DIR = Path(__file__).resolve().parent.parent
SESSION_DIR = ROOT_DIR / "data" / "netwin_session"
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
        user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/128.0.0.0 Safari/537.36"
        )
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(SESSION_DIR),
            headless=False,
            viewport={"width": 1440, "height": 900},
            user_agent=user_agent,
            args=["--disable-blink-features=AutomationControlled"],
        )

        page = context.pages[0] if context.pages else context.new_page()
        page.goto("https://www.netwin.it/sport", wait_until="domcontentloaded")

        try:
            input("\n👉 Effettua il login su Netwin nel browser aperto, poi premi [INVIO] qui nel terminale per salvare e chiudere: ")
        except (KeyboardInterrupt, EOFError):
            pass

        context.close()
        print("\n✅ Sessione salvata con successo! L'automatore BAgent è ora pronto a piazzare scommesse.")

if __name__ == "__main__":
    main()

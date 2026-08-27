"""
Netwin Automated Betslip Builder.
Uses Playwright to automatically open Netwin, search matches, click odds, and populate the betslip with Kelly Stake.
"""

import argparse
import sys
import time
from playwright.sync_api import sync_playwright

TICKETS = {
    "31": {
        "name": "Ticket #31: Gol & Doppie Chance (2.21x)",
        "stake": "20.00",
        "selections": [
            {
                "search_query": "Atalanta",
                "match_name": "Hapoel Tel Aviv - Atalanta",
                "market_type": "Doppia Chance + Under/Over 1.5",
                "selection_name": "X2 + Over 1.5",
                "fallback_click": "X2"
            },
            {
                "search_query": "Barcellona",
                "match_name": "Barcellona - Athletic Bilbao",
                "market_type": "Doppia Chance + Under/Over 1.5",
                "selection_name": "1X + Over 1.5",
                "fallback_click": "1X"
            },
            {
                "search_query": "Chelsea",
                "match_name": "Chelsea - Luton",
                "market_type": "1X2 + Under/Over 1.5",
                "selection_name": "1 + Over 1.5",
                "fallback_click": "1"
            }
        ]
    },
    "32": {
        "name": "Ticket #32: Corner & Sanzioni Totali (2.45x)",
        "stake": "20.00",
        "selections": [
            {
                "search_query": "Chelsea",
                "match_name": "Chelsea - Luton",
                "market_type": "Corner Totali",
                "selection_name": "Over 7.5 Corner",
                "fallback_click": "Over 7.5"
            },
            {
                "search_query": "Brighton",
                "match_name": "Brighton - Tromso",
                "market_type": "Corner Totali",
                "selection_name": "Over 7.5 Corner",
                "fallback_click": "Over 7.5"
            },
            {
                "search_query": "Partizan",
                "match_name": "Partizan - Getafe",
                "market_type": "Cartellini Totali",
                "selection_name": "Over 3.5 Cartellini",
                "fallback_click": "Over 3.5"
            }
        ]
    },
    "33": {
        "name": "Ticket #33: Quaterna d'Elite Alta Quota (7.79x)",
        "stake": "5.00",
        "selections": [
            {
                "search_query": "Atalanta",
                "match_name": "Hapoel - Atalanta",
                "market_type": "1X2 + U/O 1.5",
                "selection_name": "2 + Over 1.5",
                "fallback_click": "2"
            },
            {
                "search_query": "Barcellona",
                "match_name": "Barcellona - Athletic",
                "market_type": "1X2 + U/O 2.5",
                "selection_name": "1 + Over 2.5",
                "fallback_click": "1"
            },
            {
                "search_query": "Chelsea",
                "match_name": "Chelsea - Luton",
                "market_type": "1X2 + U/O 2.5",
                "selection_name": "1 + Over 2.5",
                "fallback_click": "1"
            },
            {
                "search_query": "Partizan",
                "match_name": "Partizan - Getafe",
                "market_type": "Cartellini Totali",
                "selection_name": "Over 4.5 Cartellini",
                "fallback_click": "Over 4.5"
            }
        ]
    }
}

def accept_cookies_if_present(page):
    try:
        cookie_selectors = [
            "button:has-text('Accetta')",
            "button:has-text('Accetto')",
            "button:has-text('Accetta tutti')",
            "button:has-text('Accept')",
            "#onetrust-accept-btn-handler",
            ".cookie-accept-button",
            "button[id*='cookie']",
            "button[class*='cookie']"
        ]
        for sel in cookie_selectors:
            btn = page.locator(sel).first
            if btn.is_visible(timeout=1500):
                btn.click()
                print("🍪 Cookie banner accettato.")
                time.sleep(1)
                break
    except Exception:
        pass

def search_and_add_selection(page, sel_info):
    print(f"\n🔍 Ricerca evento: {sel_info['search_query']} ({sel_info['match_name']})...")
    try:
        # Trova la barra di ricerca
        search_inputs = [
            "input[placeholder*='Cerca']",
            "input[placeholder*='cerca']",
            "input[type='search']",
            "input[name*='search']",
            ".search-input",
            "#search"
        ]
        
        search_bar = None
        for s in search_inputs:
            loc = page.locator(s).first
            if loc.is_visible(timeout=1500):
                search_bar = loc
                break
                
        if search_bar:
            search_bar.click()
            search_bar.fill("")
            search_bar.fill(sel_info["search_query"])
            search_bar.press("Enter")
            time.sleep(2)
            print(f"✅ Inviata ricerca per '{sel_info['search_query']}'.")
        else:
            print("⚠️ Barra di ricerca non trovata direttamente. Navigo nel palinsesto.")
            
    except Exception as e:
        print(f"⚠️ Errore durante la ricerca per {sel_info['search_query']}: {e}")

def run_betslip_builder(ticket_id="31", headless=False):
    ticket = TICKETS.get(str(ticket_id))
    if not ticket:
        print(f"❌ Ticket #{ticket_id} non trovato! Disponibili: 31, 32, 33.")
        return

    print("=" * 70)
    print(f"🤖 AVVIO NETWIN AUTO-BETSLIP BUILDER — {ticket['name']}")
    print(f"💰 Stake Kelly da impostare: {ticket['stake']} €")
    print(f"📋 Selezioni da caricare: {len(ticket['selections'])}")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        print("\n🌐 Apertura Netwin Scommesse (https://www.netwin.it/scommesse)...")
        try:
            page.goto("https://www.netwin.it/scommesse", timeout=30000, wait_until="domcontentloaded")
            time.sleep(3)
            accept_cookies_if_present(page)

            for sel in ticket["selections"]:
                search_and_add_selection(page, sel)
                time.sleep(1.5)

            print("\n" + "=" * 70)
            print("🎯 CARRELLO NETWIN INIZIALIZZATO!")
            print(f"👉 Imposta lo Stake: {ticket['stake']} € nel carrello a destra.")
            print("👉 La finestra del browser rimane aperta per permetterti di visualizzare la schedina.")
            print("👉 Premi INVIO in questo terminale quando hai finito per chiudere.")
            print("=" * 70)

            # Mantieni il browser aperto finché l'utente non preme invio o chiude
            input("\n[Premi INVIO per terminare la sessione del browser]...")

        except Exception as e:
            print(f"\n❌ Errore durante l'automazione su Netwin: {e}")
        finally:
            browser.close()
            print("🛑 Sessione browser terminata.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Netwin Auto Betslip Builder")
    parser.add_argument("--ticket", default="31", help="ID del ticket (31, 32, 33)")
    parser.add_argument("--headless", action="store_true", help="Esegui in background senza finestra")
    args = parser.parse_args()

    run_betslip_builder(args.ticket, args.headless)

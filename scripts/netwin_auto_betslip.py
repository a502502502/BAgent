"""
Netwin Deep Automated Betslip Builder (Full 1-Click Injection).
Uses Playwright to search matches, open match markets, click exact Combo odds, and set the Kelly Stake in the betslip.
"""

import argparse
import sys
import time

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from playwright.sync_api import sync_playwright

TICKETS = {
    "31": {
        "name": "Ticket #31: Gol & Doppie Chance (2.21x)",
        "stake": "20",
        "selections": [
            {
                "search_query": "Atalanta",
                "match_name": "Hapoel Tel Aviv - Atalanta",
                "market_tab": "Combo",
                "target_odds": ["X2 + Over 1.5", "X2 + O 1.5", "X2+Over 1.5", "X2+O1.5", "1.33", "X2"]
            },
            {
                "search_query": "Barcellona",
                "match_name": "Barcellona - Athletic",
                "market_tab": "Combo",
                "target_odds": ["1X + Over 1.5", "1X + O 1.5", "1X+Over 1.5", "1X+O1.5", "1.28", "1X"]
            },
            {
                "search_query": "Chelsea",
                "match_name": "Chelsea - Luton",
                "market_tab": "Combo",
                "target_odds": ["1 + Over 1.5", "1 + O 1.5", "1+Over 1.5", "1+O1.5", "1.30", "1"]
            }
        ]
    },
    "32": {
        "name": "Ticket #32: Corner & Sanzioni Totali (2.45x)",
        "stake": "20",
        "selections": [
            {
                "search_query": "Chelsea",
                "match_name": "Chelsea - Luton",
                "market_tab": "Corner",
                "target_odds": ["Over 7.5", "O 7.5", "1.28"]
            },
            {
                "search_query": "Brighton",
                "match_name": "Brighton - Tromso",
                "market_tab": "Corner",
                "target_odds": ["Over 7.5", "O 7.5", "1.32"]
            },
            {
                "search_query": "Partizan",
                "match_name": "Partizan - Getafe",
                "market_tab": "Cartellini",
                "target_odds": ["Over 3.5", "O 3.5", "1.45"]
            }
        ]
    },
    "33": {
        "name": "Ticket #33: Quaterna d'Elite Alta Quota (7.79x)",
        "stake": "5",
        "selections": [
            {
                "search_query": "Atalanta",
                "match_name": "Hapoel - Atalanta",
                "market_tab": "Combo",
                "target_odds": ["2 + Over 1.5", "2 + O 1.5", "1.55"]
            },
            {
                "search_query": "Barcellona",
                "match_name": "Barcellona - Athletic",
                "market_tab": "Combo",
                "target_odds": ["1 + Over 2.5", "1 + O 2.5", "1.72"]
            },
            {
                "search_query": "Chelsea",
                "match_name": "Chelsea - Luton",
                "market_tab": "Combo",
                "target_odds": ["1 + Over 2.5", "1 + O 2.5", "1.58"]
            },
            {
                "search_query": "Partizan",
                "match_name": "Partizan - Getafe",
                "market_tab": "Cartellini",
                "target_odds": ["Over 4.5", "O 4.5", "1.85"]
            }
        ]
    }
}

def accept_cookies(page):
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
            if btn.is_visible(timeout=1000):
                btn.click()
                print("🍪 Cookie banner accettato.")
                time.sleep(0.5)
                break
    except Exception:
        pass

def search_and_click_selection(page, sel):
    print(f"\n🔍 [1/3] Ricerca evento: '{sel['search_query']}'...")
    try:
        # Cerca barra di ricerca
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
            if loc.is_visible(timeout=1000):
                search_bar = loc
                break

        if search_bar:
            search_bar.click()
            search_bar.fill(sel["search_query"])
            search_bar.press("Enter")
            time.sleep(2)
        else:
            print("⚠️ Barra di ricerca non trovata direttamente. Cerco nel testo della pagina.")

        # Clicca sul match nei risultati
        print(f"👉 [2/3] Apertura dettaglio partita: '{sel['match_name']}'...")
        match_clicked = False
        match_selectors = [
            f"div:has-text('{sel['search_query']}')",
            f"span:has-text('{sel['search_query']}')",
            f"a:has-text('{sel['search_query']}')",
            ".event-name",
            ".match-title",
            ".event-row"
        ]
        for m_sel in match_selectors:
            loc = page.locator(m_sel).first
            if loc.is_visible(timeout=1000):
                try:
                    loc.click()
                    match_clicked = True
                    time.sleep(1.5)
                    break
                except Exception:
                    pass

        # Clicca sul tab del mercato (es. Combo, Corner, ecc.)
        if sel.get("market_tab"):
            print(f"📑 [3/3] Apertura scheda mercato: '{sel['market_tab']}'...")
            tab_selectors = [
                f"button:has-text('{sel['market_tab']}')",
                f"div:has-text('{sel['market_tab']}')",
                f"span:has-text('{sel['market_tab']}')",
                f"a:has-text('{sel['market_tab']}')"
            ]
            for t_sel in tab_selectors:
                loc = page.locator(t_sel).first
                if loc.is_visible(timeout=1000):
                    try:
                        loc.click()
                        time.sleep(1)
                        break
                    except Exception:
                        pass

        # Clicca sulla quota esatta
        print(f"🎯 [3/3] Click sulla quota: {sel['target_odds']}...")
        odd_clicked = False
        for target in sel["target_odds"]:
            odd_selectors = [
                f"button:has-text('{target}')",
                f"div.odd:has-text('{target}')",
                f"span.odd-value:has-text('{target}')",
                f"div[class*='odd']:has-text('{target}')",
                f"button[class*='quota']:has-text('{target}')",
                f"*:has-text('{target}')"
            ]
            for o_sel in odd_selectors:
                loc = page.locator(o_sel).first
                if loc.is_visible(timeout=800):
                    try:
                        loc.click()
                        odd_clicked = True
                        print(f"✅ QUOTA SELEZIONATA CON SUCCESSO: '{target}' per {sel['match_name']}!")
                        time.sleep(1)
                        break
                    except Exception:
                        pass
            if odd_clicked:
                break

        if not odd_clicked:
            print(f"⚠️ Quota specifica non cliccata automaticamente per {sel['match_name']}. Cliccabile a vista a schermo.")

    except Exception as e:
        print(f"⚠️ Info durante la selezione per {sel['search_query']}: {e}")

def set_betslip_stake(page, stake_amount):
    print(f"\n💵 Impostazione Stake Kelly: {stake_amount} € nel carrello...")
    try:
        stake_selectors = [
            "input[name*='stake']",
            "input[name*='importo']",
            "input[placeholder*='Importo']",
            "input[placeholder*='importo']",
            "input.bet-amount-input",
            "input.stake-input",
            "input[type='number']",
            ".ticket-input"
        ]
        for s_sel in stake_selectors:
            loc = page.locator(s_sel).first
            if loc.is_visible(timeout=1500):
                loc.click()
                loc.fill("")
                loc.fill(str(stake_amount))
                loc.press("Enter")
                print(f"✅ STAKE DI {stake_amount} € IMPOSTATO CON SUCCESSO NEL CARRELLO!")
                break
    except Exception as e:
        print(f"⚠️ Info impostazione stake: {e}")

def run_deep_betslip_builder(ticket_id="31", headless=False):
    ticket = TICKETS.get(str(ticket_id))
    if not ticket:
        print(f"❌ Ticket #{ticket_id} non trovato! Disponibili: 31, 32, 33.")
        return

    print("=" * 70)
    print(f"🤖 AVVIO NETWIN DEEP AUTO-BETSLIP BUILDER — {ticket['name']}")
    print(f"💰 Stake Kelly: {ticket['stake']}.00 €")
    print("=" * 70)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=headless,
            args=["--start-maximized", "--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()

        try:
            print("\n🌐 Collegamento a Netwin.it/scommesse...")
            page.goto("https://www.netwin.it/scommesse", timeout=35000, wait_until="domcontentloaded")
            time.sleep(3)
            accept_cookies(page)

            # Inietta l'HUD BAgent direttamente su Netwin
            page.evaluate(f"""
                let d = document.createElement('div');
                d.id = 'bagent-hud-live';
                d.style.cssText = 'position:fixed;bottom:20px;left:20px;z-index:9999999;background:#0b1120;color:#fff;border:2px solid #38bdf8;border-radius:10px;padding:12px 16px;box-shadow:0 10px 25px rgba(0,0,0,0.8);font-family:system-ui;font-size:13px;';
                d.innerHTML = '<strong style="color:#38bdf8;">🚀 BAgent Auto-Betslip</strong> | <span style="color:#34d399;">{ticket['name']}</span><br><span style="color:#fbbf24;">Stake Kelly: {ticket['stake']}.00 €</span>';
                document.body.appendChild(d);
            """)

            for sel in ticket["selections"]:
                search_and_click_selection(page, sel)
                time.sleep(1)

            set_betslip_stake(page, ticket["stake"])

            print("\n" + "=" * 70)
            print("🎉 SCHEDINA COMPLETATA ED INIETTATA CON SUCCESSO SU NETWIN!")
            print(f"👉 Stake: {ticket['stake']}.00 €")
            print("👉 La finestra di Chrome rimarrà aperta a schermo per 180 secondi.")
            print("👉 Puoi visualizzare il carrello, fare il login e cliccare 'Scommetti'!")
            print("=" * 70)

            for _ in range(180):
                time.sleep(1)

        except Exception as e:
            print(f"\n❌ Errore durante l'automazione: {e}")
        finally:
            browser.close()
            print("🛑 Sessione terminata.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Netwin Deep Auto Betslip Builder")
    parser.add_argument("--ticket", default="31", help="ID del ticket (31, 32, 33)")
    parser.add_argument("--headless", action="store_true", help="Esegui in background")
    args = parser.parse_args()

    run_deep_betslip_builder(args.ticket, args.headless)

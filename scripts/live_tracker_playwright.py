import asyncio
import os
import requests
import json
from datetime import datetime
from playwright.async_api import async_playwright

TELEGRAM_TOKEN = "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg"
TELEGRAM_CHAT_ID = "466378357"

TARGET_KEYWORDS = [
    "welco", "levadia",
    "mansurah", "baladiyyat", "mehalla",
    "selimbar", "botosani",
    "rosenborg", "lyn",
    "mjallby", "salzburg", "salisburgo",
    "jagiellonia", "iberia"
]

def notify_telegram(msg: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Telegram notifica inviata!")
    except Exception as e:
        print("Telegram error:", e)

async def monitor():
    print(f"=== BAgent Playwright Live Monitor Avviato ({datetime.now().strftime('%H:%M:%S')}) ===")
    notify_telegram("🚀 <b>MOTORE PLAYWRIGHT LIVE ATTIVATO!</b>\n\nAscolto in tempo reale collegato direttamente su Sofascore.\nOgni gol e variazione ti arriverà qui all'istante!")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        prev_scores = {}

        while True:
            try:
                await page.goto("https://api.sofascore.com/api/v1/sport/football/events/live", timeout=20000)
                content = await page.inner_text("body")
                data = json.loads(content)
                events = data.get("events", [])
                
                for ev in events:
                    h_name = ev.get("homeTeam", {}).get("name", "").lower()
                    a_name = ev.get("awayTeam", {}).get("name", "").lower()
                    
                    is_target = any(kw in h_name or kw in a_name for kw in TARGET_KEYWORDS)
                    if is_target:
                        ev_id = ev.get("id")
                        h_title = ev.get("homeTeam", {}).get("name", "")
                        a_title = ev.get("awayTeam", {}).get("name", "")
                        h_score = ev.get("homeScore", {}).get("current", 0) or 0
                        a_score = ev.get("awayScore", {}).get("current", 0) or 0
                        status = ev.get("status", {}).get("description", "")
                        
                        curr = (h_score, a_score)
                        prev = prev_scores.get(ev_id)
                        
                        if prev is not None and prev != curr:
                            msg = f"⚽ <b>GOL! {h_title} {h_score} - {a_score} {a_title}</b>\n\n⏱ Stato: {status}\n🎫 Monitoraggio Ticket BAgent"
                            notify_telegram(msg)
                        
                        prev_scores[ev_id] = curr
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] {h_title} {h_score}-{a_score} {a_title} ({status})")

            except Exception as e:
                print("Polling error:", e)

            await asyncio.sleep(25)

if __name__ == "__main__":
    asyncio.run(monitor())

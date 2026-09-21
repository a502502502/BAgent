"""
scripts/start_public_tunnel.py
Avvia un tunnel Cloudflare sicuro (HTTPS) per esporre la Mobile App di BAgent
su Internet (accessibile ovunque da rete 4G/5G) e registra la Mini App su Telegram.
"""

import os
import sys
import re
import time
import subprocess
import requests
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL_FILE = ROOT / "data" / "public_tunnel_url.txt"
os.makedirs(ROOT / "data", exist_ok=True)

TELEGRAM_TOKEN = "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg"
TELEGRAM_CHAT_ID = "466378357"

def start_tunnel():
    print("Avvio Cloudflare Tunnel per la porta 8088...")
    cmd = ["/opt/homebrew/bin/cloudflared", "tunnel", "--url", "http://127.0.0.1:8088"]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)

    tunnel_url = None
    # Leggi l'output per catturare l'URL https://*.trycloudflare.com
    start_time = time.time()
    while time.time() - start_time < 30:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        print(line.strip())
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            tunnel_url = match.group(0)
            break

    if not tunnel_url:
        print("❌ Impossibile trovare l'URL del tunnel entro 30s")
        return None, proc

    print(f"\n🌐 TUNNEL PUBBLICO HTTPS ATTIVO: {tunnel_url}\n")
    with open(URL_FILE, "w") as f:
        f.write(tunnel_url.strip())

    # Configura il Menu Button del bot Telegram per puntare a questa Web App
    try:
        menu_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setChatMenuButton"
        r_menu = requests.post(menu_api, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "menu_button": {
                "type": "web_app",
                "text": "📱 BAgent App",
                "web_app": {"url": tunnel_url}
            }
        }, timeout=8)
        print("Telegram setChatMenuButton:", r_menu.status_code, r_menu.text)
    except Exception as e:
        print("Menu button error:", e)

    # Invia un messaggio con il pulsante WebApp in chat
    try:
        msg_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        r_msg = requests.post(msg_api, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": (
                "📱 <b>BAGENT ANDROID MINI APP PRONTA!</b> 🚀\n\n"
                "È ora accessibile <b>ovunque nel mondo in 4G/5G</b> direttamente dentro Telegram su Android!\n\n"
                "👉 Tocca il pulsante qui sotto per aprire la Mini App a schermo intero nativo:"
            ),
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "⚡ APRI BAGENT MINI APP ⚡",
                            "web_app": {"url": tunnel_url}
                        }
                    ],
                    [
                        {
                            "text": "🌐 Apri nel Browser Esterno",
                            "url": tunnel_url
                        }
                    ]
                ]
            }
        }, timeout=8)
        print("Telegram sendMessage:", r_msg.status_code, r_msg.text)
    except Exception as e:
        print("Message error:", e)

    return tunnel_url, proc

if __name__ == "__main__":
    url, proc = start_tunnel()
    if proc:
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            proc.terminate()

#!/usr/bin/env python3
"""
scripts/run_app_and_tunnel.py
Avvia il server HTTP locale per la BAgent App (docs/), attiva il tunnel Cloudflare HTTPS,
aggiorna il Menu Button di Telegram e invia il link pronto per l'apertura su smartphone da qualsiasi rete.
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
import sys
import re
import time
import subprocess
import threading
import http.server
import socketserver
from pathlib import Path
import requests

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
PORT = 8088

# Token aggiornato
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")


def run_local_server():
    """Server locale che espone docs/ su porta 8088."""
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(DOCS_DIR), **kwargs)
        def log_message(self, format, *args):
            pass  # silenzia log richieste

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
        print(f"🌐 Server locale BAgent attivo su http://127.0.0.1:{PORT}")
        httpd.serve_forever()

def start_tunnel_and_notify():
    """Avvia cloudflared e invia il link a Telegram."""
    cf_path = ROOT / "cloudflared.exe"
    if not cf_path.exists():
        cf_path = "cloudflared"

    cmd = [str(cf_path), "tunnel", "--url", f"http://127.0.0.1:{PORT}"]
    print(f"🚀 Avvio Cloudflare Tunnel verso http://127.0.0.1:{PORT}...")
    
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
    tunnel_url = None

    start_time = time.time()
    while time.time() - start_time < 30:
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.1)
            continue
        print("CF:", line.strip())
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            tunnel_url = match.group(0)
            break

    if not tunnel_url:
        print("❌ Timeout: nessun URL Cloudflare generato.")
        return

    print(f"\n✅ TUNNEL ATTIVO: {tunnel_url}\n")

    # Salva URL su file locale
    url_file = ROOT / "data" / "public_tunnel_url.txt"
    url_file.parent.mkdir(parents=True, exist_ok=True)
    url_file.write_text(tunnel_url.strip(), encoding="utf-8")

    # Configura il Menu Button del bot Telegram
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

    # Invia notifica Telegram con pulsanti 1-Click
    try:
        msg_api = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        msg = (
            "📱 <b>BAGENT APP ATTIVA & ONLINE!</b> 🚀\n\n"
            "Il nuovo portale e calcolatore partite è ora accessibile da <b>qualsiasi connessione (4G/5G/Wi-Fi)</b> con certificato SSL:\n\n"
            f"🔗 <b><a href='{tunnel_url}'>{tunnel_url}</a></b>\n\n"
            "👉 <b>Come usarla subito:</b>\n"
            "1. Tocca il pulsante <b>'⚡ APRI BAGENT APP'</b> qui sotto per usarla direttamente dentro Telegram.\n"
            "2. Oppure tocca il link nel browser e fai <b>'Aggiungi a Schermata Home'</b> per aggiornare l'icona sul telefono!"
        )
        r_msg = requests.post(msg_api, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {
                            "text": "⚡ APRI BAGENT APP ⚡",
                            "web_app": {"url": tunnel_url}
                        }
                    ],
                    [
                        {
                            "text": "🌐 Apri nel Browser",
                            "url": tunnel_url
                        }
                    ]
                ]
            }
        }, timeout=8)
        print("Telegram sendMessage:", r_msg.status_code, r_msg.text)
    except Exception as e:
        print("Message error:", e)

    # Mantieni il processo attivo
    proc.wait()

if __name__ == "__main__":
    t = threading.Thread(target=run_local_server, daemon=True)
    t.start()
    time.sleep(1)
    start_tunnel_and_notify()

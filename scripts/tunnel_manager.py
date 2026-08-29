#!/usr/bin/env python3
"""
BAgent - Remote Smartphone Tunnel Manager (Cloudflare Quick Tunnel)
Avvia un tunnel HTTPS pubblico sicuro e invia il link al bot Telegram dell'utente.
"""
import os
import re
import sys
import time
import subprocess
import requests

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"Errore invio Telegram: {e}")

def run_tunnel():
    print("Avvio Cloudflare Tunnel verso https://localhost:8443...")
    cmd = ["cloudflared", "tunnel", "--url", "https://localhost:8443", "--no-tls-verify"]
    
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    tunnel_url = None
    
    for line in iter(process.stdout.readline, ""):
        print(line, end="")
        match = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
        if match:
            tunnel_url = match.group(0)
            print(f"\n✅ TUNNEL ATTIVO: {tunnel_url}\n")
            
            # Salva URL su file locale
            with open("/tmp/bagent_tunnel_url.txt", "w") as f:
                f.write(tunnel_url)
                
            # Invia notifica Telegram con bottone e link diretto
            msg = (
                f"🌴 <b>BAGENT VACANZE: PORTALE MOBILE ATTIVO!</b> 📱✨\n\n"
                f"Puoi accedere alla dashboard da qualsiasi smartphone in 4G/5G con certificato SSL valido:\n\n"
                f"🔗 <b><a href='{tunnel_url}'>{tunnel_url}</a></b>\n\n"
                f"💡 <i>Suggerimento iPhone/Android:</i> Apri il link su Safari/Chrome e tocca <b>'Aggiungi a Schermata Home'</b> per averlo come vera e propria App nativa!"
            )
            send_telegram(msg)
            break
            
    # Mantieni il processo in vita
    process.wait()

if __name__ == "__main__":
    while True:
        try:
            run_tunnel()
        except Exception as e:
            print(f"Errore tunnel: {e}, riavvio tra 10 secondi...")
            time.sleep(10)

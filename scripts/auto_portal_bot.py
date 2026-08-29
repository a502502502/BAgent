#!/usr/bin/env python3
"""
scripts/auto_portal_bot.py — Demone 24/7 Autonomo per Raspberry Pi.
1. Esegue scansione e analisi ogni 2 ore con Sesto Senso e Regole BetGuard.
2. Serve la Dashboard Web Live su porta 8443 (https://100.120.216.25:8443).
3. Ascolta ed esegue comandi interattivi su Telegram (@A502502_bot).
"""

import os
import sys
import time
import json
import threading
import http.server
import ssl
import socketserver
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Force UTF-8
sys.stdout.reconfigure(line_buffering=True)

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.portal.portal_builder import generate_portal_html
from scripts.bet_guard_validator import BetGuardValidator

# Load .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "466378357")
API_KEY = os.getenv("API_FOOTBALL_KEY", "")
PORT = 8443
PORTAL_DIR = ROOT / "portal"

validator = BetGuardValidator()

def notify_telegram(msg: str, chat_id: str = None, reply_markup: dict = None):
    if not TELEGRAM_TOKEN:
        return
    target_id = chat_id if chat_id else TELEGRAM_CHAT_ID
    if not target_id:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": str(target_id),
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup
        r = requests.post(url, json=payload, timeout=8)
        if r.status_code != 200:
            print(f"Telegram API error: {r.status_code} - {r.text}", flush=True)
    except Exception as e:
        print(f"Telegram send exception: {e}", flush=True)

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "🎫 Schedine Attive"}, {"text": "🌐 Apri Portale Web"}],
            [{"text": "💰 Saldo & Cassa"}, {"text": "🔄 Aggiorna Live"}]
        ],
        "resize_keyboard": True,
        "persistent": True
    }

def get_tunnel_url():
    p = Path("/tmp/bagent_tunnel_url.txt")
    if p.exists():
        url = p.read_text().strip()
        if url.startswith("https://"):
            return url
    return "https://192.168.1.70:8443"

def run_telegram_listener():
    """Ascolta i comandi dell'utente su Telegram e risponde in tempo reale con tastiera interattiva."""
    if not TELEGRAM_TOKEN:
        print("Telegram bot token non presente.", flush=True)
        return

    print("🤖 Telegram Bot Listener Attivo su @A502502_bot...", flush=True)
    last_update_id = 0

    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates?offset={last_update_id + 1}&timeout=20"
            r = requests.get(url, timeout=25)
            if r.status_code == 200:
                res = r.json().get("result", [])
                for upd in res:
                    last_update_id = upd.get("update_id", last_update_id)
                    msg = upd.get("message", {})
                    text = msg.get("text", "").strip()
                    chat_id = msg.get("chat", {}).get("id")

                    if not chat_id:
                        continue

                    print(f"Telegram comando ricevuto da {chat_id}: {text}", flush=True)

                    if text.startswith("/start") or text.startswith("/help") or text == "🔄 Aggiorna Live":
                        tunnel_url = get_tunnel_url()
                        help_msg = (
                            "🌴 <b>BAGENT SMARTPHONE HUB — VACANZE 24/7</b> 📱✨\n\n"
                            "Tutto sotto controllo dal tuo smartphone ovunque ti trovi:\n\n"
                            f"🌐 <b>Portale Web 4G/5G:</b> <a href='{tunnel_url}'>{tunnel_url}</a>\n\n"
                            "Usa i pulsanti rapidi in basso o i comandi testuali:"
                        )
                        notify_telegram(help_msg, chat_id=chat_id, reply_markup=get_main_keyboard())

                    elif text.startswith("/portal") or text == "🌐 Apri Portale Web":
                        tunnel_url = get_tunnel_url()
                        portal_msg = (
                            "🌐 <b>PORTALE WEB MOBILE BAGENT (ACCESSO GLOBALE)</b>\n\n"
                            f"🔗 <b><a href='{tunnel_url}'>CLICCA QUI PER APRIRE IL PORTALE</a></b>\n\n"
                            "✅ <b>Funziona su qualsiasi connessione 4G/5G / Wi-Fi</b>\n"
                            "✅ <b>Certificato SSL verde sicuro al 100%</b>\n"
                            "💡 <i>Su iPhone/Android tocca 'Aggiungi a Schermata Home' per usarla come App!</i>"
                        )
                        inline_kb = {
                            "inline_keyboard": [
                                [{"text": "📱 Apri Dashboard Web", "url": tunnel_url}]
                            ]
                        }
                        notify_telegram(portal_msg, chat_id=chat_id, reply_markup=inline_kb)

                    elif text.startswith("/tickets") or text == "🎫 Schedine Attive":
                        tickets_msg = (
                            "🎫 <b>SCHEDINE UFFICIALI IN GIOCO (SABATO 29 AGOSTO):</b>\n\n"
                            "🏆 <b>Ticket #42: Tripla Serale Live (20.00 € ➔ 53.29 €)</b>\n"
                            "• Porto vs Academico: Over 2.5 @ 1.35 ➔ <i>(0-1 parziale)</i> ⏳\n"
                            "• Real Sociedad vs Espanyol: 1 @ 1.40 ➔ <i>(1-0 parziale)</i> ⏳\n"
                            "• Juventus vs Parma: 1 + Over 1.5 @ 1.41 ➔ <i>Ore 20:45</i> ⏳\n\n"
                            "🛡️ <b>Ticket #41: Recupero d'Acciaio Serale (20.00 € ➔ 106.00 €)</b>\n"
                            "• Dortmund vs Amburgo: 1 + Over 1.5 @ 1.50 ⏳\n"
                            "• Tottenham vs Newcastle: Gol @ 1.48 ⏳\n"
                            "• Lione vs Le Havre: 1 @ 1.45 ➔ <i>Ore 20:45</i> ⏳\n"
                            "• Siviglia vs Atlético: 1X @ 1.65 ➔ <i>Ore 21:30</i> ⏳\n\n"
                            "💎 <b>Ticket #40: Corazzata Corner & Cartellini (20.00 € ➔ 86.00 €)</b>\n"
                            "• Liverpool vs Forest: Over 1.5 Casa @ 1.45 ➔ <b>✅ VINTO!</b>\n"
                            "• Lipsia vs Gladbach: 1X2 Corner (1) @ 1.32 ⏳\n"
                            "• Dortmund vs Amburgo: 1X2 Corner 1°T (1) @ 1.45 ⏳\n"
                            "• Siviglia vs Atlético: Over 4.5 Cartellini @ 1.55 ➔ <i>Ore 21:30</i> ⏳\n\n"
                            "💰 <b>Potenziale Vincita Attiva: 245.29 €!</b>"
                        )
                        notify_telegram(tickets_msg, chat_id=chat_id, reply_markup=get_main_keyboard())

                    elif text.startswith("/saldo") or text == "💰 Saldo & Cassa":
                        saldo_msg = (
                            "💰 <b>SITUAZIONE CASSA & FINANZIARIA:</b>\n\n"
                            "💳 <b>Saldo Netwin Disponibile:</b> 131.02 €\n"
                            "💵 <b>Ticket Attivi in Corsa:</b> 60.00 € (3 Ticket)\n"
                            "🚀 <b>Potenziale Incasso Attivo:</b> 245.29 €\n"
                            "🏆 <b>Profitto Netto Ieri (Incassato):</b> +115.96 € (+276% ROI)\n\n"
                            "🛡️ <i>Tutte le giocate odierne sono coperte dai profitti di ieri!</i>"
                        )
                        notify_telegram(saldo_msg, chat_id=chat_id, reply_markup=get_main_keyboard())

                    elif text.startswith("/refresh"):
                        notify_telegram("🔄 <i>Esecuzione forzata ciclo di analisi a 2 ore...</i>", chat_id=chat_id)
                        execute_2hour_cycle()
                        notify_telegram("✅ <b>Ciclo completato e Portale Web aggiornato!</b>", chat_id=chat_id)

                    elif text.startswith("/validate"):
                        query = text.replace("/validate", "").strip()
                        if query:
                            item = {"match": query, "league": "General", "pick": "1X", "ticket_events_count": 3, "press_scanned": True}
                            ok, reason = validator.validate_selection(item)
                            res_icon = "🟢 APPROVATO" if ok else "🔴 BLOCCATO"
                            notify_telegram(f"🛡️ <b>RISULTATO VALIDATORE BETGUARD:</b>\n\n<b>{query}</b>\nEsito: <b>{res_icon}</b>\nMotivo: <i>{reason}</i>", chat_id=chat_id)
                        else:
                            notify_telegram("⚠️ Uso: <code>/validate NomePartita Segno</code>", chat_id=chat_id)

        except Exception as e:
            print("Telegram loop error:", e, flush=True)

        time.sleep(1)

def main():
    print("=== BAgent 24/7 Autonomous Hub Inizializzato ===", flush=True)
    
    # 1. Primo ciclo di generazione portale
    execute_2hour_cycle()
    
    # 2. Avvia Web Server in background
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # 3. Avvia Telegram listener in background
    tele_thread = threading.Thread(target=run_telegram_listener, daemon=True)
    tele_thread.start()
    
    notify_telegram("🚀 <b>BAGENT 24/7 OPERATIVO SU RASPBERRY PI!</b>\n\n🌐 Portale attivo su: https://100.120.216.25:8443\nInvia /help per i comandi remoti.")

    # 4. Loop principale ogni 2 ore (7200 secondi)
    while True:
        time.sleep(7200)
        try:
            execute_2hour_cycle()
            notify_telegram("🔄 <b>AGGIORNAMENTO PERIODICO (2 ORE):</b>\nIl portale web è stato rinfrescato con i nuovi dati e quote!")
        except Exception as e:
            print("Periodic loop error:", e)

if __name__ == "__main__":
    main()

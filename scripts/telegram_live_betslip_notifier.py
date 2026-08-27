"""
BAgent Telegram Live Betslip Notifier Engine.
Tracks active placed bets, in-play goals, corner/card milestones, and Dutching coverage opportunities,
sending instant real-time Telegram alerts to the user.
"""

import sys
import os
import time
import requests
from datetime import datetime

# Windows UTF-8 stdout
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

TELEGRAM_TOKEN = "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg"
TELEGRAM_CHAT_ID = "466378357"

def send_telegram_msg(msg: str) -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Errore invio Telegram: {e}")
        return False

def notify_ticket_30_status(headline: str, status_qarabag: str, status_besiktas: str, status_paok: str, note: str = ""):
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"🚨 <b>{headline}</b> ({now})\n\n"
        f"👑 <b>TICKET #30 — TERZINA D'ELITE (20.00 € @ 3.65×):</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"1️⃣ 🇦🇿 <b>Qarabağ vs Twente</b> (18:00)\n"
        f"   └ 🎯 1X (Doppia Chance) @ 1.75 ➔ <b>{status_qarabag}</b>\n\n"
        f"2️⃣ 🇱🇹 <b>Kauno Žalgiris vs Beşiktaş</b> (19:00)\n"
        f"   └ 🎯 Beşiktaş Over 1.5 Gol @ 1.50 ➔ <b>{status_besiktas}</b>\n\n"
        f"3️⃣ 🇳🇴 <b>Brann vs PAOK</b> (19:00)\n"
        f"   └ 🎯 PAOK Over 3.5 Corner @ 1.39 ➔ <b>{status_paok}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Stake in Gioco</b>: <b>20.00 €</b>\n"
        f"🏆 <b>Vincita Potenziale a Cassa</b>: <b>73.00 € (+53.00 € Netto)</b>\n"
    )
    if note:
        msg += f"\n💡 <i>{note}</i>"
    return send_telegram_msg(msg)

def notify_dutching_insurance(ticket_name: str, stake: float, pot_win: float, event_pending: str, hedge_market: str, hedge_odd: float, breakeven_stake: float, profitlock_stake: float, lock_profit: float):
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"🛡️ <b>ALERT COPERTURA MATEMATICA (DUTCHING)</b> ({now})\n\n"
        f"📋 <b>Ticket in Corso</b>: {ticket_name}\n"
        f"💵 <b>Stake Giocato</b>: {stake:.2f} € | <b>Vincita a Cassa</b>: {pot_win:.2f} €\n"
        f"⏳ <b>Manca solo 1 evento</b>: <b>{event_pending}</b>\n\n"
        f"⚡ <b>Quota Live Contro-Mercato ({hedge_market})</b>: @ <b>{hedge_odd:.2f}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🅰️ <b>OPZIONE BREAK-EVEN (Rischio Zero):</b>\n"
        f"• Punta <b>{breakeven_stake:.2f} €</b> su <i>{hedge_market}</i>\n"
        f"• Se perdi la schedina ➔ Recuperi al 100% i tuoi {stake:.2f} € giocati!\n\n"
        f"🅱️ <b>OPZIONE PROFIT-LOCK (Vincita Garantita):</b>\n"
        f"• Punta <b>{profitlock_stake:.2f} €</b> su <i>{hedge_market}</i>\n"
        f"• 💰 <b>Incassi SICURI di +{lock_profit:.2f} € NETTI</b> a prescindere da come finisce!\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 <i>Piazza la copertura su Netwin se vuoi congelare il profitto!</i>"
    )
    return send_telegram_msg(msg)

def notify_cassa_victory(ticket_name: str, win_amount: float, net_profit: float):
    now = datetime.now().strftime("%H:%M:%S")
    msg = (
        f"🎉🎉 <b>CASSAAAA! TICKET VINTO!</b> 🎉🎉 ({now})\n\n"
        f"🏆 <b>{ticket_name} PRESO AL 100%!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Incasso a Cassa</b>: <b>{win_amount:.2f} €</b>\n"
        f"📈 <b>Profitto Netto</b>: <b>+{net_profit:.2f} €</b>\n"
        f"🏦 <b>Nuovo Saldo Bankroll</b>: <b>{300.00 + net_profit:.2f} €</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🚀 <i>BAgent Quantitative Engine — Missione Compiuta!</i>"
    )
    return send_telegram_msg(msg)

if __name__ == "__main__":
    print("🚀 Invio test notifica Telegram per Ticket #30...")
    success = notify_ticket_30_status(
        "🟢 BAGENT NOTIFIER ATTIVO SUL TUO TELEGRAM",
        "⏳ In attesa inizio (posticipata x pioggia)",
        "⏳ Iniziata ora (1°T 0-0)",
        "⏳ Iniziata ora (1°T 0-0)",
        "La sentinella Telegram è attiva in tempo reale. Riceverai qui gol, corner, coperture Dutching e vincite!"
    )
    if success:
        print("✅ Notifica inviata con successo su Telegram!")
    else:
        print("❌ Errore durante l'invio della notifica Telegram.")

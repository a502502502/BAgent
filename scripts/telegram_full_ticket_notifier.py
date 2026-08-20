import requests
from datetime import datetime

TELEGRAM_TOKEN = "8852289931:AAHy77CefE6rlzydAhYyfEbG-AB8XG7wlzg"
TELEGRAM_CHAT_ID = "466378357"

def send_full_ticket_alert(headline: str, custom_note: str = ""):
    """Sends a Telegram notification containing the complete active ticket recap."""
    now = datetime.now().strftime("%H:%M")
    
    # Active ticket selections
    ticket_lines = [
        "1️⃣ 🇪🇪 <b>Tartu Welco 4-2 Levadia</b> (FT)\n   └ 🎯 Over 5.5 @3.30 ➔ <b>✅ VINTO</b>",
        "2️⃣ 🇪🇬 <b>El Mansurah 0-1 Baladiyyat</b> (90')\n   └ 🎯 Under 2.5 @1.34 ➔ <b>✅ VINTO / AL SICURO</b>",
        "3️⃣ 🇷🇴 <b>Selimbar 0-1 Botosani</b> (1°T 45')\n   └ 🎯 2 (Botosani) @1.46 ➔ <b>🟢 IN VANTAGGIO</b>",
        "4️⃣ 🇳🇴 <b>Rosenborg Femm. vs Lyn</b> (18:00)\n   └ 🎯 Over 2.5 @1.40 ➔ <b>⏳ IN ARRIVO</b>",
        "5️⃣ 🇸🇪 <b>Mjallby vs Salisburgo</b> (18:00)\n   └ 🎯 Over 3.5 Cartellini @1.71 ➔ <b>⏳ IN ARRIVO</b>",
        "6️⃣ 🇵🇱 <b>Jagiellonia vs Iberia</b> (18:00)\n   └ 🎯 Over 8.5 Corner @1.59 ➔ <b>⏳ IN ARRIVO</b>"
    ]
    
    msg = (
        f"🚨 <b>{headline}</b> ({now})\n\n"
        f"📋 <b>STATO COMPLETO SCHEDINA (270.32 €):</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n" +
        "\n\n".join(ticket_lines) +
        f"\n━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 <b>Avanzamento</b>: <b>2/6</b> In Cassa · <b>1</b> In Vantaggio · <b>3</b> Alle 18:00\n"
        f"💰 <b>Vincita Potenziale</b>: <b>270.32 €</b> (Puntata 10.00 €)\n"
    )
    if custom_note:
        msg += f"\n💡 <i>{custom_note}</i>"
        
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print("Telegram send error:", e)
        return False

if __name__ == "__main__":
    send_full_ticket_alert("🔔 AGGIORNAMENTO COMPLETO SCHEDINA", "Formato master attivo per ogni notifica futura!")

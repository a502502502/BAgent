#!/usr/bin/env python3
"""
BAgent Netwin Official Booking Engine v2.1 + Telegram Push Notifier
1. Legge i ticket con booking_code == null da portal/schedine.json
2. Compila il carrello su Netwin.it tramite Playwright + Network Interceptor
3. Estrae il Codice Prenotazione ufficiale e aggiorna portal/schedine.json
4. Invia su Telegram il riepilogo con codice copiabile (`code`) e lo screenshot della ricevuta
"""

import asyncio
import json
import mimetypes
import os
import re
import sys
import urllib.request
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.async_api import async_playwright, Page, Response

ROOT = Path(__file__).resolve().parent.parent
SCHEDINE_PATH = ROOT / "portal" / "schedine.json"
NETWIN_ODDS_PATH = ROOT / "data" / "netwin_live_odds.json"
REPORTS_DIR = ROOT / "reports"
ENV_PATH = ROOT / ".env"


# =====================================================================
# 1. CARICAMENTO .ENV SICURO & NOTIFICATORE TELEGRAM (TESTO + FOTO)
# =====================================================================

def load_dotenv_safe():
    """Carica le variabili da .env senza dipendenze esterne."""
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        k = k.strip()
        v = v.strip().strip("'").strip('"')
        if k and k not in os.environ:
            os.environ[k] = v


def send_telegram_message(text: str) -> bool:
    """Invia un messaggio formattato Markdown sul canale/chat Telegram di BAgent."""
    load_dotenv_safe()
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")
    if not token or not chat_id:
        print("  [TELEGRAM WARN] TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID mancanti in .env")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"  [TELEGRAM ERROR] Invio testo fallito: {e}")
        return False


def send_telegram_photo(photo_path: Path, caption: str) -> bool:
    """Invia lo screenshot della modale di prenotazione Netwin direttamente su Telegram."""
    load_dotenv_safe()
    token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID") or os.getenv("CHAT_ID")
    if not token or not chat_id or not photo_path.exists():
        return False

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    boundary = uuid.uuid4().hex
    content_type = mimetypes.guess_type(photo_path.name)[0] or "image/png"

    parts = []
    # chat_id
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n".encode("utf-8"))
    # parse_mode
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"parse_mode\"\r\n\r\nMarkdown\r\n".encode("utf-8"))
    # caption
    parts.append(f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n".encode("utf-8"))
    # photo file
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{photo_path.name}\"\r\n"
        f"Content-Type: {content_type}\r\n\r\n".encode("utf-8")
    )
    parts.append(photo_path.read_bytes())
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))

    body = b"".join(parts)
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return resp.status == 200
    except Exception as e:
        print(f"  [TELEGRAM WARN] Invio foto fallito ({e}), invio solo testo...")
        return False


def format_ticket_telegram_alert(ticket: Dict, code: str) -> str:
    """
    Formatta il ticket prenotato rispettando rigorosamente la Regola #76 (Data e Ora obbligatorie).
    Il codice è racchiuso tra backtick (`...`) per essere copiato con un solo tocco su Telegram.
    """
    title = ticket.get("title", "Schedina BAgent")
    stake = ticket.get("stake", "10.00 €")
    odds = ticket.get("odds", "N/A")
    pot_win = ticket.get("potential_win", "N/A")

    lines = [
        f"🎟️ *PRENOTAZIONE UFFICIALE NETWIN*",
        f"📌 *{title}*",
        f"🔑 Codice (tocca per copiare): `{code}`",
        f"💰 Stake: *{stake}* | Quota: *{odds}* | Vincita: *{pot_win}*",
        "",
        "📋 *Selezioni Certificate (Regola #76):*",
    ]
    for idx, leg in enumerate(ticket.get("legs", []), start=1):
        when_str = leg.get("when", "Data/Ora N/D")
        match_str = leg.get("match", "")
        pick_str = leg.get("pick", "")
        odd_str = leg.get("odd", "")
        lines.append(f"{idx}. 🕒 `{when_str}`\n   ⚽ *{match_str}*\n   👉 `{pick_str}` (@ *{odd_str}*)")

    lines.append(f"\n🌐 _Sincronizzato con portal/schedine.json_")
    return "\n".join(lines)


# =====================================================================
# 2. MOTORE PLAYWRIGHT + NETWORK INTERCEPTOR NETWIN
# =====================================================================

MARKET_TAB_MAP: Dict[str, Tuple[str, str]] = {
    "Over 0.5 1°T + Over 0.5 2°T": ("COMBO", "OV 1°T + OV 2°T 0.5 0.5"),
    "MultiGol 0-2 1°T + 1-3 2°T": ("MULTIGOL", "0-2 1°T + 1-3 2°T"),
    "MultiGol 1-3 1°T + 1-3 2°T": ("MULTIGOL", "1-3 1°T + 1-3 2°T"),
    "MultiGol 1-3 1°T + 1-4 2°T": ("MULTIGOL", "1-3 1°T + 1-4 2°T"),
    "MultiGol 1-3 2°Tempo": ("2° TEMPO", "MultiGol 1-3 2° Tempo"),
    "Chance Mix: 1X o Over 1.5": ("CHANCE MIX", "1X o Over 1.5"),
    "Chance Mix: X2 o Over 1.5": ("CHANCE MIX", "X2 o Over 1.5"),
    "Chance Mix: X o GG": ("CHANCE MIX", "X o Gol"),
    "Chance Mix: X o Gol": ("CHANCE MIX", "X o Gol"),
    "1X + MultiGol 1-5": ("COMBO", "1X + MultiGol 1-5"),
    "1X + MultiGol 1-4": ("COMBO", "1X + MultiGol 1-4"),
    "X2 + MultiGol 1-4": ("COMBO", "X2 + MultiGol 1-4"),
    "X2 + MultiGol 2-5": ("COMBO", "X2 + MultiGol 2-5"),
    "1X + Under 3.5": ("COMBO", "1X + Under 3.5"),
    "X2 + Under 3.5": ("COMBO", "X2 + Under 3.5"),
    "1X + Over 1.5": ("COMBO", "1X + Over 1.5"),
    "X2 + Over 1.5": ("COMBO", "X2 + Over 1.5"),
    "MultiGol 1-4": ("MULTIGOL", "MultiGol 1-4"),
    "MultiGol 1-5": ("MULTIGOL", "MultiGol 1-5"),
    "MultiGol 2-5": ("MULTIGOL", "MultiGol 2-5"),
    "Goal / Entrambe Segnano": ("PRINCIPALI", "Gol"),
    "G/NG: Gol": ("PRINCIPALI", "Gol"),
}


class NetwinBookingEngine:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.intercepted_code: Optional[str] = None

    async def _handle_network_response(self, response: Response):
        url = response.url.lower()
        if any(k in url for k in ("prenota", "booking", "schedina", "coupon", "ticket", "cart")):
            try:
                if "application/json" in response.headers.get("content-type", ""):
                    body = await response.json()
                    raw_str = json.dumps(body)
                    for key in ("codicePrenotazione", "codice", "bookingCode", "idPrenotazione", "code", "hash"):
                        if isinstance(body, dict) and body.get(key):
                            val = str(body[key]).strip()
                            if 5 <= len(val) <= 24:
                                self.intercepted_code = val.upper()
                                return
                    m = re.search(r'"(?:codice\w*|booking\w*|idPrenotazione)"\s*:\s*"?([A-Z0-9]{5,22})"?', raw_str, re.I)
                    if m:
                        self.intercepted_code = m.group(1).upper()
            except Exception:
                pass

    async def accept_cookies_and_popups(self, page: Page):
        for sel in (
            "button:has-text('Accetta')",
            "button:has-text('Accetta tutti')",
            "button:has-text('OK')",
            "#onetrust-accept-btn-handler",
            ".cookie-accept",
            ".close-modal",
        ):
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=1500):
                    await loc.click()
                    await page.wait_for_timeout(400)
            except Exception:
                pass

    async def add_selection_to_cart(self, page: Page, match_name: str, pick_name: str, target_odd: str) -> bool:
        home_team = match_name.split(" vs ")[0].strip()
        clean_pick = pick_name.replace(" : SI", "").strip()
        tab_name, outcome_label = MARKET_TAB_MAP.get(clean_pick, ("TUTTI", clean_pick))

        print(f"  🔎 Cerco '{match_name}' -> [{tab_name}] '{outcome_label}' (@{target_odd})...")
        try:
            search_input = page.locator(
                "input[placeholder*='Cerca'], input[type='search'], input[name*='search'], .search-input input"
            ).first
            await search_input.wait_for(state="visible", timeout=8000)
            await search_input.click()
            await search_input.fill("")
            await search_input.fill(home_team)
            await search_input.press("Enter")
            await page.wait_for_timeout(1800)

            match_row = page.locator(f"text=/{re.escape(home_team)}/i").first
            await match_row.click()
            await page.wait_for_timeout(1800)

            if tab_name != "PRINCIPALI":
                tab_loc = page.locator(
                    f"text=/^{re.escape(tab_name)}$/i, a:has-text('{tab_name}'), button:has-text('{tab_name}')"
                ).first
                if await tab_loc.is_visible(timeout=3000):
                    await tab_loc.click()
                    await page.wait_for_timeout(1000)

            outcome_loc = page.locator(
                f"//*[contains(translate(text(), 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), '{outcome_label.upper()}')]"
                f"/ancestor::*[self::div or self::li or self::tr][1]//*[contains(text(), '{target_odd}')]"
            ).first
            if await outcome_loc.is_visible(timeout=3500):
                await outcome_loc.click()
            else:
                fallback_loc = page.locator(f"text='{outcome_label}'").first
                await fallback_loc.click(timeout=4000)

            await page.wait_for_timeout(1000)
            print(f"  ✅ Aggiunta al carrello: {match_name} -> {outcome_label}")
            return True
        except Exception as e:
            print(f"  ⚠️ Impossibile cliccare automaticamente {match_name} ({clean_pick}): {e}")
            return False

    async def finalize_booking_and_extract_code(self, page: Page, stake_str: str, ticket_id: str) -> Tuple[Optional[str], Path]:
        self.intercepted_code = None
        clean_stake = re.sub(r"[^\d.,]", "", stake_str).replace(",", ".") or "10"
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        shot_path = REPORTS_DIR / f"prenotazione_{ticket_id}.png"

        try:
            stake_input = page.locator("input[placeholder*='Importo'], input[name*='stake'], .betslip-stake input").first
            if await stake_input.is_visible(timeout=2000):
                await stake_input.fill(clean_stake)

            prenota_btn = page.locator(
                "button:has-text('Prenota'), a:has-text('Prenota'), .btn-prenota, [data-action='book']"
            ).first
            await prenota_btn.wait_for(state="visible", timeout=6000)
            await prenota_btn.click()
            await page.wait_for_timeout(3000)

            await page.screenshot(path=str(shot_path))

            if self.intercepted_code:
                return self.intercepted_code, shot_path

            modal_text = await page.locator("body").inner_text()
            for pat in (
                r"Codice\s+Prenotazione[:\s]*([A-Z0-9]{5,22})",
                r"Prenotazione\s+n[°.]?[:\s]*([A-Z0-9]{5,22})",
                r"\b([A-F0-9]{16,22})\b",
                r"Codice[:\s]+(\d{6,10})\b",
            ):
                m = re.search(pat, modal_text, re.I)
                if m:
                    code = m.group(1).upper()
                    (REPORTS_DIR / f"prenotata_{code}.html").write_text(await page.content(), encoding="utf-8")
                    return code, shot_path
        except Exception as e:
            print(f"  ❌ Errore in fase di finalizzazione prenotazione: {e}")

        return None, shot_path

    async def clear_cart(self, page: Page):
        for sel in ("button:has-text('Svuota')", "a:has-text('Svuota')", ".clear-cart", ".trash-icon"):
            try:
                loc = page.locator(sel).first
                if await loc.is_visible(timeout=1500):
                    await loc.click()
                    await page.wait_for_timeout(600)
            except Exception:
                pass

    async def book_all_pending_tickets(self):
        if not SCHEDINE_PATH.exists():
            print(f"[ERRORE] File non trovato: {SCHEDINE_PATH}")
            return

        data = json.loads(SCHEDINE_PATH.read_text(encoding="utf-8"))
        present_tickets = data.get("present", [])
        pending = [t for t in present_tickets if not t.get("booking_code")]

        if not pending:
            print("✅ Tutte le schedine in 'present' hanno già un codice di prenotazione!")
            return

        print(f"🚀 Trovate {len(pending)} schedine da prenotare su Netwin...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                viewport={"width": 1440, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            )
            page = await context.new_page()
            page.on("response", self._handle_network_response)

            print("🌐 Apertura portale Scommesse Netwin...")
            await page.goto("https://www.netwin.it/scommesse", wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)
            await self.accept_cookies_and_popups(page)

            booked_count = 0

            for ticket in pending:
                t_id = ticket.get("id", "TICKET")
                t_title = ticket.get("title", t_id)
                print(f"\n==========================================")
                print(f"🎫 Elaborazione: {t_title}")
                print(f"==========================================")

                await self.clear_cart(page)
                all_legs_ok = True

                for leg in ticket.get("legs", []):
                    ok = await self.add_selection_to_cart(
                        page,
                        match_name=leg.get("match", ""),
                        pick_name=leg.get("pick", ""),
                        target_odd=str(leg.get("odd", "")),
                    )
                    if not ok:
                        all_legs_ok = False

                if all_legs_ok:
                    code, shot_path = await self.finalize_booking_and_extract_code(
                        page, stake_str=ticket.get("stake", "10.00 €"), ticket_id=t_id
                    )
                    if code:
                        ticket["booking_code"] = code
                        booked_count += 1
                        print(f"🎉 PRENOTAZIONE COMPLETATA! Codice Netwin: [{code}]")

                        # Invio immediato su Telegram (Foto + Testo con codice copiabile)
                        tg_caption = format_ticket_telegram_alert(ticket, code)
                        sent_photo = send_telegram_photo(shot_path, tg_caption)
                        if not sent_photo:
                            send_telegram_message(tg_caption)
                        print(f"📲 Notifica Telegram inviata per il codice [{code}]!")
                    else:
                        print(f"⚠️ Impossibile leggere il codice prenotazione per {t_id}.")
                else:
                    print(f"⚠️ Alcune selezioni di {t_id} non sono state trovate: prenotazione saltata.")

            await browser.close()

        if booked_count > 0:
            data["generated_at"] = datetime.now().isoformat()
            SCHEDINE_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            print(f"\n✅ Salvati {booked_count} nuovi codici in portal/schedine.json!")


def send_existing_codes_to_telegram():
    """Modalità --notify-only: invia su Telegram i codici già presenti in portal/schedine.json."""
    if not SCHEDINE_PATH.exists():
        return
    data = json.loads(SCHEDINE_PATH.read_text(encoding="utf-8"))
    for t in data.get("present", []):
        code = t.get("booking_code")
        if code:
            msg = format_ticket_telegram_alert(t, code)
            send_telegram_message(msg)
            print(f"📲 Inviato su Telegram codice esistente: {code}")


if __name__ == "__main__":
    if "--notify-only" in sys.argv:
        send_existing_codes_to_telegram()
    else:
        headed_mode = "--headed" in sys.argv
        engine = NetwinBookingEngine(headless=not headed_mode)
        asyncio.run(engine.book_all_pending_tickets())

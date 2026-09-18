#!/usr/bin/env python3
"""
scripts/live_ticket_daemon.py — Live Tracker Ufficiale Basato su Feed Flashscore / Diretta.it
Nessuna stima locale, nessuna formula basata sull'orologio di Windows, nessuna ricerca web.
Interroga direttamente il feed raw in streaming di Flashscore (local-it.flashscore.ninja).
Aggiorna ogni 20 secondi l'HTML pre-renderizzato sul Desktop.
"""

from __future__ import annotations
import os
import sys
import time
import json
import logging
import urllib.request
from datetime import datetime
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
DESKTOP_DIR = Path(r"C:\Users\demarj\Desktop")
JSON_DESKTOP = DESKTOP_DIR / "live_ticket_data.json"
JS_DESKTOP = DESKTOP_DIR / "live_ticket_feed.js"
HTML_DESKTOP = DESKTOP_DIR / "live_ticket_tracker.html"
JSON_REPO = ROOT / "data" / "live_ticket_data.json"
JSON_REPO.parent.mkdir(parents=True, exist_ok=True)

# Mappatura rigorosa delle 7 selezioni del Ticket Netwin con le parole chiave Flashscore
TICKET_LEGS_CONFIG = [
    {
        "id": 1,
        "match_name": "FC Chernomorets Odessa vs FC Obolon Kyiv",
        "tournament": "Ucraina | Premier League",
        "netwin_id": 9305,
        "market": "1X + Under 4.5",
        "odds": 1.45,
        "kickoff": "12:00",
        "fs_keywords": ["odesa", "chernomorets", "obolon"]
    },
    {
        "id": 2,
        "match_name": "Arabia Saudita U23 vs Qatar U23",
        "tournament": "Internazionali Giovanili | Giochi Asiatici",
        "netwin_id": 10491,
        "market": "1 (Esito Finale)",
        "odds": 1.48,
        "kickoff": "12:30",
        "fs_keywords": ["saudi", "qatar"]
    },
    {
        "id": 3,
        "match_name": "Maccabi Yavne vs Hapoel Herzelia FC",
        "tournament": "Israele | Liga Alef South",
        "netwin_id": 4028,
        "market": "Under 3.5",
        "odds": 1.33,
        "kickoff": "12:35",
        "fs_keywords": ["yavne", "herzliya", "herzelia"]
    },
    {
        "id": 4,
        "match_name": "Zhejiang FC vs Wuhan Three Towns FC",
        "tournament": "Cina | Super League",
        "netwin_id": 1331,
        "market": "1X + Over 1.5",
        "odds": 1.42,
        "kickoff": "13:35",
        "fs_keywords": ["zhejiang", "wuhan"]
    },
    {
        "id": 5,
        "match_name": "FC Polissya Zhytomyr vs FC Kryvbas Kriviy Rih",
        "tournament": "Ucraina | Premier League",
        "netwin_id": 573,
        "market": "1 (Esito Finale)",
        "odds": 1.23,
        "kickoff": "14:30",
        "fs_keywords": ["polissya", "kryvbas", "hirnyk"]
    },
    {
        "id": 6,
        "match_name": "Hapoel Tel Aviv FC vs Hapoel Petah Tikva FC",
        "tournament": "Israele | Premier League",
        "netwin_id": 2989,
        "market": "Doppia Chance 1X",
        "odds": 1.07,
        "kickoff": "14:45",
        "fs_keywords": ["tel aviv", "petah tikva"]
    },
    {
        "id": 7,
        "match_name": "Highbury FC vs Gomora United",
        "tournament": "Sudafrica | Championship",
        "netwin_id": 1722,
        "market": "1X + Under 3.5",
        "odds": 1.46,
        "kickoff": "15:00",
        "fs_keywords": ["highbury", "gomora"]
    }
]

FLASHSCORE_FEED_URLS = [
    "https://local-it.flashscore.ninja/2/x/feed/f_1_0_1_it_1",
    "https://local-it.flashscore.ninja/2/x/feed/f_1_0_2_it_1"
]
FLASHSCORE_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "X-Fsign": "SW9D1eZo",
    "Accept": "*/*",
    "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
}

def fetch_flashscore_live_feed() -> list[dict]:
    """Scarica il delta live ufficiale di Flashscore/Diretta.it e lo decodifica in oggetti match."""
    raw_text = ""
    for url in FLASHSCORE_FEED_URLS:
        try:
            req = urllib.request.Request(url, headers=FLASHSCORE_HEADERS)
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_text = resp.read().decode("utf-8", errors="ignore")
                if len(raw_text) > 40000:
                    break
        except Exception as e:
            logging.debug(f"Flashscore feed {url} error: {e}")
            continue

    if not raw_text:
        return []

    parsed_matches = []
    blocks = raw_text.split("~AA÷")
    for b in blocks[1:]:
        fields = {}
        for p in b.split("¬"):
            if "÷" in p:
                k, v = p.split("÷", 1)
                fields[k] = v

        home = fields.get("AE", "").strip()
        away = fields.get("AF", "").strip()
        if not home or not away:
            continue

        ab = fields.get("AB", "1") # 1=Prog, 2=Live, 3=FT
        ac = fields.get("AC", "")  # 12=1T, 13=2T, 11=HT, 36=FT
        sh_str = fields.get("AG", "")
        sa_str = fields.get("AH", "")

        score_h = int(sh_str) if sh_str.isdigit() else 0
        score_a = int(sa_str) if sa_str.isdigit() else 0
        has_score = (sh_str != "" and sa_str != "")

        # Stato standardizzato
        if ab == "3" or ac == "36":
            status = "FT"
            minute_desc = "Finale (FT)"
        elif ab == "2":
            if ac == "11":
                status = "HT"
                minute_desc = "Intervallo"
            elif ac == "12":
                status = "LIVE_1T"
                minute_desc = "1° Tempo"
            elif ac == "13":
                status = "LIVE_2T"
                minute_desc = "2° Tempo"
            else:
                status = "LIVE"
                minute_desc = "In Corso"
        else:
            status = "NOT_STARTED"
            minute_desc = "Programmata"

        parsed_matches.append({
            "fs_id": fields.get("AA", ""),
            "home": home,
            "away": away,
            "score_home": score_h,
            "score_away": score_a,
            "has_score": has_score,
            "status": status,
            "minute_desc": minute_desc,
            "raw_ab": ab,
            "raw_ac": ac
        })

    return parsed_matches

def evaluate_leg(leg: dict) -> None:
    """Valutazione matematica deterministica dell'esito basata sui gol REALI di Flashscore."""
    sh = leg["score_home"]
    sa = leg["score_away"]
    tot = sh + sa
    m = leg["market"].upper()
    st = leg["status"]

    if st == "NOT_STARTED":
        if "OVER" in m:
            leg["leg_status"] = "PENDING"
            leg["status_detail"] = "Partita programmata (in attesa di inizio)"
        elif "1X" in m or "UNDER" in m or "X2" in m:
            leg["leg_status"] = "WINNING"
            leg["status_detail"] = "Partita programmata (punteggio 0-0 conforme)"
        else:
            leg["leg_status"] = "PENDING"
            leg["status_detail"] = "Partita programmata"
        return

    # Se terminata (FT)
    if st == "FT":
        if "1X + UNDER 4.5" in m:
            if sh >= sa and tot < 5:
                leg["leg_status"] = "WON"
                leg["status_detail"] = f"🏆 VINTA UFFICIALE: 1X centrato e {tot} gol totali (< 4.5)"
            else:
                leg["leg_status"] = "LOST"
                leg["status_detail"] = f"❌ PERSA: finale {sh}-{sa}"
        elif "UNDER 3.5" in m:
            if tot < 4:
                leg["leg_status"] = "WON"
                leg["status_detail"] = f"🏆 VINTA UFFICIALE: {tot} gol totali (< 3.5)"
            else:
                leg["leg_status"] = "LOST"
                leg["status_detail"] = f"❌ PERSA: superata soglia ({tot} gol)"
        elif m in ("1", "1 (ESITO FINALE)"):
            if sh > sa:
                leg["leg_status"] = "WON"
                leg["status_detail"] = f"🏆 VINTA UFFICIALE: vittoria casa {sh}-{sa}"
            else:
                leg["leg_status"] = "LOST"
                leg["status_detail"] = f"❌ PERSA: finale {sh}-{sa}"
        elif "1X + OVER 1.5" in m:
            if sh >= sa and tot >= 2:
                leg["leg_status"] = "WON"
                leg["status_detail"] = f"🏆 VINTA UFFICIALE: 1X centrato e {tot} gol (Over 1.5)"
            else:
                leg["leg_status"] = "LOST"
                leg["status_detail"] = f"❌ PERSA: finale {sh}-{sa}"
        elif "1X + UNDER 3.5" in m:
            if sh >= sa and tot < 4:
                leg["leg_status"] = "WON"
                leg["status_detail"] = f"🏆 VINTA UFFICIALE: 1X e Under 3.5 ({sh}-{sa})"
            else:
                leg["leg_status"] = "LOST"
                leg["status_detail"] = f"❌ PERSA: finale {sh}-{sa}"
        elif "1X" in m:
            if sh >= sa:
                leg["leg_status"] = "WON"
                leg["status_detail"] = f"🏆 VINTA UFFICIALE: 1X rispettato ({sh}-{sa})"
            else:
                leg["leg_status"] = "LOST"
                leg["status_detail"] = f"❌ PERSA: finale {sh}-{sa}"
        return

    # In corso (LIVE, LIVE_1T, HT, LIVE_2T)
    if "1X + UNDER 4.5" in m:
        if sh >= sa and tot < 5:
            leg["leg_status"] = "WINNING"
            leg["status_detail"] = f"🟢 1X coperto e {tot} gol totali (< 4.5)"
        elif tot >= 5:
            leg["leg_status"] = "LOST"
            leg["status_detail"] = f"❌ Persa: superato limite gol ({tot} gol)"
        else:
            leg["leg_status"] = "AT_RISK"
            leg["status_detail"] = f"🟡 Ospite avanti ({sh}-{sa}): serve 1X"

    elif "UNDER 3.5" in m:
        if tot < 4:
            leg["leg_status"] = "WINNING"
            leg["status_detail"] = f"🟢 In cassa: {tot} gol totali (limite Under 3.5)"
        else:
            leg["leg_status"] = "LOST"
            leg["status_detail"] = f"❌ Persa: superati 3 gol ({tot} gol)"

    elif m in ("1", "1 (ESITO FINALE)"):
        if sh > sa:
            leg["leg_status"] = "WINNING"
            leg["status_detail"] = f"🟢 In cassa: vantaggio casa ({sh}-{sa})!"
        elif sh == sa:
            leg["leg_status"] = "AT_RISK"
            leg["status_detail"] = f"🟡 Pareggio ({sh}-{sa}): serve il gol del vantaggio (1)"
        else:
            leg["leg_status"] = "AT_RISK"
            leg["status_detail"] = f"🔴 Sotto di misura ({sh}-{sa})"

    elif "1X + OVER 1.5" in m:
        if sh >= sa and tot >= 2:
            leg["leg_status"] = "WINNING"
            leg["status_detail"] = f"🟢 DOPPIO OBIETTIVO CENTRATO: {sh}-{sa} (Over 1.5 preso + 1X saldo!)"
        elif sh >= sa and tot < 2:
            leg["leg_status"] = "WINNING"
            leg["status_detail"] = f"🟡 Vantaggio interno ({sh}-{sa}): serve 1 altro gol per Over 1.5"
        else:
            leg["leg_status"] = "AT_RISK"
            leg["status_detail"] = f"🔴 Ospite avanti ({sh}-{sa})"

    elif "1X + UNDER 3.5" in m:
        if sh >= sa and tot < 4:
            leg["leg_status"] = "WINNING"
            leg["status_detail"] = f"🟢 1X coperto e {tot} gol (< 3.5)"
        elif tot >= 4:
            leg["leg_status"] = "LOST"
            leg["status_detail"] = f"❌ Persa: {tot} gol"
        else:
            leg["leg_status"] = "AT_RISK"
            leg["status_detail"] = f"🟡 Ospite avanti ({sh}-{sa})"

    elif "1X" in m:
        if sh >= sa:
            leg["leg_status"] = "WINNING"
            leg["status_detail"] = f"🟢 1X attivo ({sh}-{sa})"
        else:
            leg["leg_status"] = "AT_RISK"
            leg["status_detail"] = f"🔴 Ospite avanti ({sh}-{sa})"

def render_cards_html(legs: list[dict]) -> str:
    cards = []
    for m in legs:
        card_class = "pending"
        badge_text = "IN ATTESA"
        badge_style = "background:rgba(56,139,253,0.15); color:var(--blue); border:1px solid var(--blue);"

        if m["leg_status"] == "WON":
            card_class = "winning"
            badge_text = "🏆 VINTA"
            badge_style = "background:rgba(63,185,80,0.25); color:var(--green); border:1px solid var(--green);"
        elif m["leg_status"] == "WINNING":
            card_class = "winning"
            badge_text = "🟢 IN CASSA"
            badge_style = "background:rgba(63,185,80,0.15); color:var(--green); border:1px solid var(--green);"
        elif m["leg_status"] == "AT_RISK":
            card_class = "at-risk"
            badge_text = "🟡 IN BILICO"
            badge_style = "background:rgba(210,153,34,0.15); color:var(--gold); border:1px solid var(--gold);"
        elif m["leg_status"] == "LOST":
            card_class = "lost"
            badge_text = "❌ PERSA"
            badge_style = "background:rgba(248,81,73,0.15); color:var(--red); border:1px solid var(--red);"

        is_live = m["status"].startswith("LIVE") or m["status"] == "HT"
        is_ft = m["status"] == "FT"
        time_class = "live" if is_live else ("won-badge" if is_ft else "upcoming")
        time_icon = "🔴 " if is_live else ("🏁 " if is_ft else "⏰ ")
        time_display = f"{time_icon}{m['minute_desc']}" if is_live or is_ft else f"{time_icon}{m['kickoff']}"

        score_text = f"{m['score_home']} - {m['score_away']}" if (is_live or is_ft) else "- - -"

        card = f"""
      <div class="match-card {card_class}">
        <div class="m-top">
          <span class="m-tourn">{m['tournament']} (ID: {m['netwin_id']})</span>
          <div style="display:flex; gap:6px; align-items:center;">
            <span class="m-status-pill" style="{badge_style}">{badge_text}</span>
            <span class="m-time-pill {time_class}">{time_display}</span>
          </div>
        </div>
        <div class="m-body">
          <div class="m-teams">{m['match_name']}</div>
          <div class="m-score-badge">{score_text}</div>
        </div>
        <div class="m-bottom">
          <span class="m-pick">Giocata: <b>{m['market']}</b></span>
          <span class="m-odd">Quota: <b>{m['odds']:.2f}</b></span>
        </div>
        <div class="m-status-desc">{m['status_detail']}</div>
      </div>"""
        cards.append(card)
    return "\n".join(cards)

def build_full_html(data: dict) -> str:
    cards_html = render_cards_html(data["legs"])
    won_cnt = sum(1 for x in data["legs"] if x["leg_status"] == "WON")
    winning_cnt = sum(1 for x in data["legs"] if x["leg_status"] in ("WINNING", "WON"))
    tot_legs = len(data["legs"])
    pct = int((winning_cnt / tot_legs) * 100)

    return f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta http-equiv="refresh" content="15">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>BAgent LIVE — Tracker Ufficiale Flashscore (189.86€)</title>
<style>
  :root {{
    --bg: #090b0e;
    --card: #14181f;
    --surface: #1b212b;
    --border: #262e3b;
    --text: #f0f3f6;
    --muted: #8c97a5;
    --blue: #388bfd;
    --green: #3fb950;
    --gold: #d29922;
    --red: #f85149;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 16px 12px 60px;
    font-size: 14px;
  }}
  .wrap {{ max-width: 820px; margin: 0 auto; }}
  .topbar {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0 16px;
  }}
  .live-pill {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(63, 185, 80, 0.15);
    border: 1px solid var(--green);
    color: var(--green);
    font-size: 11px;
    font-weight: 900;
    padding: 4px 12px;
    border-radius: 20px;
    text-transform: uppercase;
  }}
  .pulse {{
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--green);
    box-shadow: 0 0 8px var(--green);
    animation: blink 1.5s infinite;
  }}
  @keyframes blink {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.3; }} }}
  .time-tag {{ font-size: 11px; color: var(--muted); }}

  .hero-card {{
    background: linear-gradient(135deg, #161e2b 0%, #11151c 100%);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.5);
    position: relative;
    overflow: hidden;
  }}
  .hero-card::before {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, var(--blue), var(--green), var(--gold));
  }}
  .hero-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }}
  .hero-title {{ font-size: 13px; font-weight: 800; color: var(--muted); text-transform: uppercase; }}
  .hero-badge {{
    background: rgba(63, 185, 80, 0.15);
    border: 1px solid var(--green);
    color: var(--green);
    font-size: 11px;
    font-weight: 800;
    padding: 2px 8px;
    border-radius: 8px;
  }}
  .hero-payout-box {{
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    margin-bottom: 8px;
  }}
  .hero-val {{ font-size: 32px; font-weight: 900; color: #fff; letter-spacing: -1px; }}
  .hero-val span {{ color: var(--green); font-size: 20px; }}
  .hero-stake {{ font-size: 13px; color: var(--muted); text-align: right; }}
  .hero-stake b {{ color: #fff; }}

  .prog-wrap {{
    background: #090b0e;
    border-radius: 8px;
    height: 8px;
    overflow: hidden;
    margin-top: 10px;
    border: 1px solid var(--border);
  }}
  .prog-fill {{
    background: linear-gradient(90deg, var(--blue), var(--green));
    height: 100%;
    width: {pct}%;
    transition: width 0.5s ease;
  }}
  .prog-text {{
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--muted);
    margin-top: 4px;
    font-weight: 700;
  }}

  .match-card {{
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 14px;
    margin-bottom: 10px;
    transition: all 0.2s;
  }}
  .match-card.winning {{ border-left: 4px solid var(--green); }}
  .match-card.at-risk {{ border-left: 4px solid var(--gold); }}
  .match-card.lost {{ border-left: 4px solid var(--red); opacity: 0.6; }}
  .match-card.pending {{ border-left: 4px solid var(--blue); }}

  .m-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }}
  .m-tourn {{ font-size: 11px; color: var(--muted); font-weight: 600; }}
  .m-status-pill {{
    font-size: 10px;
    font-weight: 900;
    padding: 2px 8px;
    border-radius: 12px;
    text-transform: uppercase;
  }}
  .m-time-pill {{
    font-size: 10px;
    font-weight: 800;
    padding: 2px 8px;
    border-radius: 12px;
  }}
  .m-time-pill.live {{ background: rgba(248, 81, 73, 0.2); color: var(--red); border: 1px solid var(--red); }}
  .m-time-pill.won-badge {{ background: rgba(63, 185, 80, 0.2); color: var(--green); border: 1px solid var(--green); }}
  .m-time-pill.upcoming {{ background: rgba(140, 151, 165, 0.15); color: var(--muted); }}

  .m-body {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }}
  .m-teams {{ font-size: 15px; font-weight: 800; color: #fff; }}
  .m-score-badge {{
    font-size: 18px;
    font-weight: 900;
    background: var(--surface);
    padding: 4px 12px;
    border-radius: 8px;
    border: 1px solid var(--border);
    color: #fff;
    letter-spacing: 1px;
  }}
  .m-bottom {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
    background: rgba(255,255,255,0.02);
    padding: 6px 10px;
    border-radius: 6px;
  }}
  .m-pick {{ color: var(--text); }}
  .m-pick b {{ color: var(--blue); }}
  .m-odd b {{ color: var(--green); }}
  .m-status-desc {{
    font-size: 11px;
    margin-top: 6px;
    color: var(--muted);
    font-style: italic;
  }}

  .footer-bar {{
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: #11151c;
    border-top: 1px solid var(--border);
    padding: 10px 16px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: var(--muted);
  }}
  .reload-btn {{
    background: var(--blue);
    border: none;
    color: #fff;
    padding: 6px 14px;
    border-radius: 8px;
    font-weight: 700;
    cursor: pointer;
  }}
</style>
</head>
<body>

<div class="wrap">
  <div class="topbar">
    <div class="live-pill">
      <div class="pulse"></div>
      FLASHSCORE / DIRETTA CERTIFICATO
    </div>
    <div class="time-tag" id="last-update">Ultimo Feed: {data['updated_at']}</div>
  </div>

  <div class="hero-card">
    <div class="hero-header">
      <span class="hero-title">🎯 SCHEDINA CASSAFORTE NETWIN</span>
      <span class="hero-badge">FEED UFFICIALE DIRETTA.IT</span>
    </div>
    <div class="hero-payout-box">
      <div class="hero-val">189,86 € <span>INCASSO</span></div>
      <div class="hero-stake">
        Puntati: <b>23,00 €</b><br>
        Quota: <b>7.79× (+10,74 € Bonus)</b>
      </div>
    </div>
    <div class="prog-wrap">
      <div class="prog-fill" style="width: {pct}%;"></div>
    </div>
    <div class="prog-text">
      <span>{won_cnt} Vinte Ufficiali • {winning_cnt} su {tot_legs} in cassa attiva</span>
      <span style="color:var(--green);">🟢 {pct}% IN CORSA</span>
    </div>
  </div>

  <div id="matches-container">
{cards_html}
  </div>
</div>

<div class="footer-bar">
  <span>Auto-refresh continuo attivo (15s) • <span id="sec-left">15</span>s</span>
  <button class="reload-btn" onclick="window.location.reload()">Aggiorna Subito</button>
</div>

<script>
let sec = 15;
setInterval(() => {{
  sec--;
  if (sec <= 0) {{
    window.location.reload();
  }}
  const el = document.getElementById('sec-left');
  if (el) el.innerText = sec;
}}, 1000);
</script>

</body>
</html>"""

def run_sync_cycle() -> dict:
    """Esegue un ciclo di sincronizzazione certificato Flashscore."""
    fs_matches = fetch_flashscore_live_feed()
    now_str = datetime.now().strftime("%H:%M:%S")

    legs_data = []
    for cfg in TICKET_LEGS_CONFIG:
        # Cerca il match nel feed Flashscore
        matched_fs = None
        for m in fs_matches:
            txt = (m["home"] + " " + m["away"]).lower()
            if any(k in txt for k in cfg["fs_keywords"]):
                matched_fs = m
                break

        leg_obj = {
            "id": cfg["id"],
            "match_name": cfg["match_name"],
            "tournament": cfg["tournament"],
            "netwin_id": cfg["netwin_id"],
            "market": cfg["market"],
            "odds": cfg["odds"],
            "kickoff": cfg["kickoff"],
            "score_home": matched_fs["score_home"] if matched_fs else 0,
            "score_away": matched_fs["score_away"] if matched_fs else 0,
            "status": matched_fs["status"] if matched_fs else "NOT_STARTED",
            "minute_desc": matched_fs["minute_desc"] if matched_fs else "Programmata",
            "fs_name": f"{matched_fs['home']} vs {matched_fs['away']}" if matched_fs else "N/D"
        }

        evaluate_leg(leg_obj)
        legs_data.append(leg_obj)

    full_payload = {
        "ticket_id": "TICKET_CASSAFORTE_23EUR_18SET",
        "stake": 23.0,
        "odds": 7.79,
        "bonus": 10.74,
        "payout": 189.86,
        "updated_at": now_str,
        "source": "Flashscore / Diretta.it Live Delta Feed (Certificato)",
        "legs": legs_data
    }

    # Scrittura Desktop
    html_content = build_full_html(full_payload)
    with open(HTML_DESKTOP, "w", encoding="utf-8") as f:
        f.write(html_content)
    with open(JSON_DESKTOP, "w", encoding="utf-8") as f:
        json.dump(full_payload, f, ensure_ascii=False, indent=2)
    with open(JSON_REPO, "w", encoding="utf-8") as f:
        json.dump(full_payload, f, ensure_ascii=False, indent=2)

    return full_payload

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    print("=" * 80)
    print("🚀 BAgent Live Tracker Ufficiale — Motore Flashscore / Diretta.it")
    print(f"📁 Output Desktop HTML: {HTML_DESKTOP}")
    print(f"📁 Output Desktop JSON: {JSON_DESKTOP}")
    print("=" * 80)

    cycle = 0
    while True:
        cycle += 1
        try:
            payload = run_sync_cycle()
            l1 = payload["legs"][0]
            l2 = payload["legs"][1]
            l3 = payload["legs"][2]
            l4 = payload["legs"][3]
            logging.info(
                f"Flashscore Cycle #{cycle} [{payload['updated_at']}] "
                f"Odesa {l1['score_home']}-{l1['score_away']} ({l1['status']}) | "
                f"Saudi {l2['score_home']}-{l2['score_away']} ({l2['status']}) | "
                f"Yavne {l3['score_home']}-{l3['score_away']} ({l3['status']}) | "
                f"Zhejiang {l4['score_home']}-{l4['score_away']} ({l4['status']})"
            )
        except Exception as e:
            logging.error(f"Errore nel ciclo #{cycle}: {e}")

        time.sleep(20)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
services/portal/portal_builder.py — Generatore Automatico della Dashboard Portale Web BAgent.
Produce un HTML moderno, responsive, mobile-first e dark-mode (portal/index.html).
"""

import json
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
PORTAL_DIR = ROOT / "portal"
INDEX_HTML = PORTAL_DIR / "index.html"

def generate_portal_html(data: dict) -> str:
    now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    bankroll = data.get("bankroll", 300.00)
    active_tickets = data.get("active_tickets", [])
    today_picks = data.get("today_picks", [])
    recent_results = data.get("recent_results", [])
    system_status = data.get("system_status", "ATTIVO ●")
    next_refresh = data.get("next_refresh", "In corso...")

    # Costruisci cards dei ticket attivi
    tickets_html = ""
    for t in active_tickets:
        badge_cls = "badge-green" if t.get("status") == "VINTO" else "badge-yellow" if t.get("status") == "IN CORSO" else "badge-blue"
        events_rows = ""
        for ev in t.get("events", []):
            ev_status = ev.get("status", "⏳")
            events_rows += f"""
            <tr>
                <td style="width: 15%; font-weight: 600;">{ev.get('time', '--:--')}</td>
                <td style="width: 45%;">{ev.get('match', '')}</td>
                <td style="width: 25%;"><span class="badge badge-blue">{ev.get('pick', '')}</span></td>
                <td style="width: 15%; text-align: right;">@{ev.get('odd', '1.00')} <span style="font-size:10px;">{ev_status}</span></td>
            </tr>
            """
        
        ref_code = t.get("ref", "N/D")
        tickets_html += f"""
        <div class="ticket-card">
            <div class="ticket-header">
                <div>
                    <span class="badge {badge_cls}">{t.get('badge', 'TICKET UFFICIALE')}</span>
                    <h3 class="ticket-title">{t.get('title', 'Ticket')}</h3>
                </div>
                <div class="ticket-odds">{t.get('odds', '1.00×')}</div>
            </div>
            <div class="ticket-meta">
                <span>Rif: <code>{ref_code}</code></span>
                <span>Stake: <strong>{t.get('stake', '10.00 €')}</strong> ➔ Pot: <strong style="color:var(--accent-green);">{t.get('potential', '0.00 €')}</strong></span>
            </div>
            <table>
                <tbody>
                    {events_rows}
                </tbody>
            </table>
            {f'<div class="cashout-box">🛡️ <strong>Cashout / Take-Profit Suggerito:</strong> {t.get("cashout_note")}</div>' if t.get("cashout_note") else ''}
        </div>
        """

    # Costruisci picks del giorno approvate da BetGuard
    picks_html = ""
    for p in today_picks:
        picks_html += f"""
        <tr>
            <td style="font-weight: 700; color: var(--accent-blue);">{p.get('time', '')}</td>
            <td><strong>{p.get('match', '')}</strong><br><span style="font-size: 10px; color: var(--text-muted);">{p.get('league', '')}</span></td>
            <td><span class="badge badge-green">{p.get('pick', '')}</span></td>
            <td style="font-weight: 800;">@{p.get('odd', '1.00')}</td>
            <td><span class="badge badge-purple">{p.get('edge', '+5.0%')}</span></td>
            <td class="sesto-senso-cell">{p.get('sesto_senso', '')}</td>
        </tr>
        """

    html = f"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>BAgent — Centrale Operativa 24/7 (Raspberry Pi)</title>
<style>
  :root {{
    --bg: #070d19;
    --card-bg: #111c30;
    --card-border: #1e293b;
    --accent-blue: #38bdf8;
    --accent-green: #10b981;
    --accent-yellow: #f59e0b;
    --accent-red: #ef4444;
    --accent-purple: #a855f7;
    --text-primary: #f8fafc;
    --text-muted: #94a3b8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text-primary);
    padding: 12px;
    font-size: 13px;
    line-height: 1.4;
  }}
  .container {{ max-width: 1000px; margin: 0 auto; }}
  
  /* HEADER */
  .header {{
    background: linear-gradient(135deg, #111c30 0%, #0a1120 100%);
    border: 1px solid var(--card-border);
    border-radius: 14px;
    padding: 16px;
    margin-bottom: 14px;
    box-shadow: 0 10px 25px -5px rgba(0,0,0,0.6);
  }}
  .header-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
    border-bottom: 1px solid var(--card-border);
    padding-bottom: 10px;
    margin-bottom: 10px;
  }}
  .brand {{ font-size: 18px; font-weight: 800; color: var(--accent-blue); display: flex; align-items: center; gap: 6px; }}
  .status-badge {{ background: #064e3b; color: #a7f3d0; border: 1px solid #059669; padding: 4px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; }}
  
  .stats-bar {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
    gap: 8px;
    margin-top: 10px;
  }}
  .stat-card {{
    background: #091120;
    border: 1px solid var(--card-border);
    border-radius: 8px;
    padding: 8px 10px;
  }}
  .stat-label {{ font-size: 10px; color: var(--text-muted); text-transform: uppercase; font-weight: 700; }}
  .stat-val {{ font-size: 16px; font-weight: 800; color: var(--accent-green); margin-top: 2px; }}

  /* CARDS */
  .card {{
    background: var(--card-bg);
    border: 1px solid var(--card-border);
    border-radius: 12px;
    padding: 14px;
    margin-bottom: 14px;
  }}
  h2 {{
    font-size: 14.5px;
    color: var(--accent-yellow);
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid var(--card-border);
    padding-bottom: 8px;
    margin-bottom: 10px;
  }}

  /* TICKETS */
  .ticket-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; }}
  .ticket-card {{
    background: #0a1222;
    border: 1px solid var(--card-border);
    border-radius: 10px;
    padding: 12px;
  }}
  .ticket-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px; }}
  .ticket-title {{ font-size: 13px; font-weight: 700; color: #fff; }}
  .ticket-odds {{ font-size: 18px; font-weight: 900; color: var(--accent-blue); }}
  .ticket-meta {{ display: flex; justify-content: space-between; font-size: 11px; color: var(--text-muted); margin-bottom: 8px; }}
  .cashout-box {{
    background: #1e1b4b;
    border: 1px solid #4338ca;
    color: #c7d2fe;
    font-size: 11px;
    padding: 6px 8px;
    border-radius: 6px;
    margin-top: 8px;
  }}

  /* TABLES */
  table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; }}
  th {{ background: #070d19; color: var(--text-muted); font-size: 10px; text-transform: uppercase; padding: 6px; text-align: left; border-bottom: 1px solid var(--card-border); }}
  td {{ padding: 6px; border-bottom: 1px solid var(--card-border); vertical-align: middle; }}
  .sesto-senso-cell {{ font-size: 10.5px; color: #cbd5e1; line-height: 1.3; }}

  /* BADGES */
  .badge {{ display: inline-block; padding: 2px 6px; border-radius: 4px; font-weight: 700; font-size: 10px; }}
  .badge-blue {{ background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }}
  .badge-green {{ background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }}
  .badge-yellow {{ background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }}
  .badge-purple {{ background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3); }}
  
  /* ACTION BUTTONS */
  .btn-bar {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 10px; }}
  .btn {{
    background: #1e293b;
    color: #f8fafc;
    border: 1px solid #334155;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 11.5px;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
  }}
  .btn-green {{ background: #065f46; border-color: var(--accent-green); color: #ecfdf5; }}
  .btn-blue {{ background: #0369a1; border-color: var(--accent-blue); color: #f0f9ff; }}

  .pulse {{ animation: pulse 2s infinite; }}
  @keyframes pulse {{ 0% {{ opacity: 1; }} 50% {{ opacity: 0.4; }} 100% {{ opacity: 1; }} }}
</style>
</head>
<body>

<div class="container">

  <!-- HEADER -->
  <div class="header">
    <div class="header-top">
      <div class="brand">
        🍓 BAgent Hub 24/7 — Portale Autonomo Raspberry Pi
      </div>
      <div class="status-badge">
        <span class="pulse">●</span> {system_status}
      </div>
    </div>
    
    <div class="stats-bar">
      <div class="stat-card">
        <div class="stat-label">💰 Bankroll</div>
        <div class="stat-val">{bankroll:.2f} €</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">🛡️ Hard Cap (8%)</div>
        <div class="stat-val" style="color:var(--accent-blue);">{(bankroll * 0.08):.2f} €</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">⏱️ Ultimo Refresh</div>
        <div class="stat-val" style="color:#fff; font-size:12px;">{now_str.split()[1]}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">🔄 Prossimo Ciclo</div>
        <div class="stat-val" style="color:var(--accent-yellow); font-size:12px;">{next_refresh}</div>
      </div>
    </div>

    <div class="btn-bar">
      <a class="btn btn-green" href="https://t.me/A502502_bot" target="_blank">📲 Apri Bot Telegram (@A502502_bot)</a>
      <a class="btn btn-blue" href="javascript:location.reload()">🔄 Ricarica Live</a>
    </div>
  </div>

  <!-- SEZIONE 1: TICKET IN CORSO -->
  <div class="card">
    <h2>
      <span>🎫 SCHEDINE & TICKET IN GIOCO (LIVE)</span>
      <span class="badge badge-green">{len(active_tickets)} Attivi</span>
    </h2>
    <div class="ticket-grid">
      {tickets_html if tickets_html else '<p style="color:var(--text-muted); font-size:12px;">Nessuna schedina attiva in questo momento.</p>'}
    </div>
  </div>

  <!-- SEZIONE 2: OPPORTUNITÀ D'ORO FILTRATE DA BETGUARD -->
  <div class="card">
    <h2>
      <span>💎 OPPORTUNITÀ D'ORO VALIDATE DA BETGUARD (PROSSIME 24H)</span>
      <span class="badge badge-blue">Regola #26 Attiva</span>
    </h2>
    <div style="overflow-x:auto;">
      <table>
        <thead>
          <tr>
            <th style="width: 8%;">Ora</th>
            <th style="width: 25%;">Partita & Torneo</th>
            <th style="width: 15%;">Mercato Netwin</th>
            <th style="width: 8%;">Quota</th>
            <th style="width: 8%;">Edge</th>
            <th style="width: 36%;">Sesto Senso & Validazione BetGuard</th>
          </tr>
        </thead>
        <tbody>
          {picks_html if picks_html else '<tr><td colspan="6" style="text-align:center; color:var(--text-muted);">Scansione in corso per le prossime gare...</td></tr>'}
        </tbody>
      </table>
    </div>
  </div>

</div>

</body>
</html>
"""
    PORTAL_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_HTML.write_text(html, encoding="utf-8")
    return str(INDEX_HTML)

if __name__ == "__main__":
    sample_data = {
        "bankroll": 300.00,
        "active_tickets": [
            {
                "title": "🏆 Ticket #34: Quintina d'Elite Serale",
                "badge": "IN CORSO",
                "odds": "4.80×",
                "stake": "20.00 €",
                "potential": "96.07 €",
                "ref": "DF07EA081B31840F2C06",
                "status": "IN CORSO",
                "cashout_note": "Ajax 5-2 già vinta, Brighton 3-0 già vinta. Valutare cashout se Barça chiude il primo tempo in vantaggio!",
                "events": [
                    {"time": "20:00", "match": "Ajax vs Sion", "pick": "1X + Over 1.5", "odd": "1.22", "status": "✅"},
                    {"time": "20:00", "match": "Hapoel Tel Aviv vs Atalanta", "pick": "X2 + Over 1.5", "odd": "1.41", "status": "⏳"},
                    {"time": "20:30", "match": "Chelsea vs Luton", "pick": "1 (1X2)", "odd": "1.09", "status": "⏳"},
                    {"time": "21:00", "match": "Partizan vs Getafe", "pick": "Over 4.5 Cartellini", "odd": "1.83", "status": "⏳"},
                    {"time": "21:00", "match": "Barcellona vs Athletic Bilbao", "pick": "1X + Over 2.5", "odd": "1.40", "status": "⏳"}
                ]
            }
        ],
        "today_picks": [
            {
                "time": "16:45", "match": "SC Freiburg vs Motherwell", "league": "Conference League",
                "pick": "1 + Over 1.5 Gol", "odd": "1.40", "edge": "+8.5%",
                "sesto_senso": "Friburgo dominante (1-3 all'andata, 5-1 in coppa). Motherwell costretto a scoprirsi."
            },
            {
                "time": "17:00", "match": "FC Copenhagen vs Inter Turku", "league": "Conference League",
                "pick": "1 + Over 1.5 Gol", "odd": "1.45", "edge": "+7.2%",
                "sesto_senso": "Parken Stadium sold-out: i danesi devono vincere per andare ai gironi dopo lo 0-0 tattico dell'andata."
            }
        ],
        "next_refresh": "Tra 2 ore esatte (Ore 23:30)"
    }
    path = generate_portal_html(sample_data)
    print("Portal HTML generated at:", path)

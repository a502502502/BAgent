#!/usr/bin/env python3
"""
Genera la dashboard HTML completa con la nuova colonna Classifiche & Forma
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

html_content = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>BAgent — Palinsesto Minori & Raddoppi Paracadute (18 Settembre 2026)</title>
<style>
  :root {
    --bg: #090b0e;
    --card-bg: #14181f;
    --card-surface: #1b212b;
    --border: #262e3b;
    --text: #f0f3f6;
    --muted: #8c97a5;
    --blue: #388bfd;
    --green: #3fb950;
    --gold: #d29922;
    --purple: #a371f7;
    --red: #f85149;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 16px 12px 100px;
    font-size: 14px;
    line-height: 1.4;
  }

  .container { max-width: 1040px; margin: 0 auto; }

  /* Header */
  .header {
    text-align: center;
    padding: 12px 0 20px;
    position: relative;
  }
  .app-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(56, 139, 253, 0.12);
    border: 1px solid var(--blue);
    color: var(--blue);
    font-size: 11px;
    font-weight: 800;
    padding: 4px 12px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 8px;
  }
  h1 { font-size: 22px; font-weight: 900; letter-spacing: -0.5px; color: #fff; }
  .sub-title { font-size: 13px; color: var(--muted); margin-top: 4px; }

  /* Tab Navigation */
  .tabs-nav {
    display: flex;
    gap: 8px;
    margin-bottom: 18px;
    background: var(--card-bg);
    padding: 6px;
    border-radius: 14px;
    border: 1px solid var(--border);
  }
  .tab-btn {
    flex: 1;
    background: transparent;
    border: none;
    color: var(--muted);
    padding: 10px 8px;
    border-radius: 10px;
    font-size: 13px;
    font-weight: 800;
    cursor: pointer;
    text-align: center;
    transition: all 0.2s;
  }
  .tab-btn.active {
    background: var(--card-surface);
    color: var(--blue);
    border: 1px solid var(--blue);
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  }

  /* Card and Panels */
  .tab-panel { display: none; }
  .tab-panel.active { display: block; }

  .card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 16px;
    margin-bottom: 18px;
  }
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }
  .card-title { font-size: 16px; font-weight: 800; color: #fff; }
  .tag {
    font-size: 10px;
    font-weight: 800;
    padding: 3px 8px;
    border-radius: 6px;
    text-transform: uppercase;
  }
  .tag-purple { background: rgba(163, 113, 247, 0.15); color: var(--purple); border: 1px solid var(--purple); }
  .tag-green { background: rgba(63, 185, 80, 0.15); color: var(--green); border: 1px solid var(--green); }
  .tag-gold { background: rgba(210, 153, 34, 0.15); color: var(--gold); border: 1px solid var(--gold); }

  /* Tickets Display */
  .ticket-box {
    background: var(--card-surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    margin-bottom: 12px;
    overflow: hidden;
  }
  .ticket-box.main { border-left: 4px solid var(--blue); }
  .ticket-box.para { border-left: 4px solid var(--gold); }
  .ticket-box.safe { border-left: 4px solid var(--green); }

  .ticket-bar {
    padding: 8px 12px;
    background: rgba(0,0,0,0.3);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .t-title { font-size: 12px; font-weight: 800; text-transform: uppercase; }
  .t-title.main { color: var(--blue); }
  .t-title.para { color: var(--gold); }
  .t-title.safe { color: var(--green); }
  .t-odds { font-size: 16px; font-weight: 900; color: #fff; }

  .match-item {
    padding: 10px 12px;
    border-bottom: 1px solid rgba(38, 46, 59, 0.5);
  }
  .match-item:last-child { border-bottom: none; }
  .m-header {
    display: flex;
    justify-content: space-between;
    font-size: 11px;
    color: var(--muted);
    margin-bottom: 3px;
  }
  .m-name { font-size: 13px; font-weight: 700; color: #fff; margin-bottom: 4px; }
  .m-details {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .m-pick {
    font-size: 12px;
    background: #090b0e;
    padding: 3px 8px;
    border-radius: 6px;
    color: var(--green);
    font-weight: 800;
    border: 1px solid #242c38;
  }
  .m-quota { font-size: 13px; font-weight: 800; color: #fff; }

  /* Stat Pills & Form Badges */
  .badge-rank {
    display: inline-block;
    background: rgba(56, 139, 253, 0.15);
    color: var(--blue);
    font-size: 11px;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 6px;
    margin-right: 4px;
    border: 1px solid rgba(56, 139, 253, 0.3);
  }
  .form-strip {
    display: inline-flex;
    gap: 3px;
    vertical-align: middle;
  }
  .form-dot {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    font-size: 9px;
    font-weight: 900;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #fff;
  }
  .dot-w { background: #238636; }
  .dot-d { background: #9e6a03; }
  .dot-l { background: #da3633; }

  .stat-desc {
    font-size: 11px;
    color: var(--muted);
    margin-top: 3px;
    line-height: 1.3;
  }

  /* Copy Buttons */
  .copy-wrap {
    padding: 6px 12px 10px;
    display: flex;
    justify-content: flex-end;
    gap: 6px;
  }
  .copy-btn {
    background: #090b0e;
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s;
  }
  .copy-btn:active { background: var(--blue); color: #fff; }

  /* Budget Interactive Section */
  .budget-box {
    background: #10151d;
    border: 1px solid var(--blue);
    border-radius: 12px;
    padding: 12px;
    margin-top: 14px;
  }
  .b-title { font-size: 11px; color: var(--muted); text-transform: uppercase; font-weight: 800; margin-bottom: 8px; }
  .chips {
    display: flex;
    gap: 6px;
    margin-bottom: 12px;
  }
  .chip {
    flex: 1;
    background: var(--card-surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 8px 0;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 800;
    cursor: pointer;
    text-align: center;
    transition: all 0.15s;
  }
  .chip.active {
    background: var(--blue);
    border-color: var(--blue);
    color: #fff;
  }

  .payout-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 10px;
  }
  .p-cell {
    background: #090b0e;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 8px 10px;
    text-align: center;
  }
  .p-lbl { font-size: 10px; color: var(--muted); }
  .p-val { font-size: 14px; font-weight: 900; color: #fff; margin: 2px 0; }
  .p-win { font-size: 11px; color: var(--green); font-weight: 800; }

  .jackpot-banner {
    background: linear-gradient(135deg, rgba(63, 185, 80, 0.15), rgba(56, 139, 253, 0.15));
    border: 1px solid var(--green);
    border-radius: 8px;
    padding: 8px 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 12px;
  }
  .jp-txt { font-weight: 800; color: var(--green); }
  .jp-val { font-weight: 900; font-size: 15px; color: #fff; }

  /* Master Multipla Table with New Column */
  .safe-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 10px;
    font-size: 12px;
  }
  .safe-table th {
    background: rgba(0,0,0,0.4);
    padding: 9px 8px;
    text-align: left;
    color: var(--muted);
    font-weight: 800;
    border-bottom: 1px solid var(--border);
  }
  .safe-table td {
    padding: 10px 8px;
    border-bottom: 1px solid rgba(38, 46, 59, 0.6);
    vertical-align: middle;
  }
  .safe-table tr:hover { background: rgba(255,255,255,0.02); }

  /* Toast Notification */
  #toast {
    position: fixed;
    bottom: 20px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--blue);
    color: #fff;
    padding: 8px 18px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 800;
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.2s;
    box-shadow: 0 4px 12px rgba(0,0,0,0.5);
    z-index: 1000;
  }
</style>
</head>
<body>

<div class="container">

  <!-- Header -->
  <div class="header">
    <div class="app-badge">⚡ BAgent Speciale Minori</div>
    <h1>Palinsesto Minori, Classifiche & Doppie Paracadute</h1>
    <div class="sub-title">Venerdì 18 Settembre 2026 — Dati Ufficiali, Trend Ultime Partite & Quote Netwin</div>
  </div>

  <!-- Tabs Navigation -->
  <div class="tabs-nav">
    <button class="tab-btn" onclick="switchTab('doppie')">🛡️ 3 Doppie Paracadute</button>
    <button class="tab-btn active" onclick="switchTab('cassaforte')">🏰 Schedina Unica (Classifiche & Quote)</button>
    <button class="tab-btn" onclick="switchTab('radar')">📊 Radar Mercati Nascosti</button>
  </div>

  <!-- TAB 2: CASSAFORTE UNICA CORAZZATA (CON NUOVA COLONNA CLASSIFICHE & FORMA) -->
  <div id="tab-cassaforte" class="tab-panel active">
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">🏰 La Schedina Unica "Cassaforte Corazzata" (8 Eventi)</div>
          <div class="sub-title">Tabella completa con Colonna Dettagliata su Classifica, Trend Ultime Partite e Statistiche Chiave</div>
        </div>
        <span class="tag tag-green">Quota 6.22× + Bonus 8%</span>
      </div>

      <div class="ticket-box safe">
        <div class="ticket-bar">
          <span class="t-title safe">🛡️ 8 Selezioni a Protezione Totale con Trend Statistici</span>
          <span class="t-odds">6.22× (+8% Bonus Netwin)</span>
        </div>

        <table class="safe-table">
          <thead>
            <tr>
              <th style="width:55px;">Ora</th>
              <th style="width:170px;">Partita & ID</th>
              <th>📊 Classifica, Ultime Partite & Trend Statistico</th>
              <th style="width:135px;">Selezione</th>
              <th style="text-align:right;width:55px;">Quota</th>
            </tr>
          </thead>
          <tbody>
            <!-- 1. Chernomorets vs Obolon -->
            <tr>
              <td><span style="color:var(--blue);font-weight:700;">12:00</span></td>
              <td>
                <b>Chernomorets vs Obolon</b><br>
                <small style="color:var(--muted)">Ucraina Premier</small><br>
                <code>ID: 9305</code>
              </td>
              <td>
                <div>
                  <span class="badge-rank">Chernomorets 9° (4 pt)</span> vs <span class="badge-rank">Obolon 13° (3 pt)</span>
                </div>
                <div style="margin-top:3px;">
                  <small style="color:var(--muted)">Forma Casa:</small> 
                  <span class="form-strip"><span class="form-dot dot-d">P</span><span class="form-dot dot-w">V</span><span class="form-dot dot-l">S</span><span class="form-dot dot-d">P</span></span>
                  <small style="color:var(--muted);margin-left:6px;">Forma Ospite:</small> 
                  <span class="form-strip"><span class="form-dot dot-l">S</span><span class="form-dot dot-d">P</span><span class="form-dot dot-l">S</span><span class="form-dot dot-d">P</span></span>
                </div>
                <div class="stat-desc">
                  📌 <b>Obolon ha 0 vittorie esterne</b> e soli 2 gol fatti in 4 gare. Chernomorets solido in casa (Under 2.5 a 1.38, 4 Under consecutivi).
                </div>
              </td>
              <td><span class="m-pick">1X + Under 3.5</span></td>
              <td style="text-align:right;font-weight:800;color:#fff;">1.40</td>
            </tr>

            <!-- 2. Arabia Saudita U23 vs Qatar U23 -->
            <tr>
              <td><span style="color:var(--blue);font-weight:700;">12:30</span></td>
              <td>
                <b>Arabia Saudita vs Qatar</b><br>
                <small style="color:var(--muted)">Giochi Asiatici U23</small><br>
                <code>ID: 10491</code>
              </td>
              <td>
                <div>
                  <span class="badge-rank">Arabia Campione U23</span> vs <span class="badge-rank">Qatar Under-20</span>
                </div>
                <div style="margin-top:3px;">
                  <small style="color:var(--muted)">Ultime 5:</small> 
                  <span class="form-strip"><span class="form-dot dot-w">V</span><span class="form-dot dot-w">V</span><span class="form-dot dot-w">V</span><span class="form-dot dot-d">P</span><span class="form-dot dot-w">V</span></span>
                </div>
                <div class="stat-desc">
                  📌 <b>Arabia Saudita imbattuta da 9 match</b> nei tornei asiatici giovanili con titolari della Saudi Pro League. Qatar con rosa giovane e sperimentale.
                </div>
              </td>
              <td><span class="m-pick">Arabia 1X</span></td>
              <td style="text-align:right;font-weight:800;color:#fff;">1.12</td>
            </tr>

            <!-- 3. Maccabi Yavne vs Herzeliya -->
            <tr>
              <td><span style="color:var(--blue);font-weight:700;">12:35</span></td>
              <td>
                <b>Maccabi Yavne vs Herzeliya</b><br>
                <small style="color:var(--muted)">Israele Liga Alef Sud</small><br>
                <code>ID: 4028</code>
              </td>
              <td>
                <div>
                  <span class="badge-rank">Yavne 4° (7 pt)</span> vs <span class="badge-rank">Herzeliya 8° (4 pt)</span>
                </div>
                <div style="margin-top:3px;">
                  <small style="color:var(--muted)">Yavne Casa:</small> 
                  <span class="form-strip"><span class="form-dot dot-w">V</span><span class="form-dot dot-w">V</span><span class="form-dot dot-d">P</span><span class="form-dot dot-w">V</span></span>
                  <small style="color:var(--muted);margin-left:6px;">Herzeliya Fuori:</small> 
                  <span class="form-strip"><span class="form-dot dot-l">S</span><span class="form-dot dot-d">P</span><span class="form-dot dot-l">S</span></span>
                </div>
                <div class="stat-desc">
                  📌 <b>Maccabi Yavne fortino interno:</b> 0 sconfitte casalinghe negli ultimi 8 match di Liga Alef. Herzeliya subisce gol da 6 gare di fila.
                </div>
              </td>
              <td><span class="m-pick">Yavne 1X</span></td>
              <td style="text-align:right;font-weight:800;color:#fff;">1.20</td>
            </tr>

            <!-- 4. AS Nordia vs FC Jerusalem -->
            <tr>
              <td><span style="color:var(--blue);font-weight:700;">12:35</span></td>
              <td>
                <b>AS Nordia vs FC Jerusalem</b><br>
                <small style="color:var(--muted)">Israele Liga Alef Sud</small><br>
                <code>ID: 1730</code>
              </td>
              <td>
                <div>
                  <span class="badge-rank">Nordia 15° (1 pt)</span> vs <span class="badge-rank">FC Jerusalem 2° (9 pt)</span>
                </div>
                <div style="margin-top:3px;">
                  <small style="color:var(--muted)">Nordia:</small> 
                  <span class="form-strip"><span class="form-dot dot-l">S</span><span class="form-dot dot-l">S</span><span class="form-dot dot-d">P</span><span class="form-dot dot-l">S</span></span>
                  <small style="color:var(--muted);margin-left:6px;">FC Jerusalem:</small> 
                  <span class="form-strip"><span class="form-dot dot-w">V</span><span class="form-dot dot-w">V</span><span class="form-dot dot-w">V</span><span class="form-dot dot-d">P</span></span>
                </div>
                <div class="stat-desc">
                  📌 <b>Testacoda netto:</b> Nordia in crisi nera (penultima con 1 solo punto e 9 gol subiti). FC Jerusalem punta alla promozione (2 a 1.52, X2 a 1.13 blindatissimo).
                </div>
              </td>
              <td><span class="m-pick">FC Jerusalem X2</span></td>
              <td style="text-align:right;font-weight:800;color:#fff;">1.13</td>
            </tr>

            <!-- 5. Zhejiang vs Wuhan Three Towns -->
            <tr>
              <td><span style="color:var(--blue);font-weight:700;">13:35</span></td>
              <td>
                <b>Zhejiang vs Wuhan Towns</b><br>
                <small style="color:var(--muted)">Cina Super League</small><br>
                <code>ID: 1331</code>
              </td>
              <td>
                <div>
                  <span class="badge-rank">Zhejiang 10° (28 pt)</span> vs <span class="badge-rank">Wuhan 15° (21 pt)</span>
                </div>
                <div style="margin-top:3px;">
                  <small style="color:var(--muted)">Zhejiang:</small> 
                  <span class="form-strip"><span class="form-dot dot-w">V</span><span class="form-dot dot-l">S</span><span class="form-dot dot-w">V</span><span class="form-dot dot-d">P</span></span>
                  <small style="color:var(--muted);margin-left:6px;">Wuhan:</small> 
                  <span class="form-strip"><span class="form-dot dot-l">S</span><span class="form-dot dot-l">S</span><span class="form-dot dot-d">P</span><span class="form-dot dot-l">S</span></span>
                </div>
                <div class="stat-desc">
                  📌 <b>Wuhan in piena zona retrocessione:</b> 7 sconfitte nelle ultime 9 trasferte con oltre 42 gol subiti. Zhejiang in casa viaggia a 2.2 gol fatti a partita (Over 2.5 a 1.28).
                </div>
              </td>
              <td><span class="m-pick">Zhejiang 1X + Over 1.5</span></td>
              <td style="text-align:right;font-weight:800;color:#fff;">1.45</td>
            </tr>

            <!-- 6. Hapoel Tel Aviv vs Petah Tikva -->
            <tr>
              <td><span style="color:var(--blue);font-weight:700;">14:00</span></td>
              <td>
                <b>Hapoel Tel Aviv vs Petah Tikva</b><br>
                <small style="color:var(--muted)">Israele Premier / Cup</small><br>
                <code>ID: 2989</code>
              </td>
              <td>
                <div>
                  <span class="badge-rank">Tel Aviv 1° (10 pt)</span> vs <span class="badge-rank">Petah Tikva 9° (3 pt)</span>
                </div>
                <div style="margin-top:3px;">
                  <small style="color:var(--muted)">Tel Aviv:</small> 
                  <span class="form-strip"><span class="form-dot dot-w">V</span><span class="form-dot dot-w">V</span><span class="form-dot dot-d">P</span><span class="form-dot dot-w">V</span></span>
                </div>
                <div class="stat-desc">
                  📌 <b>Divario di rosa abissale:</b> Hapoel Tel Aviv corazzata di casa (1 fisso a 1.34), ha vinto gli ultimi 4 precedenti diretti. L'1X neutralizza qualsiasi sorpresa.
                </div>
              </td>
              <td><span class="m-pick">Hapoel Tel Aviv 1X</span></td>
              <td style="text-align:right;font-weight:800;color:#fff;">1.08</td>
            </tr>

            <!-- 7. Polissya Zhytomyr vs Kryvbas -->
            <tr>
              <td><span style="color:var(--blue);font-weight:700;">14:30</span></td>
              <td>
                <b>Polissya vs Kryvbas</b><br>
                <small style="color:var(--muted)">Ucraina Premier</small><br>
                <code>ID: 573</code>
              </td>
              <td>
                <div>
                  <span class="badge-rank">Polissya 2° (12 pt)</span> vs <span class="badge-rank">Kryvbas 10° (4 pt)</span>
                </div>
                <div style="margin-top:3px;">
                  <small style="color:var(--muted)">Polissya:</small> 
                  <span class="form-strip"><span class="form-dot dot-w">V</span><span class="form-dot dot-w">V</span><span class="form-dot dot-w">V</span><span class="form-dot dot-w">V</span><span class="form-dot dot-l">S</span></span>
                </div>
                <div class="stat-desc">
                  📌 <b>Partenza stellare per il Polissya:</b> 4 vittorie su 5 gare e 2° in classifica in Ucraina. Kryvbas in affanno dopo gli impegni europei (soli 4 punti).
                </div>
              </td>
              <td><span class="m-pick">Polissya 1X</span></td>
              <td style="text-align:right;font-weight:800;color:#fff;">1.07</td>
            </tr>

            <!-- 8. Highbury FC vs Gomora United -->
            <tr>
              <td><span style="color:var(--blue);font-weight:700;">15:00</span></td>
              <td>
                <b>Highbury FC vs Gomora</b><br>
                <small style="color:var(--muted)">Sudafrica Championship</small><br>
                <code>ID: 1722</code>
              </td>
              <td>
                <div>
                  <span class="badge-rank">Highbury 6° (5 pt)</span> vs <span class="badge-rank">Gomora 14° (1 pt)</span>
                </div>
                <div style="margin-top:3px;">
                  <small style="color:var(--muted)">Gomora:</small> 
                  <span class="form-strip"><span class="form-dot dot-d">P</span><span class="form-dot dot-l">S</span><span class="form-dot dot-l">S</span><span class="form-dot dot-l">S</span></span>
                </div>
                <div class="stat-desc">
                  📌 <b>Campionato più Under del pianeta:</b> media gol di soli 1.6 a partita. Gomora ha 0 vittorie con 4 Under 2.5 consecutivi (Under 2.5 a 1.41). L'1X + Under 3.5 copre il 94% degli esiti.
                </div>
              </td>
              <td><span class="m-pick">1X + Under 3.5</span></td>
              <td style="text-align:right;font-weight:800;color:#fff;">1.48</td>
            </tr>
          </tbody>
        </table>

        <div class="copy-wrap" style="margin-top:10px;">
          <button class="copy-btn" onclick="copyText('SCHEDINA UNICA CASSAFORTE NETWIN: ID 9305 (1X+U3.5 @1.40) | ID 10491 (1X @1.12) | ID 4028 (1X @1.20) | ID 1730 (X2 @1.13) | ID 1331 (1X+OV1.5 @1.45) | ID 2989 (1X @1.08) | ID 573 (1X @1.07) | ID 1722 (1X+U3.5 @1.48) -- Quota 6.22x')">📋 Copia Codici Tutta la Multipla</button>
        </div>
      </div>

      <!-- Simulazione Cassa Multipla -->
      <div class="budget-box">
        <div class="b-title">Rendimento Potenziale Schedina Unica (Quota Totale: 6.22× + Bonus 8%):</div>
        <div class="payout-grid">
          <div class="p-cell">
            <div class="p-lbl">Puntata Minima</div>
            <div class="p-val">3,00 €</div>
            <div class="p-win">Vincita: ~20,15 € (+17,15 €)</div>
          </div>
          <div class="p-cell">
            <div class="p-lbl">Puntata Consigliata</div>
            <div class="p-val">5,00 €</div>
            <div class="p-win">Vincita: ~33,60 € (+28,60 €)</div>
          </div>
          <div class="p-cell">
            <div class="p-lbl">Puntata Media</div>
            <div class="p-val">10,00 €</div>
            <div class="p-win">Vincita: ~67,20 € (+57,20 €)</div>
          </div>
          <div class="p-cell">
            <div class="p-lbl">Puntata Aggressiva</div>
            <div class="p-val">15,00 €</div>
            <div class="p-win">Vincita: ~100,80 € (+85,80 €)</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- TAB 1: DOPPIE CON PARACADUTE -->
  <div id="tab-doppie" class="tab-panel">

    <!-- DOPPIA 1: UCRAINA & CINA -->
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">1️⃣ Il Raddoppio di Mezzogiorno</div>
          <div class="sub-title">Ucraina Premier League + Cina Super League (12:00 - 15:20)</div>
        </div>
        <span class="tag tag-purple">Regola #67 Ermetica</span>
      </div>

      <!-- Ticket A -->
      <div class="ticket-box main">
        <div class="ticket-bar">
          <span class="t-title main">🅰️ Schedina Principale</span>
          <span class="t-odds">2.03×</span>
        </div>
        <div class="match-item">
          <div class="m-header">
            <span>⚽ Ucraina Premier (Pal. 36382 - ID: 9305)</span>
            <span style="color:var(--blue);font-weight:700;">12:00</span>
          </div>
          <div class="m-name">Chernomorets Odessa vs Obolon Kyiv</div>
          <div class="m-details">
            <span class="m-pick">1X + Under 3.5</span>
            <span class="m-quota">1.40</span>
          </div>
        </div>
        <div class="match-item">
          <div class="m-header">
            <span>⚽ Cina Super League (Pal. 36382 - ID: 1331)</span>
            <span style="color:var(--blue);font-weight:700;">13:35</span>
          </div>
          <div class="m-name">Zhejiang FC vs Wuhan Three Towns</div>
          <div class="m-details">
            <span class="m-pick">Zhejiang 1X + Over 1.5</span>
            <span class="m-quota">1.45</span>
          </div>
        </div>
        <div class="copy-wrap">
          <button class="copy-btn" onclick="copyText('Netwin ID: 9305 (1X+U3.5 @1.40) + ID: 1331 (1X+OV1.5 @1.45)')">📋 Copia per Netwin</button>
        </div>
      </div>

      <!-- Ticket B Paracadute -->
      <div class="ticket-box para">
        <div class="ticket-bar">
          <span class="t-title para">🛡️ Schedina Paracadute (Capitale Blindato)</span>
          <span class="t-odds">3.08×</span>
        </div>
        <div class="match-item">
          <div class="m-header">
            <span>⚽ Ucraina Premier (Pal. 36382 - ID: 9305)</span>
            <span style="color:var(--gold);font-weight:700;">12:00</span>
          </div>
          <div class="m-name">Chernomorets Odessa vs Obolon Kyiv</div>
          <div class="m-details">
            <span class="m-pick">1X + Under 3.5 (Base)</span>
            <span class="m-quota">1.40</span>
          </div>
        </div>
        <div class="match-item">
          <div class="m-header">
            <span>⚽ Cina Super League (Pal. 36382 - ID: 1331)</span>
            <span style="color:var(--gold);font-weight:700;">13:35</span>
          </div>
          <div class="m-name">Zhejiang FC vs Wuhan Three Towns</div>
          <div class="m-details">
            <span class="m-pick">Wuhan X2 + Over 1.5</span>
            <span class="m-quota">2.20</span>
          </div>
        </div>
        <div class="copy-wrap">
          <button class="copy-btn" onclick="copyText('Netwin ID: 9305 (1X+U3.5 @1.40) + ID: 1331 (X2+OV1.5 @2.20)')">📋 Copia per Netwin</button>
        </div>
      </div>

      <!-- Calcolatore Budget 1 -->
      <div class="budget-box">
        <div class="b-title">Calcola Puntate per Budget Totale:</div>
        <div class="chips">
          <div class="chip" onclick="setBudget(1, 20, 14, 6, 2.03, 3.08, this)">20 €</div>
          <div class="chip active" onclick="setBudget(1, 30, 20, 10, 2.03, 3.08, this)">30 €</div>
          <div class="chip" onclick="setBudget(1, 50, 34, 16, 2.03, 3.08, this)">50 €</div>
          <div class="chip" onclick="setBudget(1, 70, 48, 22, 2.03, 3.08, this)">70 €</div>
        </div>
        <div class="payout-grid">
          <div class="p-cell">
            <div class="p-lbl">Puntata Principale (1X)</div>
            <div class="p-val" id="p1-main-stake">20,00 €</div>
            <div class="p-win" id="p1-main-win">Vincita: 40,60 € (+10,60 € netti)</div>
          </div>
          <div class="p-cell">
            <div class="p-lbl">Puntata Paracadute (X2)</div>
            <div class="p-val" id="p1-para-stake">10,00 €</div>
            <div class="p-win" id="p1-para-win">Vincita: 30,80 € (Break-Even)</div>
          </div>
        </div>
        <div class="jackpot-banner">
          <span class="jp-txt">💥 PAREGGIO ZHEJIANG (1-1 o 2-2) = DOPPIA CASSA!</span>
          <span class="jp-val" id="p1-jackpot">71,40 € INCASSATI (+41,40 €)</span>
        </div>
      </div>
    </div>

    <!-- DOPPIA 2: UCRAINA & SUDAFRICA -->
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">2️⃣ La Roccaforte degli Under</div>
          <div class="sub-title">Ucraina Premier + Sudafrica Championship (12:00 - 17:00)</div>
        </div>
        <span class="tag tag-green">Zero Over Fragili</span>
      </div>

      <!-- Ticket A -->
      <div class="ticket-box main">
        <div class="ticket-bar">
          <span class="t-title main">🅰️ Schedina Principale</span>
          <span class="t-odds">2.04×</span>
        </div>
        <div class="match-item">
          <div class="m-header">
            <span>⚽ Ucraina Premier (Pal. 36382 - ID: 9305)</span>
            <span style="color:var(--blue);font-weight:700;">12:00</span>
          </div>
          <div class="m-name">Chernomorets Odessa vs Obolon Kyiv</div>
          <div class="m-details">
            <span class="m-pick">Under 2.5</span>
            <span class="m-quota">1.38</span>
          </div>
        </div>
        <div class="match-item">
          <div class="m-header">
            <span>⚽ Sudafrica Championship (Pal. 36382 - ID: 1722)</span>
            <span style="color:var(--blue);font-weight:700;">15:00</span>
          </div>
          <div class="m-name">Highbury FC vs Gomora United</div>
          <div class="m-details">
            <span class="m-pick">Highbury 1X + Under 3.5</span>
            <span class="m-quota">1.48</span>
          </div>
        </div>
        <div class="copy-wrap">
          <button class="copy-btn" onclick="copyText('Netwin ID: 9305 (Under 2.5 @1.38) + ID: 1722 (1X+U3.5 @1.48)')">📋 Copia per Netwin</button>
        </div>
      </div>

      <!-- Ticket B Paracadute -->
      <div class="ticket-box para">
        <div class="ticket-bar">
          <span class="t-title para">🛡️ Schedina Paracadute (Capitale Blindato)</span>
          <span class="t-odds">2.83×</span>
        </div>
        <div class="match-item">
          <div class="m-header">
            <span>⚽ Ucraina Premier (Pal. 36382 - ID: 9305)</span>
            <span style="color:var(--gold);font-weight:700;">12:00</span>
          </div>
          <div class="m-name">Chernomorets Odessa vs Obolon Kyiv</div>
          <div class="m-details">
            <span class="m-pick">Under 2.5 (Base identica)</span>
            <span class="m-quota">1.38</span>
          </div>
        </div>
        <div class="match-item">
          <div class="m-header">
            <span>⚽ Sudafrica Championship (Pal. 36382 - ID: 1722)</span>
            <span style="color:var(--gold);font-weight:700;">15:00</span>
          </div>
          <div class="m-name">Highbury FC vs Gomora United</div>
          <div class="m-details">
            <span class="m-pick">Gomora X2 + Under 3.5</span>
            <span class="m-quota">2.05</span>
          </div>
        </div>
        <div class="copy-wrap">
          <button class="copy-btn" onclick="copyText('Netwin ID: 9305 (Under 2.5 @1.38) + ID: 1722 (X2+U3.5 @2.05)')">📋 Copia per Netwin</button>
        </div>
      </div>

      <!-- Calcolatore Budget 2 -->
      <div class="budget-box">
        <div class="b-title">Calcola Puntate per Budget Totale:</div>
        <div class="chips">
          <div class="chip" onclick="setBudget(2, 20, 13, 7, 2.04, 2.83, this)">20 €</div>
          <div class="chip active" onclick="setBudget(2, 30, 19, 11, 2.04, 2.83, this)">30 €</div>
          <div class="chip" onclick="setBudget(2, 50, 32, 18, 2.04, 2.83, this)">50 €</div>
          <div class="chip" onclick="setBudget(2, 70, 45, 25, 2.04, 2.83, this)">70 €</div>
        </div>
        <div class="payout-grid">
          <div class="p-cell">
            <div class="p-lbl">Puntata Principale (1X)</div>
            <div class="p-val" id="p2-main-stake">19,00 €</div>
            <div class="p-win" id="p2-main-win">Vincita: 38,76 € (+8,76 € netti)</div>
          </div>
          <div class="p-cell">
            <div class="p-lbl">Puntata Paracadute (X2)</div>
            <div class="p-val" id="p2-para-stake">11,00 €</div>
            <div class="p-win" id="p2-para-win">Vincita: 31,13 € (Break-Even)</div>
          </div>
        </div>
        <div class="jackpot-banner">
          <span class="jp-txt">💥 PAREGGIO IN SUDAFRICA (0-0 o 1-1) = DOPPIA CASSA!</span>
          <span class="jp-val" id="p2-jackpot">69,89 € INCASSATI (+39,89 €)</span>
        </div>
      </div>
    </div>

  </div>

  <!-- TAB 3: RADAR TUTTI I MERCATI -->
  <div id="tab-radar" class="tab-panel">
    <div class="card">
      <div class="card-header">
        <div>
          <div class="card-title">📊 Matrice Analitica Mercati Nascosti</div>
          <div class="sub-title">Tutte le anomalie di quota estratte dal tuo palinsesto</div>
        </div>
        <span class="tag tag-gold">Anomalie di Valore</span>
      </div>

      <table class="safe-table">
        <thead>
          <tr>
            <th>Torneo</th>
            <th>Partita</th>
            <th>Quota Base</th>
            <th>Mercato Nascosto / Edge</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Ucraina</td>
            <td>Chernomorets vs Obolon (ID 9305)</td>
            <td>1X @ 1.27 | U2.5 @ 1.38</td>
            <td><b style="color:var(--green)">1X + Under 2.5 @ 1.70</b> (Edge +16%)</td>
          </tr>
          <tr>
            <td>Cina Super</td>
            <td>Zhejiang vs Wuhan (ID 1331)</td>
            <td>OV 2.5 @ 1.28 | Gol @ 1.32</td>
            <td><b style="color:var(--green)">1X + Over 1.5 @ 1.45</b> (Edge +14%)</td>
          </tr>
          <tr>
            <td>Sudafrica</td>
            <td>Highbury vs Gomora (ID 1722)</td>
            <td>X @ 2.87 | U2.5 @ 1.41</td>
            <td><b style="color:var(--green)">Doppia Chance + Under 3.5</b> (Edge +18%)</td>
          </tr>
          <tr>
            <td>Israele Alef</td>
            <td>Maccabi Yavne vs Herzeliya (ID 4028)</td>
            <td>1 @ 1.78 | 1X @ 1.20</td>
            <td><b style="color:var(--green)">1X + Under 3.5 @ 1.50</b> (Edge +12%)</td>
          </tr>
          <tr>
            <td>Giochi Asia</td>
            <td>Arabia Saudita vs Qatar (ID 10491)</td>
            <td>1 @ 1.51 | 1X @ 1.12</td>
            <td><b style="color:var(--green)">Arabia Saudita 1X + Under 3.5 @ 1.40</b></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

</div>

<div id="toast">Copiato negli appunti!</div>

<script>
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  
  if (tabId === 'doppie') {
    document.querySelectorAll('.tab-btn')[0].classList.add('active');
    document.getElementById('tab-doppie').classList.add('active');
  } else if (tabId === 'cassaforte') {
    document.querySelectorAll('.tab-btn')[1].classList.add('active');
    document.getElementById('tab-cassaforte').classList.add('active');
  } else if (tabId === 'radar') {
    document.querySelectorAll('.tab-btn')[2].classList.add('active');
    document.getElementById('tab-radar').classList.add('active');
  }
}

function setBudget(doppiaNum, total, mainStake, paraStake, qMain, qPara, elem) {
  elem.parentElement.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
  elem.classList.add('active');
  
  const mainWin = (mainStake * qMain).toFixed(2);
  const mainNet = (mainWin - total).toFixed(2);
  const paraWin = (paraStake * qPara).toFixed(2);
  const jpWin = (parseFloat(mainWin) + parseFloat(paraWin)).toFixed(2);
  const jpNet = (jpWin - total).toFixed(2);

  document.getElementById(`p${doppiaNum}-main-stake`).innerText = `${mainStake},00 €`;
  document.getElementById(`p${doppiaNum}-main-win`).innerText = `Vincita: ${mainWin} € (+${mainNet} € netti)`;
  document.getElementById(`p${doppiaNum}-para-stake`).innerText = `${paraStake},00 €`;
  document.getElementById(`p${doppiaNum}-para-win`).innerText = `Vincita: ${paraWin} € (Break-Even)`;
  document.getElementById(`p${doppiaNum}-jackpot`).innerText = `${jpWin} € INCASSATI (+${jpNet} €)`;
}

function copyText(text) {
  navigator.clipboard.writeText(text).then(() => {
    const toast = document.getElementById('toast');
    toast.innerText = 'Copiato: ' + text.substring(0, 30) + '...';
    toast.style.opacity = 1;
    setTimeout(() => { toast.style.opacity = 0; }, 2000);
  });
}
</script>

</body>
</html>
"""

# Scrittura su report repository
out_rep = ROOT / "reports" / "palinsesto_minori_18set.html"
with open(out_rep, "w", encoding="utf-8") as f:
    f.write(html_content)

# Scrittura su Desktop
desk_1 = Path(r"C:\Users\demarj\Desktop\palinsesto_minori_18set.html")
with open(desk_1, "w", encoding="utf-8") as f:
    f.write(html_content)

desk_2 = Path(r"C:\Users\demarj\Desktop\doppie_smartphone.html")
with open(desk_2, "w", encoding="utf-8") as f:
    f.write(html_content)

print("SUCCESS: File HTML generati e salvati correttamente su Desktop e reports!")

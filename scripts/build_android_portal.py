#!/usr/bin/env python3
"""
scripts/build_android_portal.py — Generatore dell'Interfaccia Mobile Web / PWA per Android.

Crea:
- C:/Project/BAgent/portal/android.html
- C:/Project/bagent-schedine/android.html

Caratteristiche:
- Mobile-first, ottimizzato per schermi Android (OLED dark theme #070d19)
- Bottom Navigation Bar in stile Material Design 3
- Supporto touch con feedback tattile (haptic vibration)
- Filtri veloci a scorrimento orizzontale (Tutte, Core, Tiri, Specials, UECL)
- Ricerca istantanea squadra / match
- Pulsante rapido "Copia per Telegram / WhatsApp / Bookmaker"
- Polling in tempo reale da schedine.json con fallback offline su boot JSON
"""

import sys
import json
from pathlib import Path
from datetime import datetime

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = Path("C:/Project/BAgent")
MIRROR = Path("C:/Project/bagent-schedine")
SCHEDINE_JSON = ROOT / "portal" / "schedine.json"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#070d19">
<meta name="color-scheme" content="dark">
<title>BAgent Mobile — Schedine Certificate</title>
<style>
  :root {
    --bg: #070d19;
    --surface: #0f172a;
    --surface-elevated: #1e293b;
    --border: #22324e;
    --border-subtle: #1e293b;
    --primary: #38bdf8;
    --primary-bg: rgba(56, 189, 248, 0.12);
    --success: #10b981;
    --success-bg: rgba(16, 185, 129, 0.14);
    --warning: #f59e0b;
    --warning-bg: rgba(245, 158, 11, 0.14);
    --danger: #f87171;
    --danger-bg: rgba(248, 113, 113, 0.14);
    --text-high: #f8fafc;
    --text-med: #94a3b8;
    --text-low: #64748b;
    --safe-top: env(safe-area-inset-top, 0px);
    --safe-bottom: env(safe-area-inset-bottom, 0px);
  }

  * { box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }
  
  body {
    background-color: var(--bg);
    color: var(--text-high);
    font-family: -apple-system, BlinkMacSystemFont, "Roboto", "Segoe UI", sans-serif;
    min-height: 100dvh;
    padding-top: calc(var(--safe-top) + 64px);
    padding-bottom: calc(var(--safe-bottom) + 80px);
    overflow-x: hidden;
    user-select: none;
    -webkit-font-smoothing: antialiased;
  }

  /* TOP APP BAR */
  .top-bar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    height: calc(var(--safe-top) + 64px);
    padding-top: var(--safe-top);
    background: rgba(7, 13, 25, 0.92);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-left: 16px;
    padding-right: 16px;
    z-index: 1000;
  }
  
  .brand-group {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .brand-title {
    font-size: 19px;
    font-weight: 900;
    letter-spacing: 0.04em;
    color: var(--text-high);
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .brand-title span { color: var(--primary); }
  .badge-live {
    font-size: 10px;
    font-weight: 800;
    padding: 2px 7px;
    border-radius: 999px;
    background: var(--success-bg);
    color: var(--success);
    border: 1px solid rgba(16, 185, 129, 0.3);
    letter-spacing: 0.05em;
  }

  .top-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .profit-chip {
    background: var(--surface);
    border: 1px solid var(--border);
    padding: 6px 12px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: 800;
    color: var(--success);
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    line-height: 1.1;
  }
  .profit-chip small {
    font-size: 9px;
    font-weight: 600;
    color: var(--text-med);
  }
  
  .btn-icon {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-high);
    width: 38px;
    height: 38px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: transform 0.15s ease, background 0.15s;
  }
  .btn-icon:active { transform: scale(0.92); background: var(--surface-elevated); }

  /* SEARCH & QUICK FILTERS */
  .sub-header {
    padding: 12px 16px 8px;
  }
  .search-box {
    position: relative;
    margin-bottom: 12px;
  }
  .search-input {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 14px;
    padding: 12px 16px 12px 40px;
    color: var(--text-high);
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
  }
  .search-input:focus { border-color: var(--primary); }
  .search-input::placeholder { color: var(--text-low); }
  .search-icon {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    width: 16px;
    height: 16px;
    color: var(--text-low);
  }

  .filter-scroll {
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding-bottom: 4px;
    scrollbar-width: none;
  }
  .filter-scroll::-webkit-scrollbar { display: none; }
  
  .filter-pill {
    white-space: nowrap;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-med);
    padding: 7px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    transition: all 0.15s ease;
  }
  .filter-pill.active {
    background: var(--primary);
    color: #070d19;
    border-color: var(--primary);
  }

  /* LIST & TICKETS CONTAINER */
  .container {
    padding: 4px 16px 16px;
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  /* TICKET CARD */
  .ticket-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 18px;
    overflow: hidden;
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    transition: transform 0.15s ease, border-color 0.15s;
  }
  .ticket-card:active { transform: scale(0.99); }
  
  .card-header {
    padding: 14px 16px;
    background: linear-gradient(180deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.4) 100%);
    border-bottom: 1px solid var(--border-subtle);
  }
  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 8px;
    margin-bottom: 8px;
  }
  .card-title {
    font-size: 15px;
    font-weight: 800;
    color: var(--text-high);
    line-height: 1.3;
  }
  .odds-badge {
    background: var(--primary-bg);
    color: var(--primary);
    border: 1px solid rgba(56, 189, 248, 0.35);
    font-size: 16px;
    font-weight: 900;
    padding: 4px 10px;
    border-radius: 10px;
    white-space: nowrap;
  }

  .card-metrics {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: var(--text-med);
    margin-top: 4px;
  }
  .metric-item b { color: var(--text-high); font-weight: 700; }
  .metric-pot b { color: var(--success); font-weight: 800; }

  /* LEGS */
  .card-legs {
    display: flex;
    flex-direction: column;
  }
  .leg-row {
    padding: 12px 16px;
    border-bottom: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .leg-row:last-child { border-bottom: none; }
  
  .leg-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 11px;
    color: var(--text-low);
    font-weight: 600;
  }
  .leg-match {
    font-size: 14px;
    font-weight: 800;
    color: var(--text-high);
  }
  .leg-pick-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 8px;
  }
  .pick-pill {
    background: rgba(56, 189, 248, 0.08);
    border: 1px solid rgba(56, 189, 248, 0.25);
    color: var(--primary);
    font-size: 13px;
    font-weight: 800;
    padding: 4px 10px;
    border-radius: 8px;
    flex: 1;
  }
  .odd-pill {
    font-size: 13px;
    font-weight: 800;
    color: var(--text-high);
    padding: 4px 8px;
    background: var(--surface-elevated);
    border-radius: 8px;
    border: 1px solid var(--border);
  }
  .leg-notes {
    font-size: 11px;
    color: var(--text-med);
    line-height: 1.35;
  }
  
  .leg-status {
    font-size: 10px;
    font-weight: 800;
    padding: 2px 6px;
    border-radius: 6px;
    text-transform: uppercase;
  }
  .status-pending { background: var(--warning-bg); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.3); }
  .status-won { background: var(--success-bg); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.3); }
  .status-lost { background: var(--danger-bg); color: var(--danger); border: 1px solid rgba(248, 113, 113, 0.3); }

  /* CARD ACTIONS */
  .card-footer {
    padding: 10px 16px;
    background: rgba(15, 23, 42, 0.7);
    border-top: 1px solid var(--border-subtle);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .btn-share {
    background: var(--surface-elevated);
    border: 1px solid var(--border);
    color: var(--text-high);
    font-size: 12px;
    font-weight: 700;
    padding: 8px 14px;
    border-radius: 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .btn-share:active { transform: scale(0.95); }

  /* BOTTOM NAVIGATION BAR (MATERIAL 3) */
  .bottom-nav {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: calc(var(--safe-bottom) + 64px);
    padding-bottom: var(--safe-bottom);
    background: rgba(7, 13, 25, 0.94);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-around;
    align-items: center;
    z-index: 1000;
  }
  .nav-item {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 3px;
    height: 100%;
    color: var(--text-low);
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
    transition: color 0.15s;
    position: relative;
  }
  .nav-item.active {
    color: var(--primary);
  }
  .nav-item svg {
    width: 20px;
    height: 20px;
    fill: currentColor;
  }
  .nav-badge {
    position: absolute;
    top: 8px;
    right: calc(50% - 18px);
    background: var(--primary);
    color: #070d19;
    font-size: 9px;
    font-weight: 900;
    padding: 1px 5px;
    border-radius: 999px;
  }

  /* TOAST NOTIFICATION */
  .toast {
    position: fixed;
    bottom: calc(var(--safe-bottom) + 76px);
    left: 50%;
    transform: translateX(-50%) translateY(20px);
    background: #1e293b;
    color: #f8fafc;
    border: 1px solid var(--primary);
    padding: 10px 18px;
    border-radius: 14px;
    font-size: 13px;
    font-weight: 700;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    opacity: 0;
    pointer-events: none;
    transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 2000;
  }
  .toast.show {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }

  /* EMPTY STATE */
  .empty-state {
    text-align: center;
    padding: 48px 16px;
    color: var(--text-med);
  }
  .empty-state h3 { font-size: 16px; color: var(--text-high); margin-bottom: 6px; }

  /* SPIN ANIMATION */
  .spin { animation: spin 0.8s linear infinite; }
  @keyframes spin { 100% { transform: rotate(360deg); } }
</style>
</head>
<body>

<!-- TOP APP BAR -->
<header class="top-bar">
  <div class="brand-group">
    <div class="brand-title">BAG<span>ENT</span></div>
    <div class="badge-live">LIVE 2026/27</div>
  </div>
  <div class="top-actions">
    <div class="profit-chip">
      <span id="profit-val">+45.14 €</span>
      <small>Saldo Chiuso</small>
    </div>
    <a href="schedine.html" class="btn-icon" title="Vista Desktop" style="text-decoration:none;">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
        <line x1="8" y1="21" x2="16" y2="21"/>
        <line x1="12" y1="17" x2="12" y2="21"/>
      </svg>
    </a>
    <button class="btn-icon" id="btn-refresh" title="Aggiorna">
      <svg id="refresh-svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"/>
      </svg>
    </button>
  </div>
</header>

<!-- SEARCH & QUICK CATEGORY FILTERS -->
<div class="sub-header">
  <div class="search-box">
    <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
    <input type="text" class="search-input" id="search-input" placeholder="Cerca squadra, mercato o coppa...">
  </div>
  <div class="filter-scroll" id="category-filters">
    <button class="filter-pill active" data-cat="all">Tutte (<span id="count-all">0</span>)</button>
    <button class="filter-pill" data-cat="core">Core Blindato</button>
    <button class="filter-pill" data-cat="tiri">Tiri & Corner</button>
    <button class="filter-pill" data-cat="uecl">Conference League</button>
    <button class="filter-pill" data-cat="satellite">Satellite Flussi</button>
  </div>
</div>

<!-- MAIN TICKETS LIST -->
<main class="container" id="tickets-container">
  <!-- Rendered dynamically -->
</main>

<!-- BOTTOM NAVIGATION -->
<nav class="bottom-nav">
  <div class="nav-item active" data-tab="present">
    <svg viewBox="0 0 24 24"><path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
    <span>In Corso</span>
    <span class="nav-badge" id="badge-present">0</span>
  </div>
  <div class="nav-item" data-tab="future">
    <svg viewBox="0 0 24 24"><path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg>
    <span>Future</span>
  </div>
  <div class="nav-item" data-tab="past">
    <svg viewBox="0 0 24 24"><path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>
    <span>Archivio</span>
  </div>
</nav>

<!-- TOAST -->
<div class="toast" id="toast">Copiato negli appunti!</div>

<!-- EMBEDDED BOOT DATA (OFFLINE & INSTANT FIRST RENDER) -->
<script type="application/json" id="boot">
__BOOT_JSON__
</script>

<script>
  let DB = null;
  let currentTab = 'present';
  let currentCat = 'all';
  let searchQuery = '';

  function haptic() {
    if (navigator.vibrate) navigator.vibrate(10);
  }

  function showToast(text) {
    const t = document.getElementById('toast');
    t.innerText = text;
    t.classList.add('show');
    setTimeout(() => t.classList.remove('show'), 2200);
  }

  function parseBoot() {
    const el = document.getElementById('boot');
    if (el) {
      try {
        DB = JSON.parse(el.textContent);
      } catch (e) {
        console.error("Boot JSON parse error:", e);
      }
    }
  }

  async function fetchLive() {
    const icon = document.getElementById('refresh-svg');
    icon.classList.add('spin');
    try {
      const res = await fetch('schedine.json?t=' + Date.now());
      if (res.ok) {
        DB = await res.json();
        showToast("Dati aggiornati!");
      }
    } catch (e) {
      console.log("Offline mode, using cached boot data");
    } finally {
      setTimeout(() => icon.classList.remove('spin'), 400);
      render();
    }
  }

  function filterTicket(t) {
    const title = (t.title || '').toLowerCase();
    const legs = t.legs || [];
    
    // Category filter
    if (currentCat === 'core') {
      if (!title.includes('core')) return false;
    } else if (currentCat === 'tiri') {
      if (!title.includes('chirurgica') && !title.includes('balistica') && !title.includes('tiri') && !title.includes('corner')) return false;
    } else if (currentCat === 'uecl') {
      if (!title.includes('uecl') && !title.includes('conference')) return false;
    } else if (currentCat === 'satellite') {
      if (!title.includes('satellite') && !title.includes('specials')) return false;
    }

    // Search query filter
    if (searchQuery.trim() !== '') {
      const q = searchQuery.toLowerCase();
      const matchInTitle = title.includes(q);
      const matchInLegs = legs.some(l => 
        (l.match || '').toLowerCase().includes(q) ||
        (l.pick || '').toLowerCase().includes(q) ||
        (l.score || '').toLowerCase().includes(q)
      );
      if (!matchInTitle && !matchInLegs) return false;
    }

    return true;
  }

  function copyTicket(t) {
    haptic();
    let text = `${t.title}\n`;
    text += `Quota Totale: ${t.odds || ''} | Stake: ${t.stake || ''} | Vincita Pot: ${t.potential_win || ''}\n\n`;
    (t.legs || []).forEach((l, idx) => {
      text += `${idx + 1}) ${l.match} (${l.when || ''})\n   👉 Giocata: ${l.pick} @ ${l.odd}\n`;
    });
    text += `\nCertificato BAgent Reality Gate 2026/27`;

    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        showToast("Schedina copiata!");
      });
    } else {
      showToast("Condivisione non supportata");
    }
  }

  function render() {
    if (!DB) return;

    // Header profit
    const pEl = document.getElementById('profit-val');
    if (pEl && DB.profit_label) {
      pEl.innerText = DB.profit_label.split('(')[0].trim();
    }

    // Badge present count
    const presentList = DB.present || [];
    document.getElementById('badge-present').innerText = presentList.length;
    document.getElementById('count-all').innerText = presentList.length;

    // Select target list
    let list = DB[currentTab] || [];
    list = list.filter(filterTicket);

    const container = document.getElementById('tickets-container');
    container.innerHTML = '';

    if (list.length === 0) {
      container.innerHTML = `
        <div class="empty-state">
          <h3>Nessuna schedina trovata</h3>
          <p>Nessun ticket corrisponde ai filtri selezionati.</p>
        </div>
      `;
      return;
    }

    list.forEach(t => {
      const card = document.createElement('div');
      card.className = 'ticket-card';

      let legsHtml = '';
      (t.legs || []).forEach(l => {
        let statusClass = 'status-pending';
        let statusLabel = 'In Attesa';
        if (l.result === 'WON') { statusClass = 'status-won'; statusLabel = 'Vinta'; }
        else if (l.result === 'LOST') { statusClass = 'status-lost'; statusLabel = 'Persa'; }

        legsHtml += `
          <div class="leg-row">
            <div class="leg-top">
              <span>${l.when || 'Oggi'}</span>
              <span class="leg-status ${statusClass}">${statusLabel}</span>
            </div>
            <div class="leg-match">${l.match}</div>
            <div class="leg-pick-row">
              <div class="pick-pill">${l.pick}</div>
              <div class="odd-pill">@ ${l.odd}</div>
            </div>
            <div class="leg-notes">${l.score || ''}</div>
          </div>
        `;
      });

      card.innerHTML = `
        <div class="card-header">
          <div class="card-top">
            <div class="card-title">${t.title}</div>
            <div class="odds-badge">${t.odds || ''}</div>
          </div>
          <div class="card-metrics">
            <span class="metric-item">Stake: <b>${t.stake || ''}</b></span>
            <span class="metric-pot">Vincita: <b>${t.potential_win || ''}</b></span>
          </div>
        </div>
        <div class="card-legs">
          ${legsHtml}
        </div>
        <div class="card-footer">
          <span style="font-size:11px;color:var(--text-low);">${t.label || ''}</span>
          <button class="btn-share" data-id="${t.id}">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><rect x="8" y="2" width="8" height="4" rx="1" ry="1"/></svg>
            Copia
          </button>
        </div>
      `;

      card.querySelector('.btn-share').addEventListener('click', (e) => {
        e.stopPropagation();
        copyTicket(t);
      });

      container.appendChild(card);
    });
  }

  // Event Listeners
  document.addEventListener('DOMContentLoaded', () => {
    parseBoot();
    render();

    // Refresh button
    document.getElementById('btn-refresh').addEventListener('click', () => {
      haptic();
      fetchLive();
    });

    // Search input
    document.getElementById('search-input').addEventListener('input', (e) => {
      searchQuery = e.target.value;
      render();
    });

    // Category pills
    document.querySelectorAll('.filter-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        haptic();
        document.querySelectorAll('.filter-pill').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentCat = btn.getAttribute('data-cat');
        render();
      });
    });

    // Bottom nav tabs
    document.querySelectorAll('.nav-item').forEach(item => {
      item.addEventListener('click', () => {
        haptic();
        document.querySelectorAll('.nav-item').forEach(i => i.classList.remove('active'));
        item.classList.add('active');
        currentTab = item.getAttribute('data-tab');
        render();
      });
    });

    // Auto-refresh every 25 seconds if online
    setInterval(() => {
      if (document.visibilityState === 'visible') {
        fetchLive();
      }
    }, 25000);
  });
</script>
</body>
</html>
"""


def build():
    if not SCHEDINE_JSON.exists():
        print(f"File non trovato: {SCHEDINE_JSON}")
        return

    raw_json = SCHEDINE_JSON.read_text(encoding="utf-8")
    compact_json = json.dumps(json.loads(raw_json), ensure_ascii=False)

    html_content = HTML_TEMPLATE.replace("__BOOT_JSON__", compact_json)

    # 1. Scrivi su portal/android.html
    target_portal = ROOT / "portal" / "android.html"
    target_portal.write_text(html_content, encoding="utf-8")
    print(f"Generato con successo: {target_portal}")

    # 2. Scrivi su bagent-schedine/android.html
    if MIRROR.exists():
        target_mirror = MIRROR / "android.html"
        target_mirror.write_text(html_content, encoding="utf-8")
        print(f"Generato con successo (mirror GitHub Pages): {target_mirror}")


if __name__ == "__main__":
    build()

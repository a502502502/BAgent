#!/usr/bin/env python3
"""Scheda statistiche: scarica lo storico da bagent.db e scrive una pagina di lettura.

Non è una schedina. Non legge quote e non propone una selezione.
Ogni mercato in pagina esiste solo se la statistica corrispondente è nel database.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "bagent.db"
OUT_PATH = ROOT / "portal" / "demo_scheda_statistiche.html"

GAPS = [
    {
        "market": "Over 0.5 primo tempo",
        "stat": "Gol del primo tempo",
        "why": "home_goals_ht vuoto su tutte le righe Serie A",
    },
    {
        "market": "Under 1.5 primo tempo",
        "stat": "Gol del primo tempo",
        "why": "home_goals_ht vuoto su tutte le righe Serie A",
    },
    {
        "market": "Over 3.5 tiri in porta",
        "stat": "Tiri in porta",
        "why": "home_shots_on_target vuoto su tutte le righe Serie A",
    },
    {
        "market": "Over 3.5 cartellini",
        "stat": "Ammonizioni",
        "why": "home_yellow_cards vuoto su tutte le righe Serie A",
    },
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA wal_checkpoint")
    return conn


def fingerprint(row: sqlite3.Row) -> tuple:
    return (
        row["home_team"],
        row["away_team"],
        row["home_goals"],
        row["away_goals"],
        row["home_shots"],
        row["away_shots"],
        row["home_corners"],
        row["away_corners"],
        round(row["home_xg"], 2),
        round(row["away_xg"], 2),
    )


def load_teams(conn: sqlite3.Connection, league: str) -> dict:
    names = [
        r[0]
        for r in conn.execute(
            """
            SELECT home_team FROM matches
            WHERE league=? AND home_shots>0 AND away_shots>0
              AND home_corners>=0 AND home_xg IS NOT NULL AND away_xg IS NOT NULL
              AND home_goals IS NOT NULL AND away_goals IS NOT NULL
            UNION
            SELECT away_team FROM matches
            WHERE league=? AND home_shots>0 AND away_shots>0
              AND home_corners>=0 AND home_xg IS NOT NULL AND away_xg IS NOT NULL
              AND home_goals IS NOT NULL AND away_goals IS NOT NULL
            """,
            (league, league),
        )
    ]
    teams = {}
    for name in sorted(names, key=str.lower):
        rows = conn.execute(
            """
            SELECT id, date_gmt, home_team, away_team,
                   home_goals, away_goals, home_shots, away_shots,
                   home_corners, away_corners, home_xg, away_xg
            FROM matches
            WHERE league=? AND (home_team=? OR away_team=?)
              AND home_shots>0 AND away_shots>0
              AND home_corners>=0 AND home_xg IS NOT NULL AND away_xg IS NOT NULL
              AND home_goals IS NOT NULL AND away_goals IS NOT NULL
            ORDER BY id DESC
            """,
            (league, name, name),
        ).fetchall()
        kept = []
        seen = set()
        for row in rows:
            key = fingerprint(row)
            if key in seen:
                continue
            seen.add(key)
            is_home = row["home_team"] == name
            kept.append(
                {
                    "id": row["id"],
                    "date": row["date_gmt"],
                    "venue": "Casa" if is_home else "Trasferta",
                    "opponent": row["away_team"] if is_home else row["home_team"],
                    "home": row["home_team"],
                    "away": row["away_team"],
                    "hg": row["home_goals"],
                    "ag": row["away_goals"],
                    "hs": row["home_shots"],
                    "as": row["away_shots"],
                    "hc": row["home_corners"],
                    "ac": row["away_corners"],
                    "hx": round(row["home_xg"], 2),
                    "ax": round(row["away_xg"], 2),
                    "gf": row["home_goals"] if is_home else row["away_goals"],
                    "ga": row["away_goals"] if is_home else row["home_goals"],
                    "sf": row["home_shots"] if is_home else row["away_shots"],
                    "sa": row["away_shots"] if is_home else row["home_shots"],
                    "cf": row["home_corners"] if is_home else row["away_corners"],
                    "ca": row["away_corners"] if is_home else row["home_corners"],
                    "xf": round(row["home_xg"] if is_home else row["away_xg"], 2),
                    "xa": round(row["away_xg"] if is_home else row["home_xg"], 2),
                }
            )
        if len(kept) < 4:
            continue
        teams[name] = {"raw_rows": len(rows), "matches": kept}
    return teams


def build_html(payload: dict) -> str:
    data = json.dumps(payload, ensure_ascii=False).replace("<", "\\u003c")
    return TEMPLATE.replace("__PAYLOAD__", data)


TEMPLATE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BAgent — Scheda statistiche</title>
<style>
  :root {
    --bg: #0c1118;
    --card: #141b26;
    --card-2: #1a2331;
    --line: #2a3648;
    --text: #e7edf4;
    --muted: #8e9bb0;
    --home: #4c8dff;
    --away: #e0a045;
    --off: #6a7688;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font: 14px/1.45 "Segoe UI", system-ui, sans-serif;
  }
  button, select { font: inherit; color: inherit; }
  button { cursor: pointer; }
  .wrap { max-width: 980px; margin: 0 auto; padding: 22px 16px 48px; }
  .brand {
    display: flex; justify-content: space-between; gap: 12px; align-items: baseline;
    color: var(--muted); font-size: 12px; letter-spacing: .04em; text-transform: uppercase;
  }
  h1 { font-size: 22px; font-weight: 650; margin: 6px 0 4px; letter-spacing: -0.02em; }
  .lede { color: var(--muted); max-width: 68ch; margin: 0 0 18px; }
  .card {
    background: var(--card);
    border: 1px solid var(--line);
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 14px;
  }
  .head {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 14px;
    align-items: center;
  }
  .side { min-width: 0; }
  .side.home { text-align: right; }
  .side-label { color: var(--muted); font-size: 11px; letter-spacing: .06em; text-transform: uppercase; }
  .side.home .side-label { color: var(--home); }
  .side.away .side-label { color: var(--away); }
  select.team {
    width: 100%;
    max-width: 280px;
    background: transparent;
    border: none;
    font-size: 20px;
    font-weight: 650;
    padding: 2px 0;
  }
  .side.home select.team { text-align: right; }
  .sample { color: var(--muted); font-size: 12px; margin-top: 2px; }
  .form { margin-top: 8px; display: flex; gap: 4px; flex-wrap: wrap; }
  .side.home .form { justify-content: flex-end; }
  .pill {
    min-width: 22px; text-align: center;
    border: 1px solid var(--line); border-radius: 6px;
    font-size: 12px; padding: 2px 5px; color: var(--muted);
  }
  .vs { color: var(--muted); font-size: 12px; letter-spacing: .12em; text-align: center; }
  .stat {
    display: grid;
    grid-template-columns: 72px 1fr 72px;
    gap: 10px;
    align-items: center;
    width: 100%;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 7px 6px;
    text-align: left;
  }
  .stat.on { background: var(--card-2); border-color: var(--line); }
  .stat .num { font-variant-numeric: tabular-nums; font-weight: 650; font-size: 15px; }
  .stat .num.right { text-align: right; }
  .stat .num.left { text-align: left; color: var(--away); }
  .stat .num.right { color: var(--home); }
  .side-note { display: block; color: var(--muted); font-size: 11px; font-weight: 500; }
  .barname { color: var(--muted); font-size: 12px; margin-bottom: 4px; display: flex; justify-content: space-between; }
  .bar { display: grid; grid-template-columns: 1fr 1fr; gap: 3px; height: 8px; }
  .half { background: #101722; border-radius: 4px; overflow: hidden; display: flex; }
  .half.home { justify-content: flex-end; }
  .half > i { display: block; height: 100%; }
  .half.home > i { background: var(--home); }
  .half.away > i { background: var(--away); }
  .chips { display: flex; flex-wrap: wrap; gap: 6px; margin: 2px 0 12px; }
  .chip, .textbtn, .segno {
    background: transparent;
    border: 1px solid var(--line);
    border-radius: 999px;
    padding: 5px 10px;
    color: var(--muted);
  }
  .chip.on { color: var(--text); background: var(--card-2); }
  .textbtn { border-radius: 8px; }
  .group { padding-top: 8px; margin-top: 8px; border-top: 1px solid var(--line); }
  .group h2 { font-size: 15px; margin: 8px 0 2px; font-weight: 650; }
  .blurb { color: var(--muted); font-size: 12px; margin: 0 0 8px; }
  .series-block { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 6px; }
  .series-block .who { font-size: 12px; font-weight: 650; }
  .series-block .who.home { color: var(--home); }
  .series-block .who.away { color: var(--away); }
  .series { font-variant-numeric: tabular-nums; color: var(--text); font-size: 13px; }
  .market {
    display: grid;
    grid-template-columns: minmax(140px, 190px) 1fr 1fr;
    gap: 10px;
    align-items: start;
    padding: 10px 0;
    border-top: 1px solid #223044;
  }
  .market .label { font-weight: 650; }
  .market .tied { color: var(--muted); font-size: 12px; }
  .rate { font-variant-numeric: tabular-nums; font-weight: 650; }
  .cell .series { color: var(--muted); font-size: 12px; margin: 2px 0 6px; }
  .segno.on { color: var(--text); background: #1c3148; border-color: #3d628c; }
  .log {
    max-height: 280px; overflow: auto;
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  }
  .log h3 { margin: 0 0 8px; font-size: 13px; }
  .log h3.home { color: var(--home); }
  .log h3.away { color: var(--away); }
  .game { padding: 7px 0; border-top: 1px solid #223044; }
  .game b { font-weight: 650; }
  .game .meta { color: var(--muted); font-size: 12px; }
  .gaps { display: grid; gap: 6px; }
  .gap {
    display: grid; grid-template-columns: 1.2fr 1fr 1.4fr; gap: 8px;
    color: var(--off); font-size: 13px; padding: 6px 0; border-top: 1px solid #223044;
  }
  .dock .pick {
    display: flex; justify-content: space-between; gap: 10px; align-items: baseline;
    padding: 8px 0; border-top: 1px solid #223044;
  }
  .dock .pick span { color: var(--muted); font-size: 12px; }
  .empty { color: var(--muted); margin: 4px 0 0; }
  .src { color: var(--muted); font-size: 12px; }
  @media (max-width: 720px) {
    .head, .series-block, .market, .log, .gap { grid-template-columns: 1fr; }
    .side.home, .side.home select.team, .side.home .form { text-align: left; justify-content: flex-start; }
    .stat { grid-template-columns: 64px 1fr 64px; }
    select.team { max-width: none; }
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="brand"><span>BAgent · scheda statistiche</span><span>Demo di lettura</span></div>
  <h1>Statistica a sinistra, mercato a destra</h1>
  <p class="lede">Scarico dallo storico locale. Ogni mercato acceso usa una colonna presente nel database. La frequenza è il conteggio sulle partite di quella squadra. La scelta la segni tu, in fondo alla pagina.</p>
  <div id="board"></div>
  <p class="src" id="source"></p>
</div>
<script id="payload" type="application/json">__PAYLOAD__</script>
<script>
const DATA = JSON.parse(document.getElementById("payload").textContent);

const GROUPS = [
  {id:"gol", title:"Gol della partita", kind:"total", blurb:"Gol totali in ciascuna delle partite già giocate dalla squadra. Le due colonne sono due campioni separati."},
  {id:"squadra", title:"Gol della squadra", kind:"gf", blurb:"Gol fatti da quella squadra. Sotto, la riga dei gol subiti alimenta porta inviolata e gol subito."},
  {id:"esito", title:"Esito sul tabellino", kind:"result", blurb:"Vittorie, pareggi e sconfitte nelle partite già giocate. È il conteggio del risultato, riga per riga."},
  {id:"tiri", title:"Tiri", kind:"sf", blurb:"Tiri della squadra. La seconda serie è i tiri concessi."},
  {id:"corner", title:"Corner", kind:"cf", blurb:"Corner della squadra. La seconda serie è i corner concessi."}
];

const STATS = [
  {key:"xf", label:"xG prodotti", digits:2, focus:"gol", hint:"contesto dei gol"},
  {key:"xa", label:"xG concessi", digits:2, focus:"gol", hint:"contesto dei gol"},
  {key:"gf", label:"Gol fatti", digits:2, focus:"squadra", hint:"gol squadra"},
  {key:"ga", label:"Gol subiti", digits:2, focus:"squadra", hint:"gol subiti"},
  {key:"total", label:"Gol a partita", digits:2, focus:"gol", hint:"gol della partita"},
  {key:"sf", label:"Tiri", digits:1, focus:"tiri", hint:"tiri"},
  {key:"sa", label:"Tiri concessi", digits:1, focus:"tiri", hint:"tiri concessi"},
  {key:"cf", label:"Corner", digits:1, focus:"corner", hint:"corner"},
  {key:"ca", label:"Corner concessi", digits:1, focus:"corner", hint:"corner concessi"}
];

const MARKETS = [
  {id:"over15", group:"gol", scope:"match", label:"Over 1.5", stat:"Gol totali", test:m => m.gf + m.ga >= 2},
  {id:"under25", group:"gol", scope:"match", label:"Under 2.5", stat:"Gol totali", test:m => m.gf + m.ga <= 2},
  {id:"over25", group:"gol", scope:"match", label:"Over 2.5", stat:"Gol totali", test:m => m.gf + m.ga >= 3},
  {id:"under35", group:"gol", scope:"match", label:"Under 3.5", stat:"Gol totali", test:m => m.gf + m.ga <= 3},
  {id:"mg15", group:"gol", scope:"match", label:"MultiGol 1-5", stat:"Gol totali", test:m => { const t = m.gf + m.ga; return t >= 1 && t <= 5; }},
  {id:"mg25", group:"gol", scope:"match", label:"MultiGol 2-5", stat:"Gol totali", test:m => { const t = m.gf + m.ga; return t >= 2 && t <= 5; }},
  {id:"btts", group:"gol", scope:"match", label:"Gol entrambe", stat:"Entrambe segnano", test:m => m.gf > 0 && m.ga > 0},
  {id:"score", group:"squadra", scope:"team", label:"Segna almeno 1", stat:"Gol fatti", test:m => m.gf >= 1},
  {id:"mg13", group:"squadra", scope:"team", label:"MultiGol 1-3 squadra", stat:"Gol fatti", test:m => m.gf >= 1 && m.gf <= 3},
  {id:"mg24", group:"squadra", scope:"team", label:"MultiGol 2-4 squadra", stat:"Gol fatti", test:m => m.gf >= 2 && m.gf <= 4},
  {id:"cs", group:"squadra", scope:"team", label:"Porta inviolata", stat:"Gol subiti", test:m => m.ga === 0},
  {id:"conceded", group:"squadra", scope:"team", label:"Subisce almeno 1", stat:"Gol subiti", test:m => m.ga >= 1},
  {id:"win", group:"esito", scope:"team", label:"Vittoria", stat:"Risultato", test:m => m.gf > m.ga},
  {id:"draw", group:"esito", scope:"team", label:"Pareggio", stat:"Risultato", test:m => m.gf === m.ga},
  {id:"loss", group:"esito", scope:"team", label:"Sconfitta", stat:"Risultato", test:m => m.gf < m.ga},
  {id:"unbeaten", group:"esito", scope:"team", label:"Imbattuta", stat:"Risultato", test:m => m.gf >= m.ga},
  {id:"sh95", group:"tiri", scope:"team", label:"Over 9.5 tiri", stat:"Tiri", test:m => m.sf >= 10},
  {id:"sh125", group:"tiri", scope:"team", label:"Over 12.5 tiri", stat:"Tiri", test:m => m.sf >= 13},
  {id:"sh145", group:"tiri", scope:"team", label:"Over 14.5 tiri", stat:"Tiri", test:m => m.sf >= 15},
  {id:"sh165", group:"tiri", scope:"team", label:"Over 16.5 tiri", stat:"Tiri", test:m => m.sf >= 17},
  {id:"sh195", group:"tiri", scope:"team", label:"Over 19.5 tiri", stat:"Tiri", test:m => m.sf >= 20},
  {id:"sa95", group:"tiri", scope:"team", label:"Over 9.5 tiri concessi", stat:"Tiri concessi", test:m => m.sa >= 10},
  {id:"c35", group:"corner", scope:"team", label:"Over 3.5 corner", stat:"Corner", test:m => m.cf >= 4},
  {id:"c45", group:"corner", scope:"team", label:"Over 4.5 corner", stat:"Corner", test:m => m.cf >= 5},
  {id:"c65", group:"corner", scope:"team", label:"Over 6.5 corner", stat:"Corner", test:m => m.cf >= 7},
  {id:"c85", group:"corner", scope:"team", label:"Over 8.5 corner", stat:"Corner", test:m => m.cf >= 9},
  {id:"c95", group:"corner", scope:"team", label:"Over 9.5 corner", stat:"Corner", test:m => m.cf >= 10},
  {id:"ca35", group:"corner", scope:"team", label:"Over 3.5 corner concessi", stat:"Corner concessi", test:m => m.ca >= 4}
];

const state = {
  home: DATA.defaultHome,
  away: DATA.defaultAway,
  focus: null,
  group: "all",
  picks: loadPicks()
};

function loadPicks() {
  try { return JSON.parse(localStorage.getItem("bagent.statBoard.picks.v1")) || []; }
  catch (e) { return []; }
}
function savePicks() {
  localStorage.setItem("bagent.statBoard.picks.v1", JSON.stringify(state.picks));
}
function esc(value) {
  return String(value).replace(/[&<>"']/g, ch => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[ch]);
}
function matches(name) { return DATA.teams[name].matches; }
function values(name, kind) {
  const ms = matches(name);
  if (kind === "total") return ms.map(m => m.gf + m.ga);
  if (kind === "result") return ms.map(m => m.gf > m.ga ? "V" : m.gf === m.ga ? "P" : "S");
  return ms.map(m => m[kind]);
}
function average(nums) {
  return nums.reduce((a, b) => a + b, 0) / nums.length;
}
function fmt(n, digits) {
  return Number(n).toFixed(digits);
}
function count(name, market) {
  const ms = matches(name);
  return { n: ms.filter(market.test).length, d: ms.length };
}
function seriesText(name, market) {
  if (market.group === "esito") return values(name, "result").join(" ");
  if (market.stat === "Gol totali" || market.stat === "Entrambe segnano") {
    return values(name, "total").join(" ");
  }
  if (market.stat === "Gol fatti") return values(name, "gf").join(" ");
  if (market.stat === "Gol subiti") return values(name, "ga").join(" ");
  if (market.stat === "Tiri") return values(name, "sf").join(" ");
  if (market.stat === "Tiri concessi") return values(name, "sa").join(" ");
  if (market.stat === "Corner") return values(name, "cf").join(" ");
  if (market.stat === "Corner concessi") return values(name, "ca").join(" ");
  return "";
}
function sampleLine(name) {
  const t = DATA.teams[name];
  const n = t.matches.length;
  if (t.raw_rows === n) return n + " partite distinte";
  return n + " partite distinte, da " + t.raw_rows + " righe";
}
function pickKey(market, side) {
  return [state.home, state.away, market.id, side].join("|");
}
function hasPick(market, side) {
  const key = pickKey(market, side);
  return state.picks.some(p => p.key === key);
}
function formPills(name) {
  return values(name, "result").map(letter => `<i class="pill">${letter}</i>`).join("");
}
function statButton(stat) {
  const left = stat.key === "result" ? "" : average(values(state.home, stat.key));
  const right = stat.key === "result" ? "" : average(values(state.away, stat.key));
  const max = Math.max(left, right, 0.001);
  const on = state.focus === stat.focus && state.focusStat === stat.key ? " on" : "";
  return `<button type="button" class="stat${on}" data-stat="${stat.key}" data-focus="${stat.focus}">
    <span class="num right">${fmt(left, stat.digits)}</span>
    <span>
      <span class="barname"><span>${stat.label}</span><span>${stat.hint}</span></span>
      <span class="bar">
        <span class="half home"><i style="width:${(left / max) * 100}%"></i></span>
        <span class="half away"><i style="width:${(right / max) * 100}%"></i></span>
      </span>
    </span>
    <span class="num left">${fmt(right, stat.digits)}</span>
  </button>`;
}
function cell(name, market) {
  const c = count(name, market);
  const side = name;
  const on = hasPick(market, side) ? " on" : "";
  const button = market.scope === "team"
    ? `<button type="button" class="segno${on}" data-segno="${market.id}" data-side="${esc(side)}">${on ? "Segnata" : "Segno"} ${esc(side)}</button>`
    : "";
  return `<div class="cell">
    <div class="rate">${c.n} volte su ${c.d}</div>
    <div class="series">${seriesText(name, market)}</div>
    ${button}
  </div>`;
}
function marketRow(market) {
  const on = market.scope === "match" && hasPick(market, "partita") ? " on" : "";
  const matchBtn = market.scope === "match"
    ? `<button type="button" class="segno${on}" data-segno="${market.id}" data-side="partita">${on ? "Segnata sulla partita" : "Segno sulla partita"}</button>`
    : "";
  return `<div class="market">
    <div>
      <div class="label">${market.label}</div>
      <div class="tied">${market.stat}</div>
      ${matchBtn}
    </div>
    ${cell(state.home, market)}
    ${cell(state.away, market)}
  </div>`;
}
function groupBlock(group) {
  const homeNums = values(state.home, group.kind);
  const awayNums = values(state.away, group.kind);
  const extra = group.id === "squadra"
    ? `<div class="series-block">
        <div><div class="who home">${esc(state.home)} · gol subiti</div><div class="series">${values(state.home, "ga").join(" ")}</div></div>
        <div><div class="who away">${esc(state.away)} · gol subiti</div><div class="series">${values(state.away, "ga").join(" ")}</div></div>
      </div>`
    : group.id === "tiri"
    ? `<div class="series-block">
        <div><div class="who home">${esc(state.home)} · tiri concessi</div><div class="series">${values(state.home, "sa").join(" ")}</div></div>
        <div><div class="who away">${esc(state.away)} · tiri concessi</div><div class="series">${values(state.away, "sa").join(" ")}</div></div>
      </div>`
    : group.id === "corner"
    ? `<div class="series-block">
        <div><div class="who home">${esc(state.home)} · corner concessi</div><div class="series">${values(state.home, "ca").join(" ")}</div></div>
        <div><div class="who away">${esc(state.away)} · corner concessi</div><div class="series">${values(state.away, "ca").join(" ")}</div></div>
      </div>`
    : "";
  const rows = MARKETS.filter(m => m.group === group.id).map(marketRow).join("");
  return `<section class="group">
    <h2>${group.title}</h2>
    <p class="blurb">${group.blurb}</p>
    <div class="series-block">
      <div><div class="who home">${esc(state.home)}</div><div class="series">${homeNums.join(" ")}</div></div>
      <div><div class="who away">${esc(state.away)}</div><div class="series">${awayNums.join(" ")}</div></div>
    </div>
    ${extra}
    ${rows}
  </section>`;
}
function logColumn(name, css) {
  const games = matches(name).map(m => `<div class="game">
    <div class="meta">${m.venue}${m.date ? " · " + m.date : ""}</div>
    <div><b>${esc(m.home)} ${m.hg}-${m.ag} ${esc(m.away)}</b></div>
    <div class="meta">tiri ${m.hs}-${m.as} · corner ${m.hc}-${m.ac} · xG ${m.hx.toFixed(2)}-${m.ax.toFixed(2)}</div>
  </div>`).join("");
  return `<div><h3 class="${css}">${esc(name)}</h3>${games}</div>`;
}
function picksBlock() {
  const mine = state.picks.filter(p => p.home === state.home && p.away === state.away);
  const body = mine.length
    ? mine.map(p => `<div class="pick"><div><b>${p.label}</b> · ${p.side}<span><br>${p.stat} · ${p.detail}</span></div><button type="button" class="textbtn" data-drop="${p.key}">Togli</button></div>`).join("")
    : `<p class="empty">Nessuna scelta su questo confronto. I mercati restano aperti.</p>`;
  return `<section class="card dock">
    <div class="brand"><span>La mia lettura</span><button type="button" class="textbtn" data-clear>Svuota questo confronto</button></div>
    ${body}
  </section>`;
}
function render() {
  const names = Object.keys(DATA.teams);
  const options = (selected) => names.map(n => `<option${n === selected ? " selected" : ""}>${esc(n)}</option>`).join("");
  const visible = GROUPS.filter(g => state.group === "all" || g.id === state.group)
    .filter(g => !state.focus || g.id === state.focus);
  const filterNote = state.focus
    ? `<p class="blurb">Filtro sulla statistica: ${STATS.find(s => s.key === state.focusStat).label}. <button type="button" class="textbtn" data-reset-filter>Mostra tutti i mercati</button></p>`
    : "";
  const chips = [{id:"all", title:"Tutti"}, ...GROUPS].map(g =>
    `<button type="button" class="chip${state.group === g.id ? " on" : ""}" data-group="${g.id}">${g.title}</button>`
  ).join("");
  document.getElementById("board").innerHTML = `
    <section class="card">
      <div class="head">
        <div class="side home">
          <div class="side-label">Sinistra</div>
          <select class="team" data-side="home">${options(state.home)}</select>
          <div class="sample">${sampleLine(state.home)}</div>
          <div class="form">${formPills(state.home)}</div>
        </div>
        <div class="vs">VS</div>
        <div class="side away">
          <div class="side-label">Destra</div>
          <select class="team" data-side="away">${options(state.away)}</select>
          <div class="sample">${sampleLine(state.away)}</div>
          <div class="form">${formPills(state.away)}</div>
        </div>
      </div>
    </section>
    <section class="card">
      <div class="brand"><span>Confronto medie</span><span>blu a sinistra · ambra a destra</span></div>
      ${STATS.map(statButton).join("")}
    </section>
    <section class="card">
      <div class="brand"><span>Mercati collegati</span><span>${esc(state.home)} · ${esc(state.away)}</span></div>
      <div class="chips">${chips}</div>
      ${filterNote}
      ${visible.map(groupBlock).join("")}
    </section>
    <section class="card">
      <div class="brand"><span>Tabellini scaricati</span><span>ordine per id, data assente</span></div>
      <div class="log">${logColumn(state.home, "home")}${logColumn(state.away, "away")}</div>
    </section>
    <section class="card">
      <div class="brand"><span>Mercati spenti</span><span>statistica assente</span></div>
      <div class="gaps">
        ${DATA.gaps.map(g => `<div class="gap"><div>${g.market}</div><div>${g.stat}</div><div>${g.why}</div></div>`).join("")}
      </div>
    </section>
    ${picksBlock()}
  `;
  document.getElementById("source").textContent =
    "Fonte: " + DATA.source + " · etichetta " + DATA.league + " · generata " + DATA.built_at +
    ". Le righe duplicate dello stesso tabellino sono state collassate. Quote assenti.";
}

function onChange(event) {
  const select = event.target.closest("select[data-side]");
  if (!select) return;
  const side = select.dataset.side;
  const name = select.value;
  if (side === "home" && name === state.away) state.away = state.home;
  if (side === "away" && name === state.home) state.home = state.away;
  state[side] = name;
  render();
}
function onClick(event) {
  const stat = event.target.closest("[data-stat]");
  const segno = event.target.closest("[data-segno]");
  const chip = event.target.closest("[data-group]");
  const drop = event.target.closest("[data-drop]");
  if (event.target.closest("[data-reset-filter]")) {
    state.focus = null;
    state.focusStat = null;
    render();
    return;
  }
  if (event.target.closest("[data-clear]")) {
    state.picks = state.picks.filter(p => !(p.home === state.home && p.away === state.away));
    savePicks();
    render();
    return;
  }
  if (stat && !segno) {
    const key = stat.dataset.stat;
    if (state.focusStat === key) {
      state.focus = null;
      state.focusStat = null;
    } else {
      state.focus = stat.dataset.focus;
      state.focusStat = key;
      state.group = "all";
    }
    render();
    return;
  }
  if (chip) {
    state.group = chip.dataset.group;
    state.focus = null;
    state.focusStat = null;
    render();
    return;
  }
  if (drop) {
    state.picks = state.picks.filter(p => p.key !== drop.dataset.drop);
    savePicks();
    render();
    return;
  }
  if (segno) {
    const market = MARKETS.find(m => m.id === segno.dataset.segno);
    const side = segno.dataset.side;
    const key = pickKey(market, side);
    if (hasPick(market, side)) {
      state.picks = state.picks.filter(p => p.key !== key);
    } else {
      const who = side === "partita" ? state.home : side;
      const c = count(who, market);
      const awayCount = count(state.away, market);
      const detail = side === "partita"
        ? state.home + " " + c.n + " volte su " + c.d + " · " + seriesText(state.home, market)
          + " | " + state.away + " " + awayCount.n + " volte su " + awayCount.d + " · " + seriesText(state.away, market)
        : c.n + " volte su " + c.d + " · " + seriesText(who, market);
      state.picks.push({
        key, home: state.home, away: state.away,
        label: market.label, stat: market.stat, side, detail
      });
    }
    savePicks();
    render();
  }
}

document.getElementById("board").addEventListener("change", onChange);
document.getElementById("board").addEventListener("click", onClick);
render();
</script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera la scheda statistiche demo")
    parser.add_argument("--league", default="Serie A")
    parser.add_argument("--home", default="Juventus")
    parser.add_argument("--away", default="Como")
    args = parser.parse_args()

    teams = load_teams(connect(), args.league)
    if args.home not in teams or args.away not in teams:
        known = ", ".join(teams)
        raise SystemExit(f"Coppia non trovata. Squadre disponibili: {known}")

    payload = {
        "source": "data/bagent.db",
        "league": args.league,
        "built_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "defaultHome": args.home,
        "defaultAway": args.away,
        "gaps": GAPS,
        "teams": teams,
    }
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(build_html(payload), encoding="utf-8")
    home_n = len(teams[args.home]["matches"])
    away_n = len(teams[args.away]["matches"])
    print(f"squadre {len(teams)}")
    print(f"{args.home} {home_n} distinte / {teams[args.home]['raw_rows']} righe")
    print(f"{args.away} {away_n} distinte / {teams[args.away]['raw_rows']} righe")
    print(OUT_PATH)


if __name__ == "__main__":
    main()

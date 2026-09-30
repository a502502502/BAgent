"""Archivio delle schedine già registrate, future e chiuse.

Legge i JSON in reports/tickets e, se c'è, il registro SQLite.
Non inventa una schedina: se il file non c'è, la pagina resta vuota.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent.parent
TICKETS_DIR = ROOT / "reports" / "tickets"
DEFAULT_DB = ROOT / "data" / "bagent.db"
PUBLIC_SITE = ROOT.parent / "bagent-schedine"
ROME = ZoneInfo("Europe/Rome")
CHECK_SECONDS = 30
# Una partita resta "presente" per la durata di gioco, recuperi compresi.
MATCH_WINDOW = timedelta(minutes=120)

_CLOSED = {"WON": "Vinta", "LOST": "Persa", "CASHOUT": "Cashout", "VOID": "Void"}
_OPEN = {"PENDING", "IN CORSO", "OPEN"}
_SECTION_LABEL = {"present": "In corso", "future": "Futura", "past": "Chiusa"}


@dataclass(frozen=True)
class SlipLeg:
    match: str
    pick: str
    odd: float | None
    when: datetime | None
    tournament: str = ""


@dataclass
class Slip:
    slip_id: str
    title: str
    status: str
    stake: float | None
    total_odds: float | None
    payout: float | None
    profit: float | None
    legs: list[SlipLeg] = field(default_factory=list)
    source: str = ""

    @property
    def kickoff(self) -> datetime | None:
        moments = [leg.when for leg in self.legs if leg.when is not None]
        return min(moments) if moments else None

    def section(self, now: datetime) -> str:
        """present = in corso, future = non ancora iniziata, past = chiusa."""
        moment = _aware(now)
        if self.status in _CLOSED:
            return "past"
        kickoffs = [leg.when for leg in self.legs if leg.when is not None]
        if not kickoffs:
            return "present" if self.status in _OPEN else "past"
        first, last = min(kickoffs), max(kickoffs)
        if first > moment:
            return "future"
        if last + MATCH_WINDOW > moment:
            return "present"
        return "past"


def load_slips(
    tickets_dir: Path | None = None,
    db_path: Path | None = None,
) -> list[Slip]:
    """JSON e registro, uniti per id. Il registro vince sullo stato, perché è la chiusura."""
    found: dict[str, Slip] = {}
    folder = tickets_dir if tickets_dir is not None else TICKETS_DIR
    if folder.exists():
        for path in sorted(folder.glob("*.json")):
            slip = _slip_from_json(path)
            if slip is not None:
                found[slip.slip_id] = slip
    database = db_path if db_path is not None else DEFAULT_DB
    for slip in _slips_from_db(database):
        previous = found.get(slip.slip_id)
        if previous is not None and not slip.legs:
            slip.legs = previous.legs
        found[slip.slip_id] = slip
    return list(found.values())


def split_slips(slips: list[Slip], now: datetime) -> dict[str, list[Slip]]:
    moment = _aware(now)
    groups = {"present": [], "future": [], "past": []}
    for slip in slips:
        groups[slip.section(moment)].append(slip)
    opening = datetime(9999, 1, 1, tzinfo=ROME)
    closed = datetime(1970, 1, 1, tzinfo=ROME)
    groups["present"].sort(key=lambda slip: slip.kickoff or opening)
    groups["future"].sort(key=lambda slip: slip.kickoff or opening)
    groups["past"].sort(key=lambda slip: slip.kickoff or closed, reverse=True)
    return groups


def archive_payload(slips: list[Slip], now: datetime) -> dict:
    moment = _aware(now)
    groups = split_slips(slips, moment)
    settled = [slip.profit for slip in groups["past"] if slip.profit is not None and slip.status in _CLOSED]
    profit = sum(settled) if settled else None
    return {
        "generated_at": moment.isoformat(timespec="seconds"),
        "check_seconds": CHECK_SECONDS,
        "profit_label": "—" if profit is None else f"{profit:+.2f} €",
        "present": [_public_slip(slip, "present") for slip in groups["present"]],
        "future": [_public_slip(slip, "future") for slip in groups["future"]],
        "past": [_public_slip(slip, "past") for slip in groups["past"]],
    }


def render_slip_page(slips: list[Slip], now: datetime) -> str:
    payload = json.dumps(archive_payload(slips, now), ensure_ascii=False).replace("<", "\\u003c")
    return _PAGE.replace("__BOOT__", payload)


_PAGE = r"""<!DOCTYPE html>
<html lang="it">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BAgent — Archivio schedine</title>
<style>
  :root { --bg:#070d19; --card:#111c30; --line:#1e293b; --text:#f8fafc; --muted:#94a3b8; --blue:#38bdf8; --green:#10b981; --yellow:#f59e0b; --red:#f87171; }
  * { box-sizing:border-box; }
  body { margin:0; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; background:var(--bg); color:var(--text); }
  main { max-width:980px; margin:0 auto; padding:16px; }
  h1 { font-size:22px; margin:0 0 4px; }
  p { color:var(--muted); margin:0; }
  header { display:flex; justify-content:space-between; gap:12px; align-items:flex-end; margin-bottom:14px; flex-wrap:wrap; }
  .stat { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 12px; min-width:110px; }
  .stat b { display:block; font-size:16px; }
  nav { display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin-bottom:8px; }
  nav button { background:#0f172a; color:var(--muted); border:1px solid var(--line); border-radius:10px; padding:10px 6px; font-weight:700; cursor:pointer; }
  nav button.on { background:#1e293b; color:var(--text); border-color:var(--yellow); }
  nav button b { display:block; font-size:18px; color:var(--blue); }
  form { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; margin:0 0 16px; }
  label { display:block; color:var(--muted); font-size:12px; margin:8px 0 4px; }
  input[type="date"], textarea { width:100%; background:#0f172a; color:var(--text); border:1px solid var(--line); border-radius:8px; padding:8px; }
  .flags input { width:auto; }
  .flags { display:flex; flex-wrap:wrap; gap:8px; margin:8px 0; }
  .flags label { margin:0; color:var(--text); }
  form button { background:#0369a1; color:#f0f9ff; border:0; border-radius:8px; padding:10px 14px; font-weight:700; cursor:pointer; }
  #advice .why { margin:4px 0 0; color:var(--muted); font-size:13px; }
  #check { color:var(--muted); font-size:12px; min-height:18px; margin:0 0 12px; }
  #check.ok { color:var(--green); }
  #check.bad { color:var(--red); }
  .card { background:var(--card); border:1px solid var(--line); border-radius:12px; padding:12px; margin:0 0 12px; }
  .top { display:flex; justify-content:space-between; gap:8px; }
  .odd { font-size:20px; font-weight:800; color:var(--blue); }
  .meta { color:var(--muted); font-size:12px; margin:6px 0; }
  table { width:100%; border-collapse:collapse; font-size:13px; }
  td { padding:6px 0; border-top:1px solid var(--line); vertical-align:top; }
  .pick { color:var(--blue); }
  .Vinta { color:var(--green); } .Persa { color:var(--red); } .Futura, .In, .corso { color:var(--yellow); }
</style>
</head>
<body>
<main>
  <header>
    <div>
      <h1>Archivio schedine</h1>
      <p id="generated">Caricamento</p>
    </div>
    <div class="stat">P/L chiuso<b id="profit">—</b></div>
  </header>
  <nav>
    <button type="button" data-section="present" class="on">Presenti <b id="n-present">0</b></button>
    <button type="button" data-section="future">Future <b id="n-future">0</b></button>
    <button type="button" data-section="past">Passate <b id="n-past">0</b></button>
  </nav>
  <p id="check">Controllo ogni 30 secondi</p>
  <form id="ask">
    <strong>Chiedi schedina</strong>
    <label for="ask-date">Data</label>
    <input id="ask-date" name="date" type="date" required>
    <label for="ask-query">Squadre o partite, una per riga. Vuoto: il meglio del giorno.</label>
    <textarea id="ask-query" name="query" rows="3" placeholder="Napoli vs Cagliari"></textarea>
    <div class="flags">
      <label><input type="checkbox" name="corto_muso_home"> Casa di misura</label>
      <label><input type="checkbox" name="corto_muso_away"> Ospite di misura</label>
      <label><input type="checkbox" name="slow_start"> Avvio lento</label>
      <label><input type="checkbox" name="rotation"> Turnover</label>
      <label><input type="checkbox" name="low_motivation_home"> Motivazione bassa casa</label>
      <label><input type="checkbox" name="low_motivation_away"> Motivazione bassa ospite</label>
    </div>
    <button type="submit">Mercato migliore</button>
    <p id="ask-status" class="meta"></p>
    <div id="advice"></div>
  </form>
  <section id="list"></section>
</main>
<script type="application/json" id="boot">__BOOT__</script>
<script>
const EMPTY = {
  present: "Nessuna schedina in corso.",
  future: "Nessuna schedina con kickoff ancora davanti.",
  past: "Nessuna schedina chiusa in archivio."
};
let data = JSON.parse(document.getElementById("boot").textContent);
let section = "present";
let left = 30;
let adviceUrl = "";
const list = document.getElementById("list");
const check = document.getElementById("check");

function text(tag, value, className) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  node.textContent = value || "";
  return node;
}

function card(slip) {
  const art = document.createElement("article");
  art.className = "card";
  const top = document.createElement("div");
  top.className = "top";
  const title = document.createElement("div");
  title.appendChild(text("strong", slip.title));
  const meta = text("div", (slip.id || "") + " · " + (slip.label || ""), "meta");
  meta.className = "meta " + (slip.label || "").split(" ")[0];
  title.appendChild(meta);
  top.appendChild(title);
  top.appendChild(text("div", slip.odds || "—", "odd"));
  art.appendChild(top);
  art.appendChild(text("div", "Stake " + (slip.stake || "—"), "meta"));
  const table = document.createElement("table");
  (slip.legs || []).forEach(function (leg) {
    const row = document.createElement("tr");
    row.appendChild(text("td", leg.when || "—"));
    const match = document.createElement("td");
    match.appendChild(document.createTextNode(leg.match || ""));
    match.appendChild(text("div", leg.pick || "", "pick"));
    row.appendChild(match);
    row.appendChild(text("td", leg.odd || "—"));
    table.appendChild(row);
  });
  art.appendChild(table);
  return art;
}

function render() {
  ["present", "future", "past"].forEach(function (name) {
    document.getElementById("n-" + name).textContent = String((data[name] || []).length);
  });
  document.getElementById("profit").textContent = data.profit_label || "—";
  document.getElementById("generated").textContent = "Dati del " + (data.generated_at || "—");
  document.querySelectorAll("button[data-section]").forEach(function (button) {
    button.classList.toggle("on", button.getAttribute("data-section") === section);
  });
  list.replaceChildren();
  const rows = data[section] || [];
  if (!rows.length) {
    list.appendChild(text("p", EMPTY[section], "meta"));
    return;
  }
  rows.forEach(function (slip) { list.appendChild(card(slip)); });
}

function stamp() {
  return new Date().toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function selectionCard(row) {
  const art = document.createElement("article");
  art.className = "card";
  const top = document.createElement("div");
  top.className = "top";
  const title = document.createElement("div");
  title.appendChild(text("strong", row.match));
  title.appendChild(text("div", (row.when || "") + " · " + (row.league || ""), "meta"));
  title.appendChild(text("div", row.market || "", "pick"));
  top.appendChild(title);
  top.appendChild(text("div", row.odd || "—", "odd"));
  art.appendChild(top);
  art.appendChild(text("div", "P " + (row.probability || "—") + " · fair " + (row.fair_odd || "—") + " · edge " + (row.edge || "—"), "meta"));
  (row.motivations || []).forEach(function (line) {
    art.appendChild(text("p", line, "why"));
  });
  return art;
}

function showAdvice(payload) {
  const box = document.getElementById("advice");
  box.replaceChildren();
  if (!payload) return;
  if (payload.message && !payload.selections) {
    box.appendChild(text("p", payload.message, "meta"));
    return;
  }
  box.appendChild(text("p", payload.note || "", "meta"));
  if (payload.total_odds) {
    box.appendChild(text("p", "Quota combinata " + payload.total_odds, "meta"));
  }
  (payload.selections || []).forEach(function (row) { box.appendChild(selectionCard(row)); });
  if (!(payload.selections || []).length) {
    box.appendChild(text("p", payload.message || "Nessun mercato nello sweet spot per questa richiesta.", "meta"));
  }
  (payload.discarded || []).forEach(function (row) {
    box.appendChild(text("p", (row.match || "") + ": " + (row.reason || ""), "meta"));
  });
}

async function refresh() {
  try {
    const response = await fetch("schedine.json?t=" + Date.now(), { cache: "no-store" });
    if (!response.ok) throw new Error(String(response.status));
    data = await response.json();
    render();
    try {
      const engine = await fetch("motore.json?t=" + Date.now(), { cache: "no-store" });
      if (engine.ok) adviceUrl = ((await engine.json()).advice_url || "").replace(/\/$/, "");
    } catch (ignore) {}
    check.className = "ok";
    check.textContent = "Ultimo controllo " + stamp() + " · prossimo tra " + left + "s";
  } catch (error) {
    check.className = "bad";
    check.textContent = "Controllo non riuscito alle " + stamp() + " · nuovo tentativo tra " + left + "s";
  }
}

document.getElementById("ask").addEventListener("submit", async function (event) {
  event.preventDefault();
  const status = document.getElementById("ask-status");
  if (!adviceUrl) {
    status.textContent = "Motore non collegato. Il controllo lo riprova ogni 30 secondi.";
    return;
  }
  const form = new FormData(event.target);
  const flags = {};
  ["corto_muso_home", "corto_muso_away", "slow_start", "rotation", "low_motivation_home", "low_motivation_away"].forEach(function (name) {
    flags[name] = form.get(name) === "on";
  });
  status.textContent = "Calcolo in corso";
  try {
    const response = await fetch(adviceUrl + "/api/schedina", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        date: form.get("date"),
        query: form.get("query") || "",
        flags: flags
      })
    });
    const payload = await response.json();
    status.textContent = response.ok ? "Risposta aggiornata" : "Richiesta non riuscita";
    showAdvice(payload);
  } catch (error) {
    status.textContent = "Motore non raggiungibile.";
  }
});

document.querySelectorAll("button[data-section]").forEach(function (button) {
  button.addEventListener("click", function () {
    section = button.getAttribute("data-section");
    render();
  });
});
const today = new Date();
document.getElementById("ask-date").value = today.getFullYear() + "-" + String(today.getMonth() + 1).padStart(2, "0") + "-" + String(today.getDate()).padStart(2, "0");
render();
refresh();
setInterval(function () {
  left -= 1;
  if (left <= 0) {
    left = data.check_seconds || 30;
    refresh();
    return;
  }
  const failed = check.className === "bad";
  check.textContent = (failed ? "Controllo non riuscito" : "Ultimo controllo ok") + " · prossimo tra " + left + "s";
}, 1000);
</script>
</body>
</html>
"""


def write_slip_archive(
    destination: Path | None = None,
    *,
    tickets_dir: Path | None = None,
    db_path: Path | None = None,
    now: datetime | None = None,
) -> Path:
    moment = _aware(now or datetime.now(ROME))
    slips = load_slips(tickets_dir, db_path)
    target = destination or (ROOT / "portal" / "schedine.html")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_slip_page(slips, moment), encoding="utf-8")
    feed = json.dumps(archive_payload(slips, moment), ensure_ascii=False)
    target.with_name("schedine.json").write_text(feed, encoding="utf-8")
    return target


def _slip_from_json(path: Path) -> Slip | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    slip_id = str(payload.get("ticket_id") or path.stem)
    created = _parse_when(str(payload.get("created_at") or ""))
    legs = []
    for raw in payload.get("legs") or []:
        if not isinstance(raw, dict):
            continue
        when = _parse_when(str(raw.get("date_time") or raw.get("kickoff") or ""))
        if when is None and created is not None and raw.get("time"):
            clock = _parse_when(created.strftime("%Y-%m-%d") + " " + str(raw.get("time")))
            when = clock
        odd = _number(raw.get("netwin_odds") or raw.get("odds"))
        legs.append(
            SlipLeg(
                match=str(raw.get("match") or ""),
                pick=str(raw.get("pick") or raw.get("selection") or ""),
                odd=odd,
                when=when,
                tournament=str(raw.get("tournament") or ""),
            )
        )
    return Slip(
        slip_id=slip_id,
        title=str(payload.get("name") or payload.get("description") or slip_id),
        status=str(payload.get("status") or "").upper(),
        stake=_number(payload.get("stake") or payload.get("stake_eur")),
        total_odds=_number(payload.get("total_odds")),
        payout=_number(payload.get("payout_eur") or payload.get("potential_win")),
        profit=_number(payload.get("profit_loss_eur")),
        legs=legs,
        source=path.name,
    )


def _slips_from_db(db_path: Path) -> list[Slip]:
    if not db_path.exists():
        return []
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error:
        return []
    try:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "ticket_ledger" not in tables:
            return []
        slips: list[Slip] = []
        for row in conn.execute("SELECT * FROM ticket_ledger"):
            legs: list[SlipLeg] = []
            if "bet_leg_ledger" in tables:
                for leg in conn.execute(
                    "SELECT * FROM bet_leg_ledger WHERE ticket_id = ?",
                    (row["ticket_id"],),
                ):
                    legs.append(
                        SlipLeg(
                            match=str(leg["match_name"] or ""),
                            pick=str(leg["selection"] or ""),
                            odd=_number(leg["odds"]),
                            when=None,
                            tournament=str(leg["tournament"] or ""),
                        )
                    )
            slips.append(
                Slip(
                    slip_id=str(row["ticket_id"]),
                    title=str(row["description"] or row["ticket_id"]),
                    status=str(row["status"] or "").upper(),
                    stake=_number(row["stake_eur"]),
                    total_odds=_number(row["total_odds"]),
                    payout=_number(row["payout_eur"]),
                    profit=_number(row["profit_loss_eur"]),
                    legs=legs,
                    source="ticket_ledger",
                )
            )
        return slips
    except sqlite3.Error:
        return []
    finally:
        conn.close()


def _public_slip(slip: Slip, section: str) -> dict:
    label = _CLOSED.get(slip.status) or _SECTION_LABEL[section]
    return {
        "id": slip.slip_id,
        "title": slip.title,
        "label": label,
        "stake": None if slip.stake is None else f"{slip.stake:.2f} €",
        "odds": None if slip.total_odds is None else f"{slip.total_odds:.2f}×",
        "legs": [
            {
                "when": _when_label(leg.when),
                "match": leg.match,
                "pick": leg.pick,
                "odd": "—" if leg.odd is None else f"{leg.odd:.2f}",
            }
            for leg in slip.legs
        ],
    }


def _when_label(moment: datetime | None) -> str:
    if moment is None:
        return "—"
    return moment.strftime("%d/%m %H:%M")


def _parse_when(value: str) -> datetime | None:
    text = value.strip().replace("CEST", "").replace("CET", "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M:%S", "%d/%m/%Y %H:%M"):
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.replace(tzinfo=ROME)
    return None


def _number(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _aware(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=ROME)
    return moment.astimezone(ROME)

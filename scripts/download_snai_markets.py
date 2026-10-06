"""Scarica tutti i mercati di una partita SNAI.

La pagina dell'evento carica la scheda completa da flutterseatech.
Lo script apre quella pagina in background, intercetta la risposta e salva
mercato, linea e quota.

    python scripts/download_snai_markets.py https://www.snai.it/scommesse/evento/calcio/nations-league/italia-turchia
    python scripts/download_snai_markets.py <URL> --out reports/snai/italia-turchia.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    str(Path(os.environ["LOCALAPPDATA"]) / "ms-playwright"),
)

from playwright.sync_api import sync_playwright

CEST = timezone(timedelta(hours=2))
EDGE_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0"
)


def _kickoff_cest(raw: str | None) -> str:
    if not raw:
        return ""
    when = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(CEST)
    return when.strftime("%Y-%m-%d %H:%M CEST")


def compact_event_detail(detail: dict, source_url: str) -> dict:
    """Riduce la scheda SNAI a mercato, linea ed esiti con quota."""
    markets_map = detail.get("scommessaMap") or {}
    markets = []
    for info in (detail.get("infoAggiuntivaMap") or {}).values():
        code = (
            f"{info.get('codicePalinsesto')}-"
            f"{info.get('codiceAvvenimento')}-"
            f"{info.get('codiceScommessa')}"
        )
        outcomes = []
        for esito in info.get("esitoList") or []:
            raw_odd = esito.get("quota")
            if not raw_odd or raw_odd == 100:
                continue
            outcomes.append({
                "selection": esito.get("descrizione") or "",
                "odds": round(raw_odd) / 100,
                "open": esito.get("stato") == 1,
            })
        if not outcomes:
            continue
        markets.append({
            "market": (markets_map.get(code) or {}).get("descrizione") or code,
            "line": info.get("descrizione") or "",
            "outcomes": outcomes,
        })
    event = detail.get("avvenimentoFe") or {}
    event_id = ""
    if event.get("codicePalinsesto") and event.get("codiceAvvenimento"):
        event_id = f"{event['codicePalinsesto']}-{event['codiceAvvenimento']}"
    return {
        "match": event.get("descrizione") or "",
        "event_id": event_id,
        "kickoff_time": _kickoff_cest(event.get("data")),
        "source": "snai",
        "source_url": source_url,
        "fetched_at": datetime.now(CEST).strftime("%Y-%m-%d %H:%M CEST"),
        "market_count": len(markets),
        "markets": markets,
    }


def _capture_event_detail(url: str) -> dict:
    captured: dict[str, str] = {}

    def on_response(response) -> None:
        if "eventDetail" not in response.url or response.status >= 400:
            return
        try:
            body = response.text()
        except Exception:
            return
        if len(body) > len(captured.get("body", "")):
            captured["body"] = body
            captured["url"] = response.url

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            channel="msedge",
            headless=True,
            args=["--disable-http2", "--disable-quic"],
        )
        page = browser.new_page(user_agent=EDGE_UA)
        page.on("response", on_response)
        last_error = ""
        for attempt in range(2):
            try:
                page.goto(url, wait_until="commit", timeout=40000)
                page.wait_for_timeout(8000)
                if captured.get("body"):
                    break
                page.wait_for_timeout(7000)
            except Exception as exc:
                last_error = str(exc).splitlines()[0]
                if attempt == 1:
                    browser.close()
                    raise RuntimeError(f"Pagina SNAI non raggiungibile: {last_error}") from exc
        browser.close()

    if not captured.get("body"):
        raise RuntimeError("La scheda mercati non è arrivata dalla pagina SNAI.")
    return json.loads(captured["body"])


def download_snai_match(url: str, output: Path | None = None) -> dict:
    catalog = compact_event_detail(_capture_event_detail(url), url)
    if catalog["market_count"] == 0:
        raise RuntimeError(f"Nessun mercato per {catalog['match'] or url}.")
    target = output
    if target is None:
        slug = url.rstrip("/").split("/")[-1] or "partita"
        target = ROOT / "reports" / "snai" / f"{slug}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
    catalog["output"] = str(target)
    return catalog


def main() -> None:
    parser = argparse.ArgumentParser(description="Scarica tutti i mercati di una partita SNAI.")
    parser.add_argument("url", help="Indirizzo dell'evento, es. .../nations-league/italia-turchia")
    parser.add_argument("--out", type=Path, default=None, help="File JSON di destinazione")
    args = parser.parse_args()
    catalog = download_snai_match(args.url, args.out)
    print(
        f"{catalog['kickoff_time']}|{catalog['match']}|{catalog['event_id']}"
        f"|{catalog['market_count']} mercati|{catalog['output']}"
    )


if __name__ == "__main__":
    main()

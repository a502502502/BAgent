#!/usr/bin/env python3
"""Scarica i JSON mercati SNAI per lo slate 07/10/2026 (paste utente)."""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault(
    "PLAYWRIGHT_BROWSERS_PATH",
    str(Path.home() / "Library/Caches/ms-playwright"),
)

from playwright.sync_api import sync_playwright

CEST = timezone(timedelta(hours=2))
EDGE_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/128.0.0.0 Safari/537.36"
)
OUT = ROOT / "reports" / "snai" / "2026-10-07"

# URL candidati costruiti dal paste SNAI 07/10 (slug tipici snai.it)
URLS = [
    "https://www.snai.it/scommesse/evento/calcio/amichevoli-nazionali/argentina-benin",
    "https://www.snai.it/scommesse/evento/calcio/amichevoli-nazionali/colombia-peru",
    "https://www.snai.it/scommesse/evento/calcio/amichevoli-nazionali/stati-uniti-canada",
    "https://www.snai.it/scommesse/evento/calcio/amichevoli-nazionali/messico-cile",
    "https://www.snai.it/scommesse/evento/calcio/mls/chicago-fire-vancouver-whitecaps",
    "https://www.snai.it/scommesse/evento/calcio/usa-mls/chicago-fire-vancouver-whitecaps",
    "https://www.snai.it/scommesse/evento/calcio/par-division-profesional/olimpia-asuncion-club-nacional",
    "https://www.snai.it/scommesse/evento/calcio/paraguay/olimpia-asuncion-club-nacional",
    "https://www.snai.it/scommesse/evento/calcio/coppa-del-cile/colo-colo-puerto-montt",
    "https://www.snai.it/scommesse/evento/calcio/chi-coppa-del-cile/colo-colo-puerto-montt",
    "https://www.snai.it/scommesse/evento/calcio/ecu-coppa/universidad-catolica-ldu-quito",
    "https://www.snai.it/scommesse/evento/calcio/ecuador-coppa/cd-universidad-catolica-ldu-quito",
    "https://www.snai.it/scommesse/evento/calcio/uru-coppa-auf/cs-cerrito-montevideo-wanderers",
    "https://www.snai.it/scommesse/evento/calcio/concacaf-nations-league/antigua-e-barbuda-aruba",
    "https://www.snai.it/scommesse/evento/calcio/bra-serie-b/goias-athletic-club-sjdr-mg",
    "https://www.snai.it/scommesse/evento/calcio/serie-b-brasile/ponte-preta-sp-juventude",
    "https://www.snai.it/scommesse/evento/calcio/jpn-coppa-dell-imperatore/urawa-reds-omiya-ardija",
    "https://www.snai.it/scommesse/evento/calcio/jpn-coppa-dell-imperatore/fc-tokyo-shonan-bellmare",
    "https://www.snai.it/scommesse/evento/calcio/fin-veikkausliiga/if-gnistan-inter-turku",
    "https://www.snai.it/scommesse/evento/calcio/esp-segunda-b/cartagena-real-murcia-cf",
]


def slugify(s: str) -> str:
    s = (
        s.lower()
        .replace("ù", "u")
        .replace("à", "a")
        .replace("è", "e")
        .replace("é", "e")
        .replace("ò", "o")
        .replace("ì", "i")
    )
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def compact_event_detail(detail: dict, source_url: str) -> dict:
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
    kickoff = ""
    raw = event.get("data")
    if raw:
        when = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(CEST)
        kickoff = when.strftime("%Y-%m-%d %H:%M CEST")
    return {
        "match": event.get("descrizione") or "",
        "competition": event.get("descrizioneManifestazione") or "",
        "event_id": event_id,
        "kickoff_time": kickoff,
        "source": "snai",
        "source_url": source_url,
        "page_url": "",
        "fetched_at": datetime.now(CEST).strftime("%Y-%m-%d %H:%M CEST"),
        "market_count": len(markets),
        "markets": markets,
    }


def accept_cookies(page) -> None:
    for label in ("Accetta tutti", "Accetta", "Accept all"):
        btn = page.locator(f"button:has-text('{label}')")
        if btn.count():
            try:
                btn.first.click(timeout=1200)
                page.wait_for_timeout(800)
            except Exception:
                pass


def extract_event_id_from_html(html: str) -> str | None:
    patterns = [
        r"eventDetail/(\d+-\d+)",
        r'"codicePalinsesto"\s*:\s*(\d+).*?"codiceAvvenimento"\s*:\s*(\d+)',
        r"codicePalinsesto[=:](\d+).{0,40}codiceAvvenimento[=:](\d+)",
        r"/(\d{5})-(\d{3,6})(?:\?|/|\")",
    ]
    m = re.search(patterns[0], html)
    if m:
        return m.group(1)
    for pat in patterns[1:]:
        m = re.search(pat, html, re.S)
        if m and m.lastindex and m.lastindex >= 2:
            return f"{m.group(1)}-{m.group(2)}"
    return None


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    results = []
    seen = set()

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chrome,
            args=["--disable-http2", "--disable-quic", "--no-sandbox"],
        )
        for url in URLS:
            print(f"\n=== {url}", flush=True)
            ctx = browser.new_context(
                user_agent=EDGE_UA,
                viewport={"width": 1400, "height": 900},
                extra_http_headers={"Accept-Language": "it-IT,it;q=0.9"},
            )
            page = ctx.new_page()
            captured: dict[str, str] = {}
            all_api: list[str] = []

            def on_response(resp):
                u = resp.url
                if "flutterseatech" in u or "eventDetail" in u or "palinsesto" in u:
                    all_api.append(f"{resp.status} {u[:180]}")
                if "eventDetail" in u and resp.status < 400:
                    try:
                        body = resp.text()
                    except Exception:
                        return
                    if len(body) > len(captured.get("body", "")):
                        captured["body"] = body
                        captured["url"] = u

            page.on("response", on_response)
            try:
                page.goto(url, wait_until="commit", timeout=35000)
                accept_cookies(page)
                page.wait_for_timeout(6000)
                title = page.title()
                final_url = page.url
                print(f"  title={title!r} final={final_url}", flush=True)

                # Force markets tab if present
                for label in ("TUTTE", "PRINCIPALI", "COMBO"):
                    loc = page.get_by_text(label, exact=True)
                    if loc.count():
                        try:
                            loc.first.click(timeout=1500)
                            page.wait_for_timeout(3500)
                        except Exception:
                            pass

                if not captured.get("body"):
                    page.wait_for_timeout(7000)

                # Fallback: extract event id and fetch via page.request
                if not captured.get("body"):
                    html = page.content()
                    eid = extract_event_id_from_html(html)
                    print(f"  fallback eid={eid} api_seen={len(all_api)}", flush=True)
                    for line in all_api[:8]:
                        print(f"    api {line}", flush=True)
                    if eid:
                        api = (
                            "https://betting-snai.flutterseatech.it/api/"
                            "lettura-palinsesto-sport/palinsesto/prematch/v1/"
                            f"eventDetail/{eid}?offerId=0&metaTplEnabled=true"
                        )
                        try:
                            r = page.request.get(
                                api,
                                headers={
                                    "Referer": final_url,
                                    "Origin": "https://www.snai.it",
                                    "Accept": "application/json",
                                },
                                timeout=20000,
                            )
                            print(f"  request {r.status} len={len(r.text())}", flush=True)
                            if r.status == 200 and len(r.text()) > 200:
                                captured["body"] = r.text()
                                captured["url"] = api
                        except Exception as e:
                            print(f"  request err: {e}", flush=True)

                if not captured.get("body"):
                    results.append({
                        "url": url,
                        "ok": False,
                        "title": title,
                        "error": "no eventDetail",
                        "api_seen": all_api[:10],
                    })
                    ctx.close()
                    continue

                catalog = compact_event_detail(
                    json.loads(captured["body"]), captured["url"]
                )
                catalog["page_url"] = final_url
                if not catalog["match"] or catalog["market_count"] == 0:
                    results.append({"url": url, "ok": False, "error": "empty markets"})
                    ctx.close()
                    continue
                if catalog["event_id"] in seen:
                    print(f"  skip dup {catalog['event_id']}", flush=True)
                    ctx.close()
                    continue
                seen.add(catalog["event_id"])
                fname = f"{slugify(catalog['competition'] or 'match')}--{slugify(catalog['match'])}.json"
                path = OUT / fname
                path.write_text(json.dumps(catalog, ensure_ascii=False), encoding="utf-8")
                print(
                    f"  OK {catalog['kickoff_time']}|{catalog['match']}|"
                    f"{catalog['market_count']} -> {path.name}",
                    flush=True,
                )
                results.append({
                    "url": url,
                    "ok": True,
                    "file": str(path.relative_to(ROOT)),
                    "match": catalog["match"],
                    "competition": catalog["competition"],
                    "kickoff_time": catalog["kickoff_time"],
                    "event_id": catalog["event_id"],
                    "markets": catalog["market_count"],
                })
            except Exception as e:
                print(f"  ERR {e}", flush=True)
                results.append({"url": url, "ok": False, "error": str(e)[:240]})
            finally:
                ctx.close()

        browser.close()

    ok = [r for r in results if r.get("ok")]
    (OUT / "index.json").write_text(
        json.dumps(ok, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT / "download_log.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nDONE ok={len(ok)}/{len(results)} dir={OUT}", flush=True)


if __name__ == "__main__":
    main()

"""
TotalCorner — fonte statistiche calcio (gol, corner, forma recente).

Fornisce per ogni partita:
  - Over 2.5% storico (casa e trasferta, ultime 10 partite)
  - Media gol segnati/subiti
  - Corner Over% (soglia 9.5)
  - Forma recente (W/L/D)
  - Note testuali predittive ("La squadra casa non ha vinto in X delle ultime Y")
  - Pronostico automatico del sito

URL struttura:
  Homepage oggi:  https://www.totalcorner.com/it/
  Match stats:    https://www.totalcorner.com/it/stats/{home}-vs-{away}/{match_id}

Cloudflare-aware: usa cloudscraper con fallback a requests standard.
"""

from __future__ import annotations

import re
import time
from datetime import date
from typing import Any
from urllib.parse import quote

try:
    import cloudscraper
    _HAS_CLOUDSCRAPER = True
except ImportError:
    _HAS_CLOUDSCRAPER = False

try:
    from playwright.sync_api import sync_playwright
    _HAS_PLAYWRIGHT = True
except ImportError:
    _HAS_PLAYWRIGHT = False

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.totalcorner.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.8",
    "Referer": "https://www.totalcorner.com/it/",
}


def _slugify(name: str) -> str:
    """Converte nome squadra in slug URL (es. 'FC Kharkiv' → 'fc-kharkiv')."""
    s = name.lower().strip()
    s = re.sub(r"[àáâä]", "a", s)
    s = re.sub(r"[èéêë]", "e", s)
    s = re.sub(r"[ìíîï]", "i", s)
    s = re.sub(r"[òóôö]", "o", s)
    s = re.sub(r"[ùúûü]", "u", s)
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def _name_similarity(a: str, b: str) -> float:
    """Similarità semplice tra due nomi squadra (0-1)."""
    a, b = a.lower(), b.lower()
    if a == b:
        return 1.0
    # Partial match
    if a in b or b in a:
        return 0.8
    # Parole in comune
    words_a = set(a.split())
    words_b = set(b.split())
    common = words_a & words_b
    if common:
        return len(common) / max(len(words_a), len(words_b))
    return 0.0


class TotalCornerSource:
    """
    Wrapper per TotalCorner.com.

    Utilizzo:
        tc = TotalCornerSource()
        data = tc.collect("Polissya Zhytomyr", "Zorya", date(2026, 8, 17))
        # data["home_over25_pct"] → 0.90
        # data["away_over25_pct"] → 0.70
        # data["prediction"]     → "Gol Over 2.5, Corner Under 9.5"
        # data["notes"]          → ["La squadra casa non ha vinto..."]
    """

    def __init__(self, delay: float = 1.0, lang: str = "it", use_browser: bool = False):
        self._delay = delay
        self._lang = lang
        self._base = f"{BASE_URL}/{lang}"
        self._use_browser = use_browser or (not _HAS_CLOUDSCRAPER and _HAS_PLAYWRIGHT)

        # Preferisce cloudscraper per bypassare Cloudflare
        if not self._use_browser:
            if _HAS_CLOUDSCRAPER:
                self._session = cloudscraper.create_scraper(
                    browser={"browser": "chrome", "platform": "windows", "mobile": False}
                )
            else:
                self._session = requests.Session()
                self._session.headers.update(HEADERS)
        else:
            self._session = None  # usa Playwright

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _get(self, url: str) -> BeautifulSoup:
        time.sleep(self._delay)

        if self._use_browser and _HAS_PLAYWRIGHT:
            return self._get_playwright(url)

        r = self._session.get(url, headers=HEADERS, timeout=20)

        # Fallback automatico a Playwright se Cloudflare blocca (403/503)
        if r.status_code in (403, 503) and _HAS_PLAYWRIGHT:
            print(f"[TotalCorner] Cloudflare ({r.status_code}) → fallback Playwright")
            return self._get_playwright(url)

        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")

    def _get_playwright(self, url: str) -> BeautifulSoup:
        """Fetch con Playwright (Chromium headless) per bypassare Cloudflare."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30_000)
            html = page.content()
            browser.close()
        return BeautifulSoup(html, "html.parser")

    # ------------------------------------------------------------------
    # Today's matches (homepage)
    # ------------------------------------------------------------------

    def today_matches(self, target_date: date | None = None) -> list[dict]:
        """
        Restituisce tutte le partite del giorno dalla homepage TotalCorner.

        Ogni entry:
            {id, home, away, league, time, url}
        """
        url = self._base + "/"
        soup = self._get(url)

        matches = []
        # Le partite sono in righe <tr> con link /it/stats/...
        for link in soup.select("a[href*='/stats/']"):
            href = link.get("href", "")
            m = re.search(r"/stats/(.+?)-vs-(.+?)/(\d+)", href)
            if not m:
                continue

            home_slug, away_slug, match_id = m.group(1), m.group(2), m.group(3)

            # Testo del link (di solito il nome della squadra casa o l'intero evento)
            row = link.find_parent("tr") or link.find_parent("div")
            row_text = row.get_text(" ", strip=True) if row else link.get_text(strip=True)

            matches.append({
                "id": int(match_id),
                "home_slug": home_slug,
                "away_slug": away_slug,
                "url": BASE_URL + href,
                "raw_text": row_text[:200],
            })

        return matches

    # ------------------------------------------------------------------
    # Match stats page
    # ------------------------------------------------------------------

    def match_stats(self, match_id: int, home_slug: str, away_slug: str) -> dict:
        """
        Fetch e parsing della pagina statistiche di una singola partita.

        Ritorna dict con:
            found, home_name, away_name,
            home_form_summary, away_form_summary,
            home_over25_pct, away_over25_pct,
            home_avg_goals_scored, home_avg_goals_conceded,
            away_avg_goals_scored, away_avg_goals_conceded,
            home_win_pct, away_win_pct,
            home_corner_over_pct, away_corner_over_pct,
            prediction, notes, odds_ref
        """
        url = f"{self._base}/stats/{home_slug}-vs-{away_slug}/{match_id}"
        try:
            soup = self._get(url)
        except Exception as e:
            return {"found": False, "error": str(e), "url": url}

        result: dict[str, Any] = {
            "found": True,
            "source": "totalcorner",
            "url": url,
            "match_id": match_id,
        }

        text = soup.get_text("\n", strip=True)

        # ------ Nomi squadre ------
        title = soup.find("title")
        if title:
            m = re.match(r"^(.+?) vs (.+?) ", title.get_text())
            if m:
                result["home_name"] = m.group(1).strip()
                result["away_name"] = m.group(2).strip()

        # ------ Summary forma (ultime 10) ------
        # Pattern: "7V-1N-2P nelle ultime 10 partite, con 33 gol segnati e 12 subiti.
        #           Media gol: 3.3 fatti, 1.2 subiti. Vittorie 70%, gol Over 90%"
        summaries = re.findall(
            r"(\d+V-\d+N-\d+P nelle ultime \d+ partite,[^\n]+)",
            text,
        )
        if len(summaries) >= 1:
            result["home_form_summary"] = summaries[0].strip()
        if len(summaries) >= 2:
            result["away_form_summary"] = summaries[1].strip()

        # ------ Over 2.5% ------
        # "Gol totali 2.5\nOver\n90%\n...\nUnder\n10%"
        over25_pcts = re.findall(r"Gol totali 2\.5\s+Over\s+(\d+)%", text)
        if len(over25_pcts) >= 1:
            result["home_over25_pct"] = int(over25_pcts[0]) / 100
        if len(over25_pcts) >= 2:
            result["away_over25_pct"] = int(over25_pcts[1]) / 100

        # ------ Media gol ------
        # "Media gol: 3.3 fatti, 1.2 subiti"
        avg_goals = re.findall(r"Media gol:\s*([\d.]+) fatti,\s*([\d.]+) subiti", text)
        if len(avg_goals) >= 1:
            result["home_avg_goals_scored"] = float(avg_goals[0][0])
            result["home_avg_goals_conceded"] = float(avg_goals[0][1])
        if len(avg_goals) >= 2:
            result["away_avg_goals_scored"] = float(avg_goals[1][0])
            result["away_avg_goals_conceded"] = float(avg_goals[1][1])

        # ------ Win% ------
        win_pcts = re.findall(r"Vittorie (\d+)%", text)
        if len(win_pcts) >= 1:
            result["home_win_pct"] = int(win_pcts[0]) / 100
        if len(win_pcts) >= 2:
            result["away_win_pct"] = int(win_pcts[1]) / 100

        # ------ Corner Over% ------
        # "Corner totali 9.5\nOver\n40%"
        corner_pcts = re.findall(r"Corner totali [\d.]+\s+Over\s+(\d+)%", text)
        if len(corner_pcts) >= 1:
            result["home_corner_over_pct"] = int(corner_pcts[0]) / 100
        if len(corner_pcts) >= 2:
            result["away_corner_over_pct"] = int(corner_pcts[1]) / 100

        # ------ Pronostico TotalCorner ------
        # "Pronostici calcio: Gol Over 2.5, Corner Under 9.5, Polissya Zhytomyr -1.0"
        pred_m = re.search(r"Pronostici calcio:\s*([^\n(]+)", text)
        if pred_m:
            result["prediction"] = pred_m.group(1).strip()

        # ------ Note testuali ------
        # "La squadra casa non ha vinto in 10 delle ultime 12 partite"
        notes = re.findall(
            r"(La squadra (?:casa|trasferta)[^\n]{10,120})",
            text,
        )
        result["notes"] = list(dict.fromkeys(notes))  # dedup mantenendo ordine

        # ------ Quote di riferimento ------
        # "1.44\n4.00\n5.75" (ordine: 1, X, 2)
        odds_raw = re.findall(r"\b(\d+\.\d{2})\b", text[:2000])
        if len(odds_raw) >= 3:
            result["odds_ref"] = {
                "home": float(odds_raw[0]),
                "draw": float(odds_raw[1]),
                "away": float(odds_raw[2]),
            }

        # ------ Media complessiva Over 2.5 ------
        h = result.get("home_over25_pct")
        a = result.get("away_over25_pct")
        if h is not None and a is not None:
            result["avg_over25_pct"] = round((h + a) / 2, 3)

        # ------ Media gol attesa (Poisson input) ------
        hs = result.get("home_avg_goals_scored", 0)
        ac = result.get("away_avg_goals_conceded", 0)
        as_ = result.get("away_avg_goals_scored", 0)
        hc = result.get("home_avg_goals_conceded", 0)
        if hs and ac:
            result["expected_home_goals"] = round((hs + ac) / 2, 2)
        if as_ and hc:
            result["expected_away_goals"] = round((as_ + hc) / 2, 2)

        return result

    # ------------------------------------------------------------------
    # Search match by team names
    # ------------------------------------------------------------------

    def search_match(
        self,
        home: str,
        away: str,
        match_date: date | None = None,
    ) -> dict | None:
        """
        Cerca una partita nella lista di oggi per nomi squadra.
        Ritorna la prima corrispondenza con similarità ≥ 0.5, None se non trovata.
        """
        try:
            today = self.today_matches(match_date)
        except Exception:
            return None

        best_score = 0.0
        best_match = None

        for m in today:
            h_slug = m["home_slug"].replace("-", " ")
            a_slug = m["away_slug"].replace("-", " ")
            score = (
                _name_similarity(home, h_slug) +
                _name_similarity(away, a_slug)
            ) / 2

            if score > best_score:
                best_score = score
                best_match = m

        if best_score >= 0.4:
            return best_match
        return None

    # ------------------------------------------------------------------
    # Main collect
    # ------------------------------------------------------------------

    def collect(
        self,
        home: str,
        away: str,
        match_date: date | None = None,
    ) -> dict:
        """
        Raccoglie le statistiche TotalCorner per una partita.

        Strategia:
          1. Cerca nella lista partite di oggi per nome squadra
          2. Se trovata → fetch stats page
          3. Se non trovata → costruisce URL da slugify dei nomi e prova direttamente
             (richiede match_id che non abbiamo → ritorna found=False)
        """
        entry = self.search_match(home, away, match_date)

        if entry:
            return self.match_stats(
                match_id=entry["id"],
                home_slug=entry["home_slug"],
                away_slug=entry["away_slug"],
            )

        # Fallback: nessuna partita trovata oggi
        return {
            "found": False,
            "home": home,
            "away": away,
            "date": match_date.isoformat() if match_date else None,
            "note": "Partita non trovata su TotalCorner (oggi). Potrebbe non essere disponibile.",
        }

    # ------------------------------------------------------------------
    # Format for LLM prompt
    # ------------------------------------------------------------------

    def format_for_prompt(self, data: dict) -> str:
        """
        Formatta i dati TotalCorner come testo per il prompt del Sesto Senso.
        """
        if not data.get("found"):
            return ""

        lines = ["=== TOTALCORNER — STATISTICHE STORICHE ==="]

        home = data.get("home_name", "Casa")
        away = data.get("away_name", "Trasferta")

        # Forma recente
        if s := data.get("home_form_summary"):
            lines.append(f"[{home}] {s}")
        if s := data.get("away_form_summary"):
            lines.append(f"[{away}] {s}")

        # Over 2.5
        h25 = data.get("home_over25_pct")
        a25 = data.get("away_over25_pct")
        avg25 = data.get("avg_over25_pct")
        if h25 is not None:
            lines.append(
                f"Over 2.5 gol: {home} {int(h25*100)}% | "
                f"{away} {int(a25*100) if a25 else '?'}% | "
                f"Media {int(avg25*100) if avg25 else '?'}%"
            )

        # Gol attesi
        exp_h = data.get("expected_home_goals")
        exp_a = data.get("expected_away_goals")
        if exp_h and exp_a:
            lines.append(f"Gol attesi (media storica): {home} {exp_h} | {away} {exp_a} | Totale {round(exp_h+exp_a,2)}")

        # Corner
        hc = data.get("home_corner_over_pct")
        ac = data.get("away_corner_over_pct")
        if hc is not None:
            lines.append(
                f"Corner Over 9.5: {home} {int(hc*100)}% | {away} {int(ac*100) if ac else '?'}%"
            )

        # Pronostico
        if pred := data.get("prediction"):
            lines.append(f"Pronostico TotalCorner: {pred}")

        # Note
        for note in data.get("notes", [])[:4]:
            lines.append(f"⚠ {note}")

        return "\n".join(lines)

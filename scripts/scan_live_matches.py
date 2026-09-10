#!/usr/bin/env python3
"""
scripts/scan_live_matches.py — Live Value & Momentum Scanner BAgent (Regole #33, #40, #41, #42, #43).

Scansiona in tempo reale TUTTE le partite LIVE in corso nel mondo:
1. Acquisisce minuto di gioco, punteggio ed eventi live (espulsioni, cartellini, gol).
2. Estrae le statistiche di pressione (Tiri in Porta, Possesso, Corner, Falli).
3. Scarica le quote reali live da API-Football (/odds/live).
4. Calcola il decadimento temporale (Poisson residuo) e identifica l'Edge live.
5. Filtra trappole e seleziona i veri Sweet Spot in-play (Late Goal, Assedio Corner, Copertura).

Uso:
    python scripts/scan_live_matches.py
    python scripts/scan_live_matches.py --fixture 1575465
"""

from __future__ import annotations
import os
import sys
import math
import requests
import argparse
from typing import Dict, List, Any, Optional
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if "=" in line and not line.startswith("#") and line.strip():
            k, _, v = line.partition("=")
            if k.strip() and v.strip():
                os.environ.setdefault(k.strip(), v.strip())

API_KEY = os.getenv("API_FOOTBALL_KEY", "")
API_HOST = "v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}


def get_live_fixtures() -> List[Dict[str, Any]]:
    url = f"https://{API_HOST}/fixtures?live=all"
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code == 200:
            return r.json().get("response", [])
    except Exception as e:
        print(f"Errore recupero live fixtures: {e}")
    return []


def get_fixture_stats(fid: int) -> Dict[str, Dict[str, Any]]:
    url = f"https://{API_HOST}/fixtures/statistics?fixture={fid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            res = r.json().get("response", [])
            stats = {}
            for t_item in res:
                t_name = t_item.get("team", {}).get("name", "")
                t_stats = {s.get("type"): s.get("value") for s in t_item.get("statistics", [])}
                stats[t_name] = t_stats
            return stats
    except Exception:
        pass
    return {}


def get_live_odds(fid: int) -> List[Dict[str, Any]]:
    url = f"https://{API_HOST}/odds/live?fixture={fid}"
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code == 200:
            res = r.json().get("response", [])
            if res:
                return res[0].get("odds", [])
    except Exception:
        pass
    return []


def analyze_live_match(f: Dict[str, Any]):
    fid = f.get("fixture", {}).get("id")
    league = f.get("league", {}).get("name", "")
    country = f.get("league", {}).get("country", "")
    h_name = f.get("teams", {}).get("home", {}).get("name", "")
    a_name = f.get("teams", {}).get("away", {}).get("name", "")
    el = f.get("fixture", {}).get("status", {}).get("elapsed", 0)
    st = f.get("fixture", {}).get("status", {}).get("short", "")
    gh = f.get("goals", {}).get("home", 0) or 0
    ga = f.get("goals", {}).get("away", 0) or 0
    tot_g = gh + ga

    # Ignora partite finite o senza minuti
    if st in ["FT", "AET", "PEN", "TBD", "NS"]:
        return

    print(f"\n{'='*85}")
    print(f"🔴 LIVE MATCH: {h_name} {gh} - {ga} {a_name} ({el}' {st}) — {country}: {league} [ID #{fid}]")
    print(f"{'='*85}")

    # Statistiche di pressione
    stats = get_fixture_stats(fid)
    h_shots_ot = stats.get(h_name, {}).get("Shots on Goal") or 0
    a_shots_ot = stats.get(a_name, {}).get("Shots on Goal") or 0
    h_corners = stats.get(h_name, {}).get("Corner Kicks") or 0
    a_corners = stats.get(a_name, {}).get("Corner Kicks") or 0
    h_poss = str(stats.get(h_name, {}).get("Ball Possession") or "50%")
    a_poss = str(stats.get(a_name, {}).get("Ball Possession") or "50%")

    print(f"📊 Pressione Live: Possesso {h_poss} vs {a_poss} | Tiri Porta: {h_shots_ot} - {a_shots_ot} | Corner: {h_corners} - {a_corners}")

    # Scarica quote live
    live_bets = get_live_odds(fid)
    if not live_bets:
        print("⏳ Quote live bookmaker temporaneamente sospese o non disponibili su questo feed.")
        return

    # Minuti residui
    mins_rem = max(3, 90 - (el or 45))
    if el and el > 85:
        mins_rem = max(4, 95 - el)

    print(f"⏱️  Minuti residui stimati: ~{mins_rem} min")

    # Mappatura opportunità live chiave
    opportunities = []

    for bet in live_bets:
        b_name = bet.get("name", "")
        b_id = bet.get("id")
        vals = bet.get("values", [])

        # 1. Over/Under totale gol
        if "Over/Under" in b_name or "Match Goals" in b_name or b_id in [5, 49]:
            for v in vals:
                v_type = v.get("value")
                odd = float(v.get("odd") or 0.0)
                handicap = v.get("handicap")
                suspended = v.get("suspended", False)
                if suspended or odd < 1.20:
                    continue

                if v_type == "Over" and handicap:
                    try:
                        line = float(handicap)
                        # Se è la linea immediatamente sopra il punteggio attuale (es. 2-1 -> Over 3.5)
                        if line == tot_g + 0.5:
                            # Stima gol residuo basata su intensità e minuti
                            shot_tempo = (h_shots_ot + a_shots_ot) / max(1, (el / 45))
                            lambda_rem = (mins_rem / 90.0) * max(0.8, 0.4 * shot_tempo)
                            p_another_goal = 1.0 - math.exp(-lambda_rem)
                            edge = (p_another_goal * odd) - 1.0

                            opportunities.append({
                                "type": "GOAL_LIVE",
                                "market": f"Over {line} Gol Totali (Altro Gol nei restanti {mins_rem}')",
                                "odd": odd,
                                "prob": p_another_goal,
                                "edge": edge,
                                "notes": f"Pressione tiri: {h_shots_ot+a_shots_ot} totali. P_reale stima gol: {p_another_goal*100:.1f}%"
                            })
                    except Exception:
                        pass

        # 2. Corner live
        if "Corner" in b_name and ("Over" in str(vals) or "Handicap" in b_name):
            for v in vals:
                v_type = str(v.get("value"))
                odd = float(v.get("odd") or 0.0)
                handicap = v.get("handicap")
                suspended = v.get("suspended", False)
                if not suspended and "Over" in v_type and 1.30 <= odd <= 2.20 and handicap:
                    try:
                        c_line = float(handicap)
                        tot_c = h_corners + a_corners
                        if c_line >= tot_c:
                            c_needed = c_line - tot_c
                            # Tasso corner stimato
                            c_rate = (tot_c / max(10, el)) * mins_rem
                            p_corner = 1.0 - sum((c_rate**k * math.exp(-c_rate)/math.factorial(k)) for k in range(int(c_needed) + 1)) if c_rate > 0 else 0.5
                            edge_c = (p_corner * odd) - 1.0
                            if edge_c > 0.03:
                                opportunities.append({
                                    "type": "CORNER_LIVE",
                                    "market": f"Corner Live Over {c_line} (Attuali: {tot_c})",
                                    "odd": odd,
                                    "prob": p_corner,
                                    "edge": edge_c,
                                    "notes": f"Ritmo corner: {tot_c} in {el}'. Servono {c_needed+0.5:.0f} corner nei restanti {mins_rem}'."
                                })
                    except Exception:
                        pass

    # Ordina opportunità live per edge
    opportunities.sort(key=lambda x: x["edge"], reverse=True)

    if opportunities:
        print(f"\n💡 OPPORTUNITÀ LIVE IDENTIFICATE ({len(opportunities)} con valore):")
        for o in opportunities[:3]:
            tag = "⭐ TOP VALUE" if o["edge"] >= 0.10 else "👀 VALUE"
            print(f"   • [{tag}] {o['market']} @ quota {o['odd']:.2f}")
            print(f"     P_reale stimata: {o['prob']*100:.1f}% | Edge: {o['edge']*100:+.1f}%")
            print(f"     Motivazione: {o['notes']}")
    else:
        print("⏸️  Nessun disallineamento di quota significativo o quote sospese dai bookmaker al momento.")


def main():
    parser = argparse.ArgumentParser(description="Scanner Opportunità Live Betting BAgent")
    parser.add_argument("--fixture", type=int, help="ID Fixture specifica da analizzare")
    args = parser.parse_args()

    print("\n" + "="*85)
    print("📡 AVVIO SCANNER ONNIMERCATO LIVE BETTING (IN-PLAY RADAR)")
    print("="*85)

    if args.fixture:
        url = f"https://{API_HOST}/fixtures?id={args.fixture}"
        r = requests.get(url, headers=HEADERS, timeout=10)
        res = r.json().get("response", [])
        if res:
            analyze_live_match(res[0])
        else:
            print("Fixture non trovata.")
    else:
        live_list = get_live_fixtures()
        print(f"Trovate {len(live_list)} partite in corso nel mondo.")
        for f in live_list:
            analyze_live_match(f)

    print("\n" + "="*85 + "\n")


if __name__ == "__main__":
    main()

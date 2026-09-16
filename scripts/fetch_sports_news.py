#!/usr/bin/env python3
"""
scripts/fetch_sports_news.py — Rassegna Stampa & Know-How Specialistico Multi-Lega (Regola #59).

Estrae e analizza in tempo reale gli articoli integrali dai principali quotidiani sportivi 
(Gazzetta, Marca, AS, The Athletic, BBC Sport, Kicker, L'Équipe, A Bola, ecc.) per alimentare
il Sesto Senso con know-how tattico, indiscrezioni di spogliatoio e conferenze stampa.

Uso:
    python scripts/fetch_sports_news.py --home "Milan" --away "Benfica" --league "Champions League"
    python scripts/fetch_sports_news.py --home "Barcelona" --away "Racing Santander" --league "LaLiga"
    python scripts/fetch_sports_news.py --team "Arsenal" --league "Premier League"
"""

from __future__ import annotations
import sys
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.football.external.sources.news import SixthSenseNewsCollector, get_league_config


def main():
    parser = argparse.ArgumentParser(description="Estrattore di Intelligence Giornalistica per il Sesto Senso")
    parser.add_argument("--home", type=str, help="Squadra di casa")
    parser.add_argument("--away", type=str, help="Squadra ospite")
    parser.add_argument("--team", type=str, help="Singola squadra")
    parser.add_argument("--league", type=str, default="Serie A", help="Lega o competizione (es. Serie A, Premier League, LaLiga, Champions League)")
    parser.add_argument("--max-results", type=int, default=6, help="Numero max di articoli per sezione")

    args = parser.parse_args()

    collector = SixthSenseNewsCollector()

    if args.team:
        print(f"\n=======================================================")
        print(f"📰 RASSEGNA STAMPA SPECIALIZZATA: {args.team.upper()} ({args.league})")
        print(f"=======================================================")
        cfg = get_league_config(args.league)
        lang = cfg["language"] if cfg else "it"
        country = cfg["country"] if cfg else "IT"
        
        articles = collector.google.search_team(args.team, language=lang, country=country, max_results=args.max_results)
        print(f"\n📋 Trovati {len(articles)} articoli dai quotidiani di riferimento:")
        for idx, a in enumerate(articles, 1):
            print(f"\n[{idx}] {a.title}")
            print(f"    🗞️ Fonte: {a.source} | Data: {a.published_at or 'Oggi'}")
            if a.snippet:
                print(f"    📝 Estratto: {a.snippet}")
            print(f"    🔗 Link: {a.url}")
        return

    if not args.home or not args.away:
        print("❌ Specificare --home e --away (o --team per singola squadra).")
        sys.exit(1)

    print(f"\n=======================================================")
    print(f"📰 SESTO SENSO: RASSEGNA STAMPA INTEGRALE & KNOW-HOW")
    print(f"🏟️  Match: {args.home} vs {args.away} | Torneo: {args.league}")
    print(f"=======================================================")

    bundle = collector.collect(
        home=args.home,
        away=args.away,
        league=args.league,
        max_per_team=args.max_results
    )

    print(f"\n🔍 Totale Articoli Rilevati: {bundle['total_articles']}")
    if bundle.get("league_source"):
        print(f"🌐 Fonti Quotidiane Primarie: {bundle['league_source']}")

    sections = [
        (f"🏆 FOCUS PRE-PARTITA ({args.home} vs {args.away})", bundle["articles"]["match"]),
        (f"🔵 FOCUS SPOGLIATOIO & TATTICA: {args.home.upper()}", bundle["articles"]["home_team"]),
        (f"🔴 FOCUS SPOGLIATOIO & TATTICA: {args.away.upper()}", bundle["articles"]["away_team"]),
    ]

    for title, articles in sections:
        if not articles:
            continue
        print(f"\n-------------------------------------------------------")
        print(f"{title} ({len(articles)} articoli)")
        print(f"-------------------------------------------------------")
        for idx, a in enumerate(articles[:args.max_results], 1):
            print(f"[{idx}] {a['title']}")
            print(f"    🗞️ Fonte: {a['source']} | 📅 {a.get('published_at', 'Oggi')}")
            if a.get("snippet"):
                print(f"    📝 {a['snippet']}")
            print(f"    🔗 {a['url']}")

    print(f"\n=======================================================")
    print(f"✅ Rassegna stampa completata. Know-how pronto per l'analisi.")
    print(f"=======================================================\n")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
scripts/test_sportmicro_status.py — Test Rapido Connessione Sportmicro / PostgreSQL.

Esegui direttamente dal terminale:
    python scripts/test_sportmicro_status.py
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_KEY = os.getenv("SPORTMICRO_API_KEY", "").strip()

print("=" * 75)
print("🔍 TEST STATO SERVER SPORTMICRO (PostgREST / PostgreSQL)")
print("=" * 75)

if not API_KEY:
    print("❌ ERRORE: SPORTMICRO_API_KEY non trovata nel file .env!")
    sys.exit(1)

print(f"🔑 Chiave caricata: {API_KEY[:4]}...{API_KEY[-4:]}")
print(f"🌐 Host di riferimento: https://football.sportmicro.com\n")

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "User-Agent": "BAgent-Diagnostic/1.0",
}

endpoints_to_test = [
    ("/countries?limit=1", "Paesi e Federazioni"),
    ("/matches?limit=1", "Partite Recenti"),
    ("/odds/bookmakers?limit=1", "Catalogo Bookmaker"),
    ("/odds/to-score-in-both-halves?limit=1", "Mercato 'Segna Entrambi i Tempi'"),
]

for endpoint, description in endpoints_to_test:
    url = f"https://football.sportmicro.com{endpoint}"
    print(f"👉 Test: {description} ({endpoint})")
    try:
        r = requests.get(url, headers=headers, timeout=6)
        print(f"   HTTP Status: {r.status_code}")
        if r.status_code == 200:
            print(f"   🟢 RISPOSTA OK! Server operativo.")
            print(f"   Dati ricevuti: {r.text[:120]}...\n")
        elif r.status_code == 500:
            print(f"   🔴 ERRORE 500 (Database PostgreSQL non raggiungibile):")
            print(f"   Messaggio dal server: {r.text.strip()}\n")
        else:
            print(f"   ⚠️ Risposta anomala {r.status_code}: {r.text[:150]}\n")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Errore di rete / Timeout: {e}\n")

print("=" * 75)
print("💡 Se vedi '57P03: the database system is shutting down' o 'No suitable host',")
print("   il cluster PostgreSQL remoto di Sportmicro è temporaneamente in manutenzione.")
print("   Riprova tra qualche minuto!")
print("=" * 75)

import json
from pathlib import Path

snai_dir = Path("reports/snai")

def verify_leg(filename, market_name_part, selection):
    path = snai_dir / filename
    if not path.exists():
        return False, f"File {filename} non esiste"
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    for m in d.get("markets", []):
        full_market = f"{m.get('market', '')} {m.get('line', '')}".strip()
        if market_name_part.upper() in full_market.upper():
            for o in m.get("outcomes", []):
                if selection.upper() == o.get("selection", "").upper():
                    return True, full_market, o.get("selection"), float(o.get("odds", 0))
    return False, f"Non trovato in {filename}: {market_name_part} | {selection}"

portfolio = [
    # Ticket 1
    ("T1", "italia-turchia.json", "MARCATORE PIÙ ULTRA SCAMACCA", "SI"),
    ("T1", "francia-belgio.json", "MULTIGOAL SQUADRA 1", "1-3"),
    ("T1", "romania-svezia.json", "1 TEMPO: 1X2 CORNER", "2"),
    ("T1", "irlanda-del-nord-georgia.json", "COMBO CHANCE: 1 O NOGOAL", "1 O NOGOAL"),
    
    # Ticket 2
    ("T2", "italia-turchia.json", "CELIK ZEKI U/O 1.5 FALLI COMMESSI", "OVER"),
    ("T2", "bosnia-erzegovina-polonia.json", "MULTIGOAL TEMPO 1", "1-3"),
    ("T2", "montenegro-armenia.json", "1X2 CORNER CALCI ANGOLO 1X2 T.R.", "1"),
    ("T2", "ucraina-ungheria.json", "U/O 3.5 PUNTI CARTELLINI", "OVER"),
    
    # Ticket 3
    ("T3", "croazia-spagna.json", "MARCATORE PIÙ ULTRA YAMAL", "SI"),
    ("T3", "inghilterra-repubblica-ceca.json", "PRIMA A 6 CALCI D'ANGOLO", "TEAM 1"),
    ("T3", "svizzera-macedonia.json", "MULTIGOAL SQUADRA 1", "1-3"),
    ("T3", "albania-san-marino.json", "PRIMA A 6 CALCI D'ANGOLO", "TEAM 1"),
    
    # Ticket 4
    ("T4", "kazakistan-isole-far-oer.json", "MULTIGOAL SQUADRA 1", "1-3"),
    ("T4", "croazia-spagna.json", "1X2 PUNTI CARTELLINI", "1"),
    ("T4", "inghilterra-repubblica-ceca.json", "1X2 PUNTI CARTELLINI", "2"),
    ("T4", "moldova-slovacchia.json", "PRIMA A 5 CALCI D'ANGOLO", "TEAM 2"),
    
    # Ticket 5
    ("T5", "scozia-slovenia.json", "1X2 CORNER CALCI ANGOLO 1X2 T.R.", "1"),
    ("T5", "lussemburgo-bulgaria.json", "MULTIGOAL SQUADRA 1", "1-3"),
    ("T5", "bielorussia-finlandia.json", "DOPPIA CHANCE MULTIESITI", "X2"),
    ("T5", "estonia-islanda.json", "MULTIGOAL SQUADRA 2", "1-3")
]

print("=== VERIFICA COMPLETA DELLE 20 SELEZIONI SUI CATALOGHI REALI SNAI ===")
all_ok = True
ticket_odds = {}
for ticket, fn, mk, sel in portfolio:
    res = verify_leg(fn, mk, sel)
    if res[0]:
        print(f"[{ticket}] OK | {fn} | {res[1]} -> '{res[2]}' @ {res[3]}")
        ticket_odds[ticket] = ticket_odds.get(ticket, 1.0) * res[3]
    else:
        print(f"[{ticket}] ERRORE: {res[1]}")
        all_ok = False

print("\n--- QUOTE TOTALI PER TICKET ---")
for t, odd in ticket_odds.items():
    print(f"{t}: Quota {round(odd, 2)} | Ritorno su 2.50 EUR = {round(odd * 2.50, 2)} EUR")

print(f"\nEsito complessivo: {'TUTTO VERIFICATO CON SUCCESSO' if all_ok else 'PRESENTI ERRORI'}")

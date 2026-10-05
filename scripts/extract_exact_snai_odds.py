import json
from pathlib import Path
import sys

ROOT = Path("C:/Project/BAgent")
sys.path.insert(0, str(ROOT))

from services.analysis.xg_poisson_engine import QuantitativeEngine

engine = QuantitativeEngine(rho=-0.05)
snai_dir = Path("reports/snai")

def get_market_odd(file_name, target_keywords):
    path = snai_dir / file_name
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    
    markets = data.get("markets", [])
    candidates = []
    
    for m in markets:
        m_name = m.get("market", "")
        line = m.get("line", "")
        m_full = f"{m_name} {line}".strip()
        
        # Check matching keywords
        for target, target_sel in target_keywords:
            if target.upper() in m_full.upper():
                for o in m.get("outcomes", []):
                    sel = o.get("selection", "")
                    if target_sel.upper() == sel.upper() or (target_sel.upper() in sel.upper() and len(sel) < 15):
                        odds = o.get("odds")
                        if odds:
                            candidates.append({
                                "market_name": m_full,
                                "selection": sel,
                                "odds": float(odds)
                            })
    return candidates

# Let's inspect options for all 17 matches
matches_config = [
    # STASERA 05/10 (7 partite)
    ("italia-turchia.json", "Italia vs Turchia", 2.05, 0.80, [
        ("DOPPIA CHANCE + MULTIGOAL", "1X + 1-4"),
        ("1X + MULTIGOAL", "1X + 1-4"),
        ("COMBO: 1X2 + U/O", "1 + U"),
        ("COMBO CHANCE: 1 O UNDER", "SI"),
        ("UNDER/OVER", "UNDER 3.5"),
        ("UNDER/OVER", "OVER 1.5")
    ]),
    ("francia-belgio.json", "Francia vs Belgio", 1.75, 1.05, [
        ("DOPPIA CHANCE + MULTIGOAL", "1X + 1-4"),
        ("COMBO: 1X2 + U/O", "1X + O"),
        ("COMBO CHANCE: 1 O OVER", "SI"),
        ("UNDER/OVER", "OVER 1.5"),
        ("MULTIGOAL", "1-4")
    ]),
    ("romania-svezia.json", "Romania vs Svezia", 1.00, 1.65, [
        ("DOPPIA CHANCE + MULTIGOAL", "X2 + 1-5"),
        ("DOPPIA CHANCE + MULTIGOAL", "X2 + 1-4"),
        ("1X2 CORNER", "2"),
        ("UNDER/OVER", "UNDER 3.5"),
        ("DOPPIA CHANCE", "X2")
    ]),
    ("ucraina-ungheria.json", "Ucraina vs Ungheria", 1.25, 0.95, [
        ("UNDER/OVER", "UNDER 3.5"),
        ("COMBO CHANCE: 1 O UNDER", "SI"),
        ("MULTIGOAL", "1-3"),
        ("MULTIGOAL", "1-4")
    ]),
    ("bosnia-erzegovina-polonia.json", "Bosnia Erzegovina vs Polonia", 1.15, 1.35, [
        ("UNDER/OVER", "UNDER 3.5"),
        ("MULTIGOAL", "1-3"),
        ("MULTIGOAL", "1-4"),
        ("COMBO CHANCE: 2 O UNDER", "SI")
    ]),
    ("irlanda-del-nord-georgia.json", "Irlanda del Nord vs Georgia", 1.10, 1.05, [
        ("UNDER/OVER", "UNDER 3.5"),
        ("DOPPIA CHANCE", "1X"),
        ("COMBO CHANCE: 1 O UNDER", "SI"),
        ("MULTIGOAL", "1-3")
    ]),
    ("montenegro-armenia.json", "Montenegro vs Armenia", 1.55, 0.85, [
        ("DOPPIA CHANCE + MULTIGOAL", "1X + 1-4"),
        ("COMBO: 1X2 + U/O", "1X + U"),
        ("COMBO CHANCE: 1 O UNDER", "SI"),
        ("UNDER/OVER", "UNDER 3.5"),
        ("DOPPIA CHANCE", "1X")
    ]),
    
    # DOMANI 06/10 (10 partite)
    ("croazia-spagna.json", "Croazia vs Spagna", 1.00, 1.90, [
        ("DOPPIA CHANCE", "X2"),
        ("DOPPIA CHANCE + MULTIGOAL", "X2 + 1-4"),
        ("UNDER/OVER", "UNDER 3.5"),
        ("COMBO CHANCE: 2 O OVER", "SI")
    ]),
    ("inghilterra-repubblica-ceca.json", "Inghilterra vs Repubblica Ceca", 2.30, 0.65, [
        ("DOPPIA CHANCE", "1X"),
        ("DOPPIA CHANCE + MULTIGOAL", "1X + 1-4"),
        ("MULTIGOAL CASA", "1-3"),
        ("UNDER/OVER", "UNDER 4.5")
    ]),
    ("svizzera-macedonia.json", "Svizzera vs Macedonia del Nord", 2.10, 0.60, [
        ("DOPPIA CHANCE", "1X"),
        ("DOPPIA CHANCE + MULTIGOAL", "1X + 1-4"),
        ("UNDER/OVER", "UNDER 4.5")
    ]),
    ("albania-san-marino.json", "Albania vs San Marino", 3.10, 0.20, [
        ("DOPPIA CHANCE + MULTIGOAL", "1X + 2-5"),
        ("UNDER/OVER", "OVER 1.5"),
        ("MULTIGOAL CASA", "2-5")
    ]),
    ("kazakistan-isole-far-oer.json", "Kazakistan vs Isole Far Oer", 1.25, 0.90, [
        ("DOPPIA CHANCE", "1X"),
        ("UNDER/OVER", "UNDER 3.5"),
        ("MULTIGOAL", "1-3")
    ]),
    ("bielorussia-finlandia.json", "Bielorussia vs Finlandia", 0.95, 1.35, [
        ("DOPPIA CHANCE", "X2"),
        ("UNDER/OVER", "UNDER 3.5"),
        ("DOPPIA CHANCE + MULTIGOAL", "X2 + 1-5")
    ]),
    ("lussemburgo-bulgaria.json", "Lussemburgo vs Bulgaria", 1.15, 1.10, [
        ("UNDER/OVER", "UNDER 3.5"),
        ("MULTIGOAL", "1-3"),
        ("DOPPIA CHANCE", "1X")
    ]),
    ("moldova-slovacchia.json", "Moldova vs Slovacchia", 0.70, 1.70, [
        ("DOPPIA CHANCE", "X2"),
        ("UNDER/OVER", "UNDER 3.5"),
        ("DOPPIA CHANCE + MULTIGOAL", "X2 + 1-5")
    ]),
    ("scozia-slovenia.json", "Scozia vs Slovenia", 1.45, 0.95, [
        ("DOPPIA CHANCE", "1X"),
        ("UNDER/OVER", "UNDER 3.5"),
        ("MULTIGOAL", "1-3")
    ]),
    ("estonia-islanda.json", "Estonia vs Islanda", 0.85, 1.55, [
        ("DOPPIA CHANCE", "X2"),
        ("UNDER/OVER", "UNDER 3.5"),
        ("DOPPIA CHANCE + MULTIGOAL", "X2 + 1-5")
    ]),
]

print("Scanning all 17 matches for exact SNAI lines and odds...")
for fname, m_name, lh, la, kws in matches_config:
    opts = get_market_odd(fname, kws)
    print(f"\n[{m_name}] (xG {lh:.2f} - {la:.2f})")
    if opts:
        for o in opts[:5]:
            print(f"   {o['market_name']} | Sel: {o['selection']} | Quota SNAI: {o['odds']}")
    else:
        print("   No match found with keywords.")

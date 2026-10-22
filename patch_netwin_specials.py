#!/usr/bin/env python3
"""
Patch netwin_odds_downloader.py to add special market aggregates.
Run from the BAgent root: python patch_netwin_specials.py
"""
from pathlib import Path

TARGET = Path("services/betting/netwin_odds_downloader.py")

OLD_LIST = """SECONDARY_AGGREGATES: List[int] = [
    452,   # DC + Under/Over
    1477,  # DC + MultiGol
    335,   # MultiGol
    444,   # 1X2 + Under/Over
    456,   # DC + Gol/NoGol
    459,   # Chance Mix 1X2 o Under/Over
    460,   # Chance Mix 1X2 o Gol/NoGol
    461,   # Chance Mix Gol/NoGol o Under/Over
    2846,  # Chance Mix DC o Gol/NoGol
    389,   # MultiGol Squadra Casa e Ospite
    448,   # 1X2 + Gol/NoGol
    450,   # Under/Over + Gol/NoGol
    2613,  # Draw No Bet
    341,   # 1X2 e Doppia Chance 1° Tempo
    344,   # Under/Over 1° Tempo
    345,   # Gol/NoGol 1° Tempo
    352,   # MultiGol 1° Tempo
]"""

NEW_LIST = """SECONDARY_AGGREGATES: List[int] = [
    452,   # DC + Under/Over
    1477,  # DC + MultiGol
    335,   # MultiGol
    444,   # 1X2 + Under/Over
    456,   # DC + Gol/NoGol
    459,   # Chance Mix 1X2 o Under/Over
    460,   # Chance Mix 1X2 o Gol/NoGol
    461,   # Chance Mix Gol/NoGol o Under/Over
    2846,  # Chance Mix DC o Gol/NoGol
    389,   # MultiGol Squadra Casa e Ospite
    448,   # 1X2 + Gol/NoGol
    450,   # Under/Over + Gol/NoGol
    2613,  # Draw No Bet
    341,   # 1X2 e Doppia Chance 1° Tempo
    344,   # Under/Over 1° Tempo
    345,   # Gol/NoGol 1° Tempo
    352,   # MultiGol 1° Tempo
    # Specials (tiri / corner / cartellini) — candidate IDs
    500, 501, 502, 503, 510, 520, 530, 540, 550,
    600, 610, 620, 630, 640, 650,
    700, 710, 720, 730, 740, 750,
    800, 810, 820, 830, 840, 850,
    900, 910, 920, 930, 940, 950,
    1000, 1010, 1020, 1030, 1040, 1050,
    1100, 1110, 1120, 1130,
    1200, 1210, 1220, 1230,
    1300, 1310, 1320,
    1400, 1410, 1420,
    1500, 1510, 1520,
    1600, 1610, 1620,
    1700, 1710, 1720,
    1800, 1810, 1820,
    1900, 1910, 1920,
    2000, 2010, 2020,
    2100, 2110, 2120,
    2200, 2210, 2220,
    2300, 2310, 2320,
    2400, 2410, 2420,
    2500, 2510, 2520,
    2700, 2710, 2720,
    2800, 2810, 2820,
    2900, 2910, 2920,
    3000, 3010, 3020,
]"""

SPECIAL_PARSE = """
                    # Specials: tiri / corner / cartellini
                    if any(k in desc for k in ("TIRI", "TIR", "SHOT")):
                        side = "Casa" if "CASA" in desc or "HOME" in desc else ("Ospite" if "OSP" in desc or "AWAY" in desc else "Totale")
                        label = f"Over {spread_str} Tiri {side}" if ce == 2 else (f"Under {spread_str} Tiri {side}" if ce == 1 else None)
                        if label and spread_str:
                            m["markets"].setdefault("TIRI", {})[label] = q
                    elif any(k in desc for k in ("CORNER", "ANGOLO", "ANGOLI")):
                        side = "Casa" if "CASA" in desc or "HOME" in desc else ("Ospite" if "OSP" in desc or "AWAY" in desc else "Totale")
                        label = f"Over {spread_str} Corner {side}" if ce == 2 else (f"Under {spread_str} Corner {side}" if ce == 1 else None)
                        if label and spread_str:
                            m["markets"].setdefault("CORNER", {})[label] = q
                    elif any(k in desc for k in ("CARTELLIN", "CARD", "AMMONIZ")):
                        side = "Casa" if "CASA" in desc or "HOME" in desc else ("Ospite" if "OSP" in desc or "AWAY" in desc else "Totale")
                        label = f"Over {spread_str} Cartellini {side}" if ce == 2 else (f"Under {spread_str} Cartellini {side}" if ce == 1 else None)
                        if label and spread_str:
                            m["markets"].setdefault("CARTELLINI", {})[label] = q
"""

MARKER = """                    # 17. MultiGol 1° Tempo (agg 352)
                    elif agg_id == 352 and ce == 1:
                        if "1" in desc or (h >> 16) == 1 or "1°" in desc or "1?" in desc:
                            mg_1t = decode_multigol_range(h)
                            if mg_1t:
                                m["markets"].setdefault("PRIMO_TEMPO", {})[f"MultiGol {mg_1t} 1° Tempo"] = q
"""

def main():
    if not TARGET.exists():
        print(f"ERROR: {TARGET} not found. Run from BAgent root.")
        return
    text = TARGET.read_text(encoding="utf-8")
    if OLD_LIST not in text:
        print("WARNING: expected SECONDARY_AGGREGATES block not found. File may already be patched or modified.")
        return
    text = text.replace(OLD_LIST, NEW_LIST, 1)
    if MARKER not in text:
        print("WARNING: MultiGol 1° Tempo marker not found. Parsing block not inserted.")
    else:
        text = text.replace(MARKER, MARKER + SPECIAL_PARSE, 1)
    TARGET.write_text(text, encoding="utf-8")
    print(f"Patched {TARGET}")
    print("Now run: python scripts/download_netwin_odds.py --tournament \"Europa League\"")

if __name__ == "__main__":
    main()

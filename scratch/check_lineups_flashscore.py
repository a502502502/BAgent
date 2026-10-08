import requests
import json

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
    'x-fsign': 'SW9D1eZo',
}

base_url = "https://local-global.flashscore.ninja/2/x/feed"

for mid, name in [("86Wob8La", "HJK vs VPS"), ("GWZgdnjC", "KuPS vs AC Oulu")]:
    print("=" * 80)
    print(f"CHECKING {name} (Flashscore mid: {mid})")
    
    # 1. Lineups
    url_li = f"{base_url}/df_li_1_{mid}"
    r_li = requests.get(url_li, headers=headers, timeout=10)
    has_lineups = False
    if r_li.status_code == 200 and len(r_li.text) > 100:
        has_lineups = True
        # Extract players
        print(f"  Lineup feed received! Length: {len(r_li.text)}")
        # Parse names: SA÷... or names in feed
        names = []
        for part in r_li.text.split("¬"):
            if "÷" in part:
                k, v = part.split("÷", 1)
                if k in ["SA", "SB", "AC", "AD", "PH", "PI", "PJ"]:
                    names.append(f"{k}:{v}")
        print("  Sample lineup tokens:", names[:20])
    else:
        print(f"  Lineup not yet published (status {r_li.status_code}, len {len(r_li.text)})")

    # 2. Match details / live odds
    url_det = f"{base_url}/df_dos_1_{mid}"
    r_det = requests.get(url_det, headers=headers, timeout=10)
    if r_det.status_code == 200:
        print(f"  Odds/Details received (len {len(r_det.text)})")
        odds_tokens = [p for p in r_det.text.split("¬") if any(c.isdigit() for c in p)][:10]
        print("  Odds sample:", odds_tokens[:6])

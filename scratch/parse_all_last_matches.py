import urllib.request
import sys
import re

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "x-fsign": "SW9D1eZo"
}

matches = [
    ("zozyFe7t", "FC Osaka", "Ehime", "J3 League"),
    ("GCRJUNLs", "Geylang", "Tanjong Pagar", "Singapore PL"),
    ("6XvSfU5M", "Shan United", "Ezra FC", "ASEAN Champ."),
    ("lUcYV8vR", "Dynamo Kyiv", "Epitsentr", "Ucraina PL"),
    ("MFaDS7IO", "AS Roma U20", "Como U20", "Primavera 1"),
    ("lAyh7wXH", "FC Ballkani", "Dukagjini", "Kosovo Superliga"),
    ("p0q4Qn2l", "Shakhtar", "Ch. Odesa", "Ucraina PL"),
    ("QPisJZtH", "U. Cluj", "Otelul", "Romania Superliga"),
    ("G4LSyG5D", "Al Shamal", "Al Ittihad", "AFC Champions"),
    ("rFwuw4qS", "Como", "Parma", "Serie A"),
    ("dxQcraL7", "Torino", "Roma", "Serie A"),
    ("nBSIVLy2", "Inter", "Udinese", "Serie A"),
    ("r5HQ6xTH", "Bodo/Glimt", "Sandefjord", "Norvegia Eliteserien"),
    ("llKk8XsI", "Gaziantep", "Fenerbahce", "Turchia Super Lig"),
    ("hdqa7PVb", "Villarreal", "Betis", "LaLiga"),
    ("Q1TGrNGq", "Leeds", "Newcastle", "Premier League"),
    ("zorKqtLb", "Braga", "Estoril", "Liga Portugal"),
    ("8GAxJvHk", "Flamengo", "Corinthians", "Brasileirao")
]

def parse_last_matches(content, team_name):
    # Search for section "Last matches: Team"
    res = []
    sections = content.split("~KB÷")
    for sec in sections:
        lines = sec.split("~")
        header = lines[0]
        if f"Last matches: {team_name}" in header:
            for l in lines[1:6]:
                # find pattern team score
                # e.g. KJ÷*Como¬KL÷4:1
                parts = dict(p.split("÷", 1) for p in l.split("¬") if "÷" in p)
                opponent = parts.get("KJ", "").replace("*", "").strip()
                score = parts.get("KL", "").strip()
                # outcome: KO or KP or check who won
                if opponent and score and ":" in score:
                    res.append(f"{opponent} ({score})")
                if len(res) == 3:
                    break
            break
    return res

print("=== PARSING LAST 3 MATCHES FOR ALL KEY TEAMS ===")
data_table = []
for mid, h_name, a_name, league in matches:
    url = f"https://local-global.flashscore.ninja/2/x/feed/df_hh_1_{mid}"
    h_last, a_last = [], []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            h_last = parse_last_matches(content, h_name)
            a_last = parse_last_matches(content, a_name)
    except Exception as e:
        pass
    
    data_table.append({
        "mid": mid,
        "league": league,
        "home": h_name,
        "away": a_name,
        "h_last": " | ".join(h_last) if h_last else "N.D.",
        "a_last": " | ".join(a_last) if a_last else "N.D."
    })
    print(f"[{league}] {h_name} vs {a_name}:")
    print(f"   Casa ({h_name}): {data_table[-1]['h_last']}")
    print(f"   Ospite ({a_name}): {data_table[-1]['a_last']}")


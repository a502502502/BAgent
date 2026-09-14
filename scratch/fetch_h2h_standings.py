import urllib.request
import json
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "x-fsign": "SW9D1eZo"
}

matches = [
    ("zozyFe7t", "FC Osaka vs Ehime"),
    ("GCRJUNLs", "Geylang vs Tanjong Pagar"),
    ("lUcYV8vR", "Dynamo Kyiv vs Epitsentr"),
    ("p0q4Qn2l", "Shakhtar vs Ch. Odesa"),
    ("QPisJZtH", "U. Cluj vs Otelul"),
    ("rFwuw4qS", "Como vs Parma"),
    ("dxQcraL7", "Torino vs Roma"),
    ("nBSIVLy2", "Inter vs Udinese"),
    ("r5HQ6xTH", "Bodo/Glimt vs Sandefjord"),
    ("llKk8XsI", "Gaziantep vs Fenerbahce"),
    ("hdqa7PVb", "Villarreal vs Betis"),
    ("Q1TGrNGq", "Leeds vs Newcastle"),
    ("zorKqtLb", "Braga vs Estoril"),
    ("8GAxJvHk", "Flamengo vs Corinthians")
]

print("=== CHECKING H2H / STANDINGS FROM FLASHSCORE FEEDS ===")
for mid, name in matches:
    # H2H feed endpoint: df_hh_1_{mid}
    url = f"https://local-global.flashscore.ninja/2/x/feed/df_hh_1_{mid}"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            content = resp.read().decode("utf-8", errors="replace")
            print(f"\n{name} ({mid}) H2H Length: {len(content)}")
            # Let's extract last matches scores
            scores = []
            for item in content.split("~"):
                if "KL÷" in item and "KJ÷" in item:
                    # Match line in H2H
                    parts = dict(p.split("÷", 1) for p in item.split("¬") if "÷" in p)
                    h = parts.get("KJ", "")
                    a = parts.get("KL", "")
                    hg = parts.get("KM", "")
                    ag = parts.get("KN", "")
                    dt = parts.get("KC", "")
                    if h and a and hg != "" and ag != "":
                        scores.append(f"{h} {hg}-{ag} {a}")
            if scores:
                print("   Ultime gare:", " | ".join(scores[:4]))
    except Exception as e:
        print(f"Error for {name}: {e}")

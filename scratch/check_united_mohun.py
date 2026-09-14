import urllib.request
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "x-fsign": "SW9D1eZo"
}

url = "https://local-global.flashscore.ninja/2/x/feed/df_hh_1_OxLBoXJi"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=8) as resp:
        content = resp.read().decode("utf-8", errors="replace")
        print("H2H Length:", len(content))
        for line in content.split("~"):
            if "KJ÷" in line:
                parts = dict(p.split("÷", 1) for p in line.split("¬") if "÷" in p)
                print("MATCH:", parts.get("KC"), parts.get("KJ"), parts.get("KL"))
except Exception as e:
    print("Error:", e)

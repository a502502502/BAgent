import urllib.request
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "x-fsign": "SW9D1eZo"
}

url = "https://local-global.flashscore.ninja/2/x/feed/df_hh_1_rFwuw4qS" # Como vs Parma
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=8) as resp:
    content = resp.read().decode("utf-8", errors="replace")
    for section in content.split("~KB÷"):
        lines = section.split("~")
        print("--- SECTION HEADER ---", lines[0][:80])
        for line in lines[1:6]:
            parts = {}
            for item in line.split("¬"):
                if "÷" in item:
                    k, v = item.split("÷", 1)
                    parts[k] = v
            # Look at keys
            print("  MATCH:", parts.get("KJ"), parts.get("KL"), parts.get("KM"), parts.get("KN"), parts.get("KO"), parts.get("KP"))

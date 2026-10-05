import urllib.request
import json
import base64
import sys

sys.stdout.reconfigure(encoding='utf-8')

repo = "fernandosc14/football-prediction"
url = f"https://api.github.com/repos/{repo}/contents/src/features.py"
req = urllib.request.Request(url, headers={"User-Agent": "BAgent-Bot"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())
    content = base64.b64decode(data["content"]).decode('utf-8', errors='ignore')
    print("Length of features.py:", len(content))
    print(content[:3000])
    print("\n--- NEXT PART ---")
    print(content[3000:6000])

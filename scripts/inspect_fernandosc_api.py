import urllib.request
import json
import base64
import sys

sys.stdout.reconfigure(encoding='utf-8')

def fetch_file(repo, path):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "BAgent-Bot"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, dict) and "content" in data:
                return base64.b64decode(data["content"]).decode('utf-8', errors='ignore')
            return str(data)
    except Exception as e:
        return f"Error: {e}"

print("=== fernandosc14/football-prediction / src/api_fetch.py ===")
print(fetch_file("fernandosc14/football-prediction", "src/api_fetch.py")[:2500])

print("\n=== fernandosc14/football-prediction / config/config.yaml or json ===")
print("config contents:", fetch_file("fernandosc14/football-prediction", "config"))

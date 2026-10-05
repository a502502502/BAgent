import urllib.request
import json
import base64
import sys

sys.stdout.reconfigure(encoding='utf-8')

def get_readme(repo):
    url = f"https://api.github.com/repos/{repo}/readme"
    req = urllib.request.Request(url, headers={"User-Agent": "BAgent-Bot"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return base64.b64decode(data.get("content", "")).decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Error: {e}"

print("=== penaltyblog README ===")
pb_rm = get_readme("martineastwood/penaltyblog")
print(pb_rm[:1800])

print("\n=== soccerdata README ===")
sd_rm = get_readme("probberechts/soccerdata")
print(sd_rm[:1800])

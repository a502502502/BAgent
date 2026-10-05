import urllib.request
import json
import base64
import sys

sys.stdout.reconfigure(encoding='utf-8')

repo = "fernandosc14/football-prediction"

def fetch_contents(path=""):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "BAgent-Bot"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return f"Error: {e}"

def fetch_file(path):
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

print("=== Root contents ===")
items = fetch_contents("")
if isinstance(items, list):
    for it in items:
        print(f"{it['type']}: {it['name']} (path: {it['path']})")

print("\n=== src/ contents ===")
src_items = fetch_contents("src")
if isinstance(src_items, list):
    for it in src_items:
        print(f"{it['type']}: {it['name']} (path: {it['path']})")

print("\n=== README.md excerpt ===")
readme = fetch_file("README.md")
print(readme[:2000])

print("\n=== requirements.txt ===")
reqs = fetch_file("requirements.txt")
print(reqs)

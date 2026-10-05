import urllib.request
import json
import base64
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

def fetch_file(repo, path):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "BAgent-Bot"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if isinstance(data, dict) and "content" in data:
                return base64.b64decode(data["content"]).decode('utf-8', errors='ignore')
            elif isinstance(data, list):
                return "\n".join([f"{item['type']}: {item['name']}" for item in data])
            return str(data)
    except Exception as e:
        return f"Error: {e}"

print("=== sports-skills / skills / football-data ===")
print(fetch_file("machina-sports/sports-skills", "skills/football-data"))

print("\n=== sports-skills / skills / football-data / SKILL.md ===")
skill_md = fetch_file("machina-sports/sports-skills", "skills/football-data/SKILL.md")
print(skill_md[:2000])

print("\n=== sports-skills / skills / espn-api / SKILL.md ===")
espn_md = fetch_file("machina-sports/sports-skills", "skills/espn-api/SKILL.md")
print(espn_md[:2000])

print("\n=== football_pro / core / accumulator.py ===")
accum = fetch_file("TemiKayode/football_pro", "core/accumulator.py")
print(accum[:1500])

print("\n=== football_pro / core / goals_analyzer.py ===")
goals = fetch_file("TemiKayode/football_pro", "core/goals_analyzer.py")
print(goals[:1500])

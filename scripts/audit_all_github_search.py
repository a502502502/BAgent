import urllib.request
import json
import base64
import sys

sys.stdout.reconfigure(encoding='utf-8')

repos = [
    "machina-sports/sports-skills",
    "fernandosc14/football-prediction",
    "tanweer919/FootballMojo",
    "jliakosgr/LiveOddsApiAndGoalAlerts",
    "TemiKayode/football_pro",
    "chromeheartbeat/SmartFootballPredictionsBot",
    "chromeheartbeat/-Smart-Football-Predictions-Bot-PHP-Edition-",
    "vrivellino/cfs",
    "ahmedaw-official/kogoro",
    "banarsiamin/rapidapi-football-prediction"
]

results = []

for repo in repos:
    url = f"https://api.github.com/repos/{repo}"
    req = urllib.request.Request(url, headers={"User-Agent": "BAgent-Bot"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            r_info = {
                "name": repo,
                "stars": data.get("stargazers_count", 0),
                "forks": data.get("forks_count", 0),
                "language": data.get("language", "Unknown"),
                "updated_at": data.get("updated_at", ""),
                "description": data.get("description", ""),
                "archived": data.get("archived", False)
            }
            # fetch readme if possible
            readme_url = f"https://api.github.com/repos/{repo}/readme"
            req_rm = urllib.request.Request(readme_url, headers={"User-Agent": "BAgent-Bot"})
            try:
                with urllib.request.urlopen(req_rm) as resp_rm:
                    rm_data = json.loads(resp_rm.read().decode())
                    content = base64.b64decode(rm_data.get("content", "")).decode("utf-8", errors="ignore")
                    r_info["readme_preview"] = content[:500].replace("\n", " ")
            except Exception as e:
                r_info["readme_preview"] = "No readme"
            results.append(r_info)
    except Exception as e:
        results.append({"name": repo, "error": str(e)})

print(json.dumps(results, indent=2))

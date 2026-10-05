import urllib.request
import json
import urllib.parse
import sys

sys.stdout.reconfigure(encoding='utf-8')

queries = [
    "penaltyblog",
    "kloppy soccer",
    "sports betting backtest python",
    "betting exchange arbitrage pinnacle python"
]

found_repos = {}

for q in queries:
    url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(q)}&sort=stars&order=desc&per_page=5"
    req = urllib.request.Request(url, headers={"User-Agent": "BAgent-Searcher"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            for item in data.get("items", []):
                full_name = item["full_name"]
                if full_name not in found_repos:
                    found_repos[full_name] = {
                        "name": full_name,
                        "stars": item["stargazers_count"],
                        "description": item.get("description", ""),
                        "language": item.get("language", ""),
                        "updated_at": item.get("updated_at", ""),
                        "url": item["html_url"]
                    }
    except Exception as e:
        print(f"Error on query '{q}': {e}")

sorted_repos = sorted(found_repos.values(), key=lambda x: x["stars"], reverse=True)

for r in sorted_repos[:12]:
    print(f"\n[{r['stars']} stars] {r['name']} ({r['language']}) - {r['url']}")
    print(f"  Desc: {r['description']}")
    print(f"  Updated: {r['updated_at']}")

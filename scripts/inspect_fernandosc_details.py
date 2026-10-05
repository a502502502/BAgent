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
            elif isinstance(data, list):
                return "\n".join([f"{item['type']}: {item['name']}" for item in data])
            return str(data)
    except Exception as e:
        return f"Error: {e}"

def fetch_repo_meta(repo):
    url = f"https://api.github.com/repos/{repo}"
    req = urllib.request.Request(url, headers={"User-Agent": "BAgent-Bot"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

# 1. Inspect fernandosc14/football-prediction core files
print("=== fernandosc14/football-prediction / src/features.py ===")
features_py = fetch_file("fernandosc14/football-prediction", "src/features.py")
print(features_py[:2500])

print("\n=== fernandosc14/football-prediction / src/train.py ===")
train_py = fetch_file("fernandosc14/football-prediction", "src/train.py")
print(train_py[:2500])

print("\n=== fernandosc14/football-prediction / src/predict.py ===")
predict_py = fetch_file("fernandosc14/football-prediction", "src/predict.py")
print(predict_py[:2500])

print("\n=== fernandosc14/football-prediction / src/data_prep.py ===")
data_prep = fetch_file("fernandosc14/football-prediction", "src/data_prep.py")
print(data_prep[:2500])

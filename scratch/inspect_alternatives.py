import os, requests, json
from dotenv import load_dotenv
load_dotenv(".env")
key = os.getenv("FOOTYSTATS_API_KEY", "")

candidates = {
    "Gent vs Standard Liege": 8562372,
    "Rapid Wien vs Wattens": 8565847,
    "Racing Club vs Sarmiento": 8419475,
    "Nacional vs Famalicao": 8574337,
    "Gil Vicente vs Maritimo": 8574412
}

results = {}
for name, mid in candidates.items():
    url = f"https://api.football-data-api.com/match?key={key}&match_id={mid}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        d = r.json().get("data", {})
        results[name] = {
            "competition": d.get("competition_name"),
            "date_unix": d.get("date_unix"),
            "home": d.get("home_name"),
            "away": d.get("away_name"),
            "home_ppg": d.get("home_ppg"),
            "away_ppg": d.get("away_ppg"),
            "home_xg": d.get("team_a_xg_prematch"),
            "away_xg": d.get("team_b_xg_prematch"),
            "over15_potential": d.get("o15_potential"),
            "over25_potential": d.get("o25_potential"),
            "btts_potential": d.get("btts_potential"),
            "odds_1": d.get("odds_ft_1"),
            "odds_x": d.get("odds_ft_x"),
            "odds_2": d.get("odds_ft_2"),
            "odds_over15": d.get("odds_ft_over15"),
            "odds_over25": d.get("odds_ft_over25"),
            "odds_under35": d.get("odds_ft_under35"),
            "odds_btts_yes": d.get("odds_btts_yes")
        }

print(json.dumps(results, indent=2))

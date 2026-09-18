import os, sys, json, requests
from dotenv import load_dotenv

load_dotenv(".env")
key = os.getenv("FOOTYSTATS_API_KEY", "")

match_ids = {
    "Groningen vs Zwolle": 8547846,
    "Bayern vs Union Berlin": 8572525,
    "Monaco vs Lens": 8548608,
    "Monza vs Sassuolo": 8545203,
    "Espanyol vs Elche": 8570369,
    "Brentford vs Chelsea": 8558044
}

results = {}
for name, mid in match_ids.items():
    url = f"https://api.football-data-api.com/match?key={key}&match_id={mid}"
    r = requests.get(url, timeout=10)
    if r.status_code == 200:
        d = r.json().get("data", {})
        results[name] = {
            "home": d.get("home_name"),
            "away": d.get("away_name"),
            "league": d.get("competition_name"),
            "home_ppg": d.get("home_ppg"),
            "away_ppg": d.get("away_ppg"),
            "home_xg": d.get("team_a_xg_prematch"),
            "away_xg": d.get("team_b_xg_prematch"),
            "home_goals_avg": d.get("team_a_scored_avg"),
            "away_goals_avg": d.get("team_b_scored_avg"),
            "home_conceded_avg": d.get("team_a_conceded_avg"),
            "away_conceded_avg": d.get("team_b_conceded_avg"),
            "btts_pct": d.get("btts_potential"),
            "over15_pct": d.get("o15_potential"),
            "over25_pct": d.get("o25_potential"),
            "odds_1": d.get("odds_ft_1"),
            "odds_x": d.get("odds_ft_x"),
            "odds_2": d.get("odds_ft_2"),
            "odds_over25": d.get("odds_ft_over25"),
            "odds_under25": d.get("odds_ft_under25"),
            "odds_btts_yes": d.get("odds_btts_yes"),
            "odds_btts_no": d.get("odds_btts_no")
        }

print(json.dumps(results, indent=2))

import os, requests, json
from dotenv import load_dotenv
load_dotenv(".env")
key = os.getenv("FOOTYSTATS_API_KEY", "")

url = f"https://api.football-data-api.com/match?key={key}&match_id=8570369"
r = requests.get(url, timeout=10)
if r.status_code == 200:
    d = r.json().get("data", {})
    print("=== ESPANYOL VS ELCHE (FootyStats Data) ===")
    print("Competition:", d.get("competition_name"))
    print("Home PPG:", d.get("home_ppg"), "Away PPG:", d.get("away_ppg"))
    print("Avg Goals Match:", d.get("avg_potential"))
    print("Over 1.5:", d.get("o15_potential"), "% | Over 2.5:", d.get("o25_potential"), "% | Over 3.5:", d.get("o35_potential"), "% | Over 4.5:", d.get("o45_potential"), "%")
    print("BTTS:", d.get("btts_potential"), "%")
    print("Home Scored Avg:", d.get("team_a_scored_avg"), "Home Conceded Avg:", d.get("team_a_conceded_avg"))
    print("Away Scored Avg:", d.get("team_b_scored_avg"), "Away Conceded Avg:", d.get("team_b_conceded_avg"))
    print("xG Pre-match Home:", d.get("team_a_xg_prematch"), "Away:", d.get("team_b_xg_prematch"))
    print("H2H Previous Matches:")
    h2h = d.get("previous_matches_results", {})
    print("  H2H:", h2h)
    h2h_matches = d.get("h2h", {}).get("previous_matches", [])
    for pm in h2h_matches[:5]:
        print(f"  {pm.get('date')}: {pm.get('home_team')} {pm.get('home_score')}-{pm.get('away_score')} {pm.get('away_team')}")

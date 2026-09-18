import os, requests
from dotenv import load_dotenv
load_dotenv(".env")
key = os.getenv("FOOTYSTATS_API_KEY", "")

url = f"https://api.football-data-api.com/match?key={key}&match_id=8572525"
r = requests.get(url, timeout=10)
if r.status_code == 200:
    d = r.json().get("data", {})
    print("=== BAYERN VS UNION (Corner Stats) ===")
    print("Corner potential match:", d.get("corners_potential"))
    print("Corner over 8.5:", d.get("corners_o85_potential"))
    print("Corner over 9.5:", d.get("corners_o95_potential"))
    print("Corner over 10.5:", d.get("corners_o105_potential"))
    print("Home corners avg:", d.get("team_a_corners_avg"))
    print("Away corners avg:", d.get("team_b_corners_avg"))
    print("Home shots avg:", d.get("team_a_shots_avg"))
    print("Away shots avg:", d.get("team_b_shots_avg"))
    print("Home dangerous attacks:", d.get("team_a_dangerous_attacks_avg"))

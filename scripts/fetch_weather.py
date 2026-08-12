import sys
from pathlib import Path
import json
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import requests

from services.football_data_loader import FootballDataLoader
from services.football_historical_dataset import FootballHistoricalDataset


STADIUM_COORDS = {
    "Arsenal": (51.5549, -0.1084),
    "Aston Villa": (52.5092, -1.8848),
    "Bournemouth": (50.7352, -1.8384),
    "Brentford": (51.4907, -0.2889),
    "Brighton": (50.8619, -0.0834),
    "Burnley": (53.7890, -2.2302),
    "Chelsea": (51.4816, -0.1909),
    "Crystal Palace": (51.3983, -0.0855),
    "Everton": (53.4388, -2.9663),
    "Fulham": (51.4749, -0.2216),
    "Ipswich": (52.0552, 1.1447),
    "Leeds": (53.7778, -1.5722),
    "Leicester": (52.6204, -1.1422),
    "Liverpool": (53.4308, -2.9608),
    "Luton": (51.8843, -0.4316),
    "Man City": (53.4831, -2.2004),
    "Man United": (53.4631, -2.2913),
    "Newcastle": (54.9756, -1.6217),
    "Norwich": (52.6221, 1.3089),
    "Nott'm Forest": (52.9399, -1.1327),
    "Sheffield United": (53.3703, -1.4713),
    "Southampton": (50.9058, -1.3910),
    "Sunderland": (54.9144, -1.3883),
    "Tottenham": (51.6043, -0.0663),
    "Watford": (51.6499, -0.4013),
    "West Brom": (52.5091, -1.9640),
    "West Ham": (51.5386, -0.0166),
    "Wolves": (52.5903, -2.1301),
}

raw_dir = Path("data/football/raw")
files = sorted(raw_dir.glob("E0_*.csv"))

loader = FootballDataLoader()
all_matches = []
for f in files:
    all_matches.extend(loader.load(f))

dataset = FootballHistoricalDataset(all_matches)
completed = [m for m in dataset.all() if m.is_completed]

unmapped = set()
for m in completed:
    if m.match.home.id not in STADIUM_COORDS:
        unmapped.add(m.match.home.id)

if unmapped:
    print("SQUADRE NON MAPPATE (aggiungi le coordinate):")
    for u in sorted(unmapped):
        print(" -", u)
    print()

mappable = [m for m in completed if m.match.home.id in STADIUM_COORDS]
print(f"Partite totali: {len(completed)}, mappabili: {len(mappable)}")
print()

cache_path = Path("data/football/weather_cache.json")
cache = {}
if cache_path.exists():
    cache = json.loads(cache_path.read_text())
    print(f"Cache esistente caricata: {len(cache)} date-luogo già scaricate")

results = []
new_calls = 0

for i, m in enumerate(mappable):

    home_id = m.match.home.id
    lat, lon = STADIUM_COORDS[home_id]
    date_str = m.date.strftime("%Y-%m-%d")
    hour = m.date.hour

    cache_key = f"{lat},{lon},{date_str}"

    if cache_key not in cache:
        url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}&longitude={lon}"
            f"&start_date={date_str}&end_date={date_str}"
            "&hourly=temperature_2m,precipitation,wind_speed_10m"
        )
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            cache[cache_key] = resp.json()
            new_calls += 1
        except Exception as e:
            print(f"Errore meteo per {cache_key}: {e}")
            continue

        if new_calls % 20 == 0 and new_calls > 0:
            cache_path.write_text(json.dumps(cache))
            print(f"  ... {new_calls} nuove chiamate fatte, {i+1}/{len(mappable)} partite processate")

    data = cache[cache_key]

    try:
        hourly = data["hourly"]
        idx = hourly["time"].index(f"{date_str}T{hour:02d}:00")
        temp = hourly["temperature_2m"][idx]
        rain = hourly["precipitation"][idx]
        wind = hourly["wind_speed_10m"][idx]
    except (KeyError, ValueError, IndexError):
        continue

    results.append(
        {
            "match_id": m.match_id,
            "date": date_str,
            "home": home_id,
            "temperature": temp,
            "precipitation": rain,
            "wind_speed": wind,
            "result": m.result,
        }
    )

cache_path.write_text(json.dumps(cache))

print()
print(f"Meteo recuperato per {len(results)} / {len(completed)} partite")
print(f"Nuove chiamate API in questa esecuzione: {new_calls}")

output_path = Path("data/football/weather_enriched.json")
output_path.write_text(json.dumps(results))
print(f"Salvato in: {output_path}")

import sys
from pathlib import Path
from datetime import datetime, timezone
import os

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.football.external.collector import FootballExternalCollector


def main():

    if len(sys.argv) != 4:
        print(
            'USAGE: python scripts\test_external_collector.py '
            '"HOME" "AWAY" YYYY-MM-DD'
        )
        return

    if not os.getenv("API_FOOTBALL_KEY"):
        print("API_FOOTBALL_KEY=NOT SET")
        return

    home = sys.argv[1]
    away = sys.argv[2]
    date = sys.argv[3]

    collector = FootballExternalCollector()

    print()
    print("=" * 60)
    print("EXTERNAL FOOTBALL COLLECTOR")
    print("=" * 60)
    print("HOME:", home)
    print("AWAY:", away)
    print("DATE:", date)
    print("COLLECTED:", datetime.now(timezone.utc).isoformat())

    data = collector.search_fixture(home, away, date)

    response = data.get("response", [])

    print("FIXTURES FOUND:", len(response))

    if not response:
        print("NO FIXTURE FOUND")
        return

    fixture = response[0]
    fixture_id = fixture["fixture"]["id"]

    print("FIXTURE ID:", fixture_id)

    injuries = collector.injuries(fixture_id)
    lineups = collector.lineups(fixture_id)
    odds = collector.odds(fixture_id)

    print("INJURIES:", len(injuries.get("response", [])))
    print("LINEUPS:", len(lineups.get("response", [])))
    print("ODDS:", len(odds.get("response", [])))


if __name__ == "__main__":
    main()


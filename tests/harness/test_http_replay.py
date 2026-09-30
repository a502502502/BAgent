from pathlib import Path

import vcr

from services.football.external.footystats_client import FootyStatsClient

CASSETTE = Path(__file__).resolve().parents[2] / "harness" / "cassettes" / "footystats_league_list.yaml"


def test_league_list_replays_from_the_cassette(tmp_path, monkeypatch):
    monkeypatch.delenv("FOOTYSTATS_API_KEY", raising=False)
    with vcr.use_cassette(str(CASSETTE), record_mode="none"):
        client = FootyStatsClient(api_key="test-key")
        client.cache_dir = tmp_path
        client.leagues_cache_path = tmp_path / "leagues.json"
        leagues = client.get_league_list(force_refresh=True)
    assert leagues[0]["name"] == "Serie A"
    assert leagues[0]["country"] == "Italy"

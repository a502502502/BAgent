from services.analysis.snai_goal_book import goal_odds_from_catalog


def test_open_goal_markets_keep_their_canonical_name():
    catalog = {
        "markets": [
            {
                "market": "1X2 ESITO FINALE",
                "line": "ESITO FINALE 1X2",
                "outcomes": [
                    {"selection": "1", "odds": 1.12, "open": True},
                    {"selection": "X", "odds": 8.0, "open": True},
                ],
            },
            {
                "market": "MULTIGOL",
                "line": "MULTIESITI",
                "outcomes": [{"selection": "2-5", "odds": 1.30, "open": True}],
            },
            {
                "market": "GIOCATORE MARCATORE",
                "line": "YAMAL",
                "outcomes": [{"selection": "SI", "odds": 1.50, "open": True}],
            },
        ]
    }
    odds = goal_odds_from_catalog(catalog)
    assert odds["1"] == 1.12
    assert odds["MultiGol 2-5"] == 1.30
    assert "YAMAL" not in odds
    assert all("GIOCATORE" not in key for key in odds)

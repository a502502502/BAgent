from services.live.score_change_watch import changed_rows, find_row, selection_note


def test_a_youth_side_does_not_stand_in_for_the_senior_team():
    feed = [
        {"home": "France U19", "away": "Italy U19", "score": "0-1", "status_code": "13"},
        {"home": "Italy", "away": "Belgium", "score": "-", "status_code": "1"},
    ]
    row = find_row(feed, "Italia", "Belgio")
    assert row["home"] == "Italy"


def test_the_first_sighting_is_stored_and_the_next_goal_is_an_alert():
    legs = [{"match": "Georgia vs Irlanda del Nord", "pick": "Over 1.5"}]
    first = [{"home": "Georgia", "away": "Northern Ireland", "score": "-", "status_code": "1", "period": ""}]
    alerts, state = changed_rows({}, legs, first)
    assert alerts == []
    second = [{"home": "Georgia", "away": "Northern Ireland", "score": "1-0", "status_code": "12", "period": "23"}]
    alerts, state = changed_rows(state, legs, second)
    assert alerts[0]["score"] == "1-0"
    assert alerts[0]["note"] == "in corso"
    assert selection_note("Over 1.5", "2-0", "live") == "chiusa vinta"
    assert selection_note("Under 2.5", "2-1", "live") == "chiusa persa"
    assert selection_note("X2", "1-0", "ft") == "chiusa persa"
    assert state["Georgia|Irlanda del Nord"].startswith("1-0|")

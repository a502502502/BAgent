from services.betting.netwin_market_parser import (
    UnsupportedNetwinMarket,
    extract_booking_code,
    is_real_netwin_booking_code,
    market_tab_labels,
    outcome_search_texts,
    parse_netwin_selection,
    row_matches_teams,
    split_home_away,
)


def test_straight_1():
    action = parse_netwin_selection("1X2", "1")
    assert action.family == "1X2"
    assert action.pick == "1"
    assert action.column_hint() == 0


def test_doppia_chance_1x():
    action = parse_netwin_selection("DOPPIA CHANCE", "1X")
    assert action.family == "DC"
    assert action.pick == "1X"
    assert action.column_hint() == 3


def test_over_15():
    action = parse_netwin_selection("", "Over 1.5")
    assert action.family == "OU"
    assert action.pick == "OVER"
    assert action.ou_line == 1.5
    assert action.column_hint() is None


def test_combo_1x_under_35():
    action = parse_netwin_selection("", "1X + Under 3.5")
    assert action.family == "COMBO"
    assert action.combo_result == "1X"
    assert action.combo_ou_side == "UNDER"
    assert action.combo_ou_line == 3.5
    assert action.column_hint() is None


def test_gol():
    action = parse_netwin_selection("G/NG", "Gol")
    assert action.family == "BTTS"
    assert action.pick == "GOL"
    assert action.column_hint() == 8


def test_multigol_2_4():
    action = parse_netwin_selection("", "MultiGol 2-4")
    assert action.family == "MULTIGOL"
    assert action.multigol_range == "2-4"
    assert action.multigol_scope == "MATCH"
    assert action.column_hint() is None


def test_unknown_raises():
    try:
        parse_netwin_selection("", "Chance Mix X o GG")
    except UnsupportedNetwinMarket as exc:
        assert "Cannot map" in str(exc)
        return
    raise AssertionError("expected UnsupportedNetwinMarket")


def test_split_home_away_from_match():
    home, away = split_home_away({"match": "Inter vs Udinese"})
    assert home == "Inter"
    assert away == "Udinese"


def test_row_matches_both_teams():
    row = "Inter Milano 1  X  2  Udinese Calcio"
    assert row_matches_teams(row, "Inter", "Udinese")
    assert not row_matches_teams(row, "Inter", "Juventus")


def test_row_ignores_united_stopword():
    row = "Newcastle United vs Manchester City"
    assert row_matches_teams(row, "Newcastle", "Manchester City")


def test_extract_booking_code_from_box_only():
    box = "Prenotazioni effettuate\nCodice prenotazione 482917\nCarica"
    assert extract_booking_code(box) == "482917"
    assert is_real_netwin_booking_code("482917")
    body = "Kickoff 20:45 quota 1.23456 pagina 100000"
    assert extract_booking_code(body) is None
    assert not is_real_netwin_booking_code("NW-1130-T88")


def test_combo_tab_and_labels():
    action = parse_netwin_selection("", "1X + Under 3.5")
    tabs = market_tab_labels(action)
    assert any("Doppia Chance" in t for t in tabs)
    labels = outcome_search_texts(action)
    assert any("1X" in t and "3.5" in t for t in labels)

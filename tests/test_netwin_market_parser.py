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
        parse_netwin_selection("", "Mercato Inventato XYZ")
    except UnsupportedNetwinMarket as exc:
        assert "Cannot map" in str(exc)
        return
    raise AssertionError("expected UnsupportedNetwinMarket")


def test_chance_mix_x_o_gg():
    action = parse_netwin_selection("", "Chance Mix: X o GG")
    assert action.family == "CHANCE_MIX"
    assert action.chance_mix and "X" in action.chance_mix
    assert any("Chance Mix" in t for t in market_tab_labels(action))


def test_corner_over():
    action = parse_netwin_selection("Corner", "Over 8.5")
    assert action.family == "CORNER"
    assert action.specialty_side == "OVER"
    assert action.specialty_line == 8.5
    assert any("Corner" in t for t in market_tab_labels(action))


def test_cards_1x2():
    action = parse_netwin_selection("Cartellini", "1")
    assert action.family == "CARDS"
    assert action.specialty_side == "1"


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


def test_combo_multigol_double_chance_and_straight():
    home_dc = parse_netwin_selection("", "1X + MultiGol 1-4")
    assert home_dc.family == "COMBO"
    assert home_dc.combo_type == "MULTIGOL"
    assert home_dc.combo_result == "1X"
    assert home_dc.combo_multigol_range == "1-4"
    assert home_dc.combo_multigol_scope == "MATCH"

    away_band = parse_netwin_selection("", "x2 + multigol  2 - 4")
    assert away_band.combo_type == "MULTIGOL"
    assert away_band.combo_result == "X2"
    assert away_band.combo_multigol_range == "2-4"

    straight = parse_netwin_selection("", "1 + MultiGol 1-4")
    assert straight.combo_type == "MULTIGOL"
    assert straight.combo_result == "1"
    assert straight.combo_multigol_range == "1-4"
    assert any("MultiGol" in tab for tab in market_tab_labels(straight))


def test_team_multigol_sets_home_or_away_scope():
    home = parse_netwin_selection("", "MultiGol 1-2 Casa")
    assert home.family == "MULTIGOL"
    assert home.multigol_range == "1-2"
    assert home.multigol_scope == "HOME"

    away = parse_netwin_selection("", "MultiGol 1-3 Ospite")
    assert away.multigol_range == "1-3"
    assert away.multigol_scope == "AWAY"
    assert any("Ospite" in label for label in outcome_search_texts(away))


def test_combo_under_and_btts_keep_the_result_side():
    under_35 = parse_netwin_selection("", "1X + Under 3.5")
    assert under_35.combo_type == "OU"
    assert under_35.combo_ou_side == "UNDER"
    assert under_35.combo_ou_line == 3.5

    under_45 = parse_netwin_selection("", "1X + Under 4.5")
    assert under_45.combo_type == "OU"
    assert under_45.combo_result == "1X"
    assert under_45.combo_ou_line == 4.5

    both_score = parse_netwin_selection("", "1X + Gol")
    assert both_score.family == "COMBO"
    assert both_score.combo_type == "BTTS"
    assert both_score.combo_result == "1X"
    assert both_score.combo_ou_side == "GOL"
    assert any("Gol" in label for label in outcome_search_texts(both_score))


def test_corner_lines_keep_over_and_record_the_side():
    home_corners = parse_netwin_selection("", "Over 4.5 Corner Casa")
    assert home_corners.family == "CORNER"
    assert home_corners.specialty_side == "OVER"
    assert home_corners.specialty_line == 4.5
    assert home_corners.specialty_scope == "HOME"
    assert any("Casa" in label for label in outcome_search_texts(home_corners))

    total_corners = parse_netwin_selection("", "Over 8.5 Corner")
    assert total_corners.family == "CORNER"
    assert total_corners.specialty_side == "OVER"
    assert total_corners.specialty_line == 8.5
    assert total_corners.specialty_scope == "TOTAL"
    assert any("Angoli" in tab for tab in market_tab_labels(total_corners))

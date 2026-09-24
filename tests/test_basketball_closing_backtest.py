"""Il backtest NBA non legge il futuro e non gioca una closing line già nel prezzo."""

from datetime import date, timedelta

from services.basketball.backtest import ClosingLine, WalkForwardBacktest, summarize
from services.basketball.fetch import parse_home_games
from services.basketball.gamelog import TeamBox, estimate_possessions, pair_team_boxes
from services.basketball.pricing import choose_side, edge, home_cover_probability, over_probability
from services.basketball.projection import project_score
from services.basketball.ratings import RatingBook, TeamRating


def test_possessions_follow_dean_oliver():
    assert estimate_possessions(fga=90, oreb=10, tov=12, fta=20) == 90 - 10 + 12 + 0.44 * 20


def test_rating_snapshot_excludes_the_game_just_played_until_update():
    book = RatingBook()
    game = _game("1", date(2025, 10, 22), "BOS", "NYK", 120, 110, 100)
    assert book.snapshot() == {}
    book.update(game)
    boston = book.snapshot()["BOS"]
    assert boston.games == 1
    assert boston.offensive_rating == 120
    assert boston.defensive_rating == 110
    assert boston.pace == 100


def test_same_day_games_do_not_leak_into_each_other():
    opening = date(2025, 10, 22)
    history = [
        _game(str(index), opening + timedelta(days=index), "BOS", "NYK", 110, 100, 100)
        for index in range(1, 11)
    ]
    same_day = [
        _game("a", opening + timedelta(days=20), "BOS", "NYK", 140, 80, 100),
        _game("b", opening + timedelta(days=20), "NYK", "BOS", 70, 130, 100),
    ]
    rows = WalkForwardBacktest(min_games=10, home_court_prior=0.0, home_court_strength=0.0).run(
        history + same_day
    )
    assert len(rows) == 2
    assert rows[0].predicted_margin == 20
    assert rows[1].predicted_margin == -20


def test_projection_uses_opponent_defense_once():
    home = TeamRating("BOS", 20, pace=100, offensive_rating=118, defensive_rating=108)
    away = TeamRating("NYK", 20, pace=100, offensive_rating=112, defensive_rating=114)
    projected = project_score(home, away, league_average=112, home_court=2)
    assert projected.home_points == 121
    assert projected.away_points == 107
    assert projected.margin == 14
    assert projected.total == 228


def test_cover_probability_is_a_coin_flip_when_the_line_matches_the_projection():
    assert home_cover_probability(6, 12, -6) == 0.5
    assert over_probability(220, 15, 220) == 0.5
    assert edge(0.5, 2.0) == 0
    assert choose_side({"home": (0.5, 1.87), "away": (0.5, 1.87)}, min_edge=0.04) is None


def test_a_line_equal_to_the_projection_is_not_bet_at_italian_juice():
    games = _season(games_before=12, decided=4, home_points=120, away_points=108)
    engine = WalkForwardBacktest(min_games=10, home_court_prior=0.0, home_court_strength=0.0)
    preview = engine.run(games)
    lines = [
        ClosingLine(
            row.game_date,
            row.home,
            row.away,
            home_spread=-row.predicted_margin,
            total=row.predicted_total,
        )
        for row in preview
    ]
    graded = WalkForwardBacktest(min_games=10, home_court_prior=0.0, home_court_strength=0.0).run(
        games, lines
    )
    assert graded
    assert all(row.spread_side is None for row in graded)
    assert all(row.total_side is None for row in graded)


def test_a_stale_line_is_bet_when_the_edge_clears_four_percent():
    games = _season(games_before=12, decided=1, home_points=120, away_points=108)
    target = games[-1]
    rows = WalkForwardBacktest(min_games=10, home_court_prior=0.0, home_court_strength=0.0).run(
        games,
        [
            ClosingLine(
                target.game_date,
                target.home,
                target.away,
                home_spread=0.0,
                total=200.0,
                home_spread_odds=1.87,
                away_spread_odds=1.87,
                over_odds=1.87,
                under_odds=1.87,
            )
        ],
    )
    last = rows[-1]
    assert last.spread_side == "home"
    assert last.spread_edge is not None and last.spread_edge >= 0.04
    assert last.total_side == "over"
    summary = summarize(rows)
    assert summary.spread_bets == 1
    assert summary.spread_roi == edge(1.0, 1.87)


def test_home_log_keeps_one_game_and_renames_reference_abbreviations():
    html = """
    <table id="team_game_log">
      <tr>
        <td data-stat="date"><a href="/boxscores/202410220BOS.html">2024-10-22</a></td>
        <td data-stat="game_location"></td>
        <td data-stat="opp_name_abbr">CHO</td>
        <td data-stat="team_game_score">110</td>
        <td data-stat="opp_team_game_score">99</td>
        <td data-stat="fga">90</td><td data-stat="fta">20</td><td data-stat="orb">10</td><td data-stat="tov">12</td>
        <td data-stat="opp_fga">80</td><td data-stat="opp_fta">10</td><td data-stat="opp_orb">8</td><td data-stat="opp_tov">15</td>
      </tr>
      <tr>
        <td data-stat="date"><a href="/boxscores/202410230NYK.html">2024-10-23</a></td>
        <td data-stat="game_location">@</td>
        <td data-stat="opp_name_abbr">NYK</td>
        <td data-stat="team_game_score">100</td>
        <td data-stat="opp_team_game_score">101</td>
        <td data-stat="fga">70</td><td data-stat="fta">10</td><td data-stat="orb">5</td><td data-stat="tov">9</td>
        <td data-stat="opp_fga">71</td><td data-stat="opp_fta">11</td><td data-stat="opp_orb">6</td><td data-stat="opp_tov">8</td>
      </tr>
    </table>
    """
    boxes = parse_home_games(html, "2024-25", "BRK")
    games = pair_team_boxes(boxes)
    assert len(games) == 1
    assert games[0].home == "BKN"
    assert games[0].away == "CHA"
    assert games[0].home_points == 110
    assert games[0].possessions > 0


def test_new_season_does_not_inherit_last_season_ratings():
    first = [
        _game(f"a{index}", date(2024, 10, 22) + timedelta(days=index), "BOS", "NYK", 130, 90, 100)
        for index in range(12)
    ]
    second = [
        _game(f"b{index}", date(2025, 10, 22) + timedelta(days=index), "BOS", "NYK", 100, 100, 100)
        for index in range(12)
    ]
    rows = WalkForwardBacktest(min_games=10, home_court_prior=0.0, home_court_strength=0.0).run(
        first + second
    )
    season_two = [row for row in rows if row.season == "2025-26"]
    assert season_two
    assert abs(season_two[0].predicted_margin) < 1


def _season(games_before: int, decided: int, home_points: int, away_points: int):
    start = date(2025, 10, 22)
    games = []
    for index in range(games_before + decided):
        games.append(
            _game(
                str(index),
                start + timedelta(days=index),
                "BOS",
                "NYK",
                home_points,
                away_points,
                100,
            )
        )
    return games


def _game(game_id, game_date, home, away, home_points, away_points, possessions):
    boxes = [
        TeamBox(game_id, game_date, _season_of(game_date), home, True, home_points, possessions, 0, 0, 0),
        TeamBox(game_id, game_date, _season_of(game_date), away, False, away_points, possessions, 0, 0, 0),
    ]
    return pair_team_boxes(boxes)[0]


def _season_of(game_date: date) -> str:
    start_year = game_date.year if game_date.month >= 8 else game_date.year - 1
    return f"{start_year}-{str(start_year + 1)[-2:]}"

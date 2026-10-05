from services.analysis.statistical_combo import (
    best_combination,
    best_ticket,
    rank_statistical_combos,
    statistical_score,
)


def test_score_peaks_on_the_sweet_spot():
    center = statistical_score(0.80, 1.45)
    short_price = statistical_score(0.93, 1.21)
    longshot = statistical_score(0.40, 3.20)
    assert center > short_price
    assert center > longshot
    assert statistical_score(0.70, 1.15) == 0.0


def test_negative_edge_stays_in_the_ranking():
    ranked = rank_statistical_combos(
        2.16,
        0.89,
        {
            "1": 1.38,
            "X": 5.0,
            "2": 8.0,
            "Over 2.5": 1.52,
            "MultiGol 2-5": 1.30,
        },
    )
    winner = best_combination(ranked)
    assert winner is not None
    assert winner.market == "MultiGol 2-5"
    assert winner.edge < 0
    assert winner.blocked is None


def test_rigid_result_and_tight_band_do_not_win():
    ranked = rank_statistical_combos(
        2.16,
        0.89,
        {
            "1": 1.38,
            "Over 2.5": 1.52,
            "1 + Over 1.5": 1.45,
            "MultiGol 1-3": 1.45,
            "MultiGol 2-5": 1.30,
        },
    )
    names = {row.market: row.blocked for row in ranked}
    assert names["1 + Over 1.5"] == "1X2 secco"
    assert names["MultiGol 1-3"] == "tetto su attacco dominante"
    assert best_combination(ranked).market == "MultiGol 2-5"


def test_ticket_keeps_four_highest_scores():
    from services.analysis.statistical_combo import StatPick

    picks = [
        StatPick(f"m{i}", 0.75, 1.40, 1.33, 0.05, score)
        for i, score in enumerate((0.9, 0.2, 0.7, 0.4, 0.8, 0.1))
    ]
    chosen = best_ticket(picks, size=4)
    assert len(chosen) == 4
    assert [row.score for row in chosen] == [0.9, 0.8, 0.7, 0.4]

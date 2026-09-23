from application.validation.ranking_history import (
    RankingHistory,
    RankingSnapshot
)


history = RankingHistory(
    [
        RankingSnapshot(
            date="2026-01-01",
            rankings={
                "Juventus": 1,
                "Milan": 2
            }
        ),
        RankingSnapshot(
            date="2026-01-08",
            rankings={
                "Juventus": 2,
                "Milan": 1
            }
        )
    ]
)


assert history.get_ranking(
    "Juventus",
    "2026-01-05"
) == 1


assert history.get_ranking(
    "Juventus",
    "2026-01-10"
) == 2


assert history.get_ranking(
    "Milan",
    "2026-01-05"
) == 2


assert history.get_ranking(
    "Milan",
    "2026-01-10"
) == 1


print()
print("RANKING HISTORY TEST PASSED")
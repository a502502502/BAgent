from application.validation.ranking_history import (
    RankingHistory,
    RankingSnapshot
)


history = RankingHistory(
    [
        RankingSnapshot(
            date="2026-01-01",
            rankings={
                "JannikSinner": 1,
                "CarlosAlcaraz": 2
            }
        ),
        RankingSnapshot(
            date="2026-01-08",
            rankings={
                "JannikSinner": 2,
                "CarlosAlcaraz": 1
            }
        )
    ]
)


assert history.get_ranking(
    "JannikSinner",
    "2026-01-05"
) == 1


assert history.get_ranking(
    "JannikSinner",
    "2026-01-10"
) == 2


assert history.get_ranking(
    "CarlosAlcaraz",
    "2026-01-05"
) == 2


assert history.get_ranking(
    "CarlosAlcaraz",
    "2026-01-10"
) == 1


print()
print("RANKING HISTORY TEST PASSED")
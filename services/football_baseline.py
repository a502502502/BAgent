from models.football_probability import (
    FootballProbability,
)


class FootballBaseline:

    HOME = 0.45
    DRAW = 0.27
    AWAY = 0.28

    def predict(self) -> FootballProbability:

        return FootballProbability(
            home=self.HOME,
            draw=self.DRAW,
            away=self.AWAY,
        )

import math
from typing import Optional

from models.contribution import Contribution
from models.football_profile import FootballTeamProfile


class FootballMatchBalanceFactor:

    def evaluate(
        self,
        home_profile: Optional[FootballTeamProfile],
        away_profile: Optional[FootballTeamProfile],
    ) -> Optional[Contribution]:

        if home_profile is None or away_profile is None:
            return None

        if (
            home_profile.matches <= 0
            or away_profile.matches <= 0
        ):
            return None

        home_win_rate = home_profile.win_rate
        away_win_rate = away_profile.win_rate
        home_draw_rate = home_profile.draw_rate
        away_draw_rate = away_profile.draw_rate

        if (
            home_win_rate is None
            or away_win_rate is None
            or home_draw_rate is None
            or away_draw_rate is None
        ):
            return None

        win_difference = abs(
            home_win_rate - away_win_rate
        )

        draw_rate = (
            home_draw_rate + away_draw_rate
        ) / 2.0

        win_balance = math.exp(
            -4.0 * win_difference
        )

        draw_component = min(
            1.0,
            draw_rate / 0.30,
        )

        value = (
            0.70 * win_balance
            + 0.30 * draw_component
        )

        value = max(
            0.0,
            min(1.0, value),
        )

        confidence = min(
            1.0,
            (
                home_profile.matches
                + away_profile.matches
            )
            / 40.0,
        )

        return Contribution(
            factor="MatchBalance",
            value=value,
            confidence=confidence,
            explanation=(
                "Historical match balance based "
                "on similarity of team win rates "
                "and historical draw rates."
            ),
            details={
                "home_team": home_profile.team_name,
                "away_team": away_profile.team_name,
                "home_win_rate": home_win_rate,
                "away_win_rate": away_win_rate,
                "home_draw_rate": home_draw_rate,
                "away_draw_rate": away_draw_rate,
                "win_difference": win_difference,
                "average_draw_rate": draw_rate,
                "win_balance": win_balance,
                "draw_component": draw_component,
            },
        )

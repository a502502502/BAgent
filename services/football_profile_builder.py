from typing import Dict, Iterable

from models.football import FootballMatch
from models.football_profile import FootballTeamProfile


class FootballProfileBuilder:

    def build(
        self,
        matches: Iterable[FootballMatch],
    ) -> Dict[str, FootballTeamProfile]:

        profiles: Dict[str, FootballTeamProfile] = {}

        for match in matches:

            home_profile = self._get_or_create(
                profiles,
                match.home.id,
                match.home.name,
            )

            away_profile = self._get_or_create(
                profiles,
                match.away.id,
                match.away.name,
            )

            if not match.is_completed:
                continue

            self._update_home(
                home_profile,
                match,
            )

            self._update_away(
                away_profile,
                match,
            )

        return profiles

    @staticmethod
    def _get_or_create(
        profiles: Dict[str, FootballTeamProfile],
        team_id: str,
        team_name: str,
    ) -> FootballTeamProfile:

        if team_id not in profiles:

            profiles[team_id] = FootballTeamProfile(
                team_id=team_id,
                team_name=team_name,
            )

        return profiles[team_id]

    @staticmethod
    def _update_home(
        profile: FootballTeamProfile,
        match: FootballMatch,
    ):

        profile.matches += 1
        profile.home_matches += 1

        profile.goals_for += match.home_goals
        profile.goals_against += match.away_goals

        if match.home_goals > match.away_goals:

            profile.wins += 1
            profile.home_wins += 1

        elif match.home_goals == match.away_goals:

            profile.draws += 1
            profile.home_draws += 1

        else:

            profile.losses += 1
            profile.home_losses += 1

        if match.away_goals == 0:
            profile.clean_sheets += 1

        if (
            match.home_goals > 0
            and match.away_goals > 0
        ):
            profile.btts_matches += 1

        if match.home_corners is not None:
            profile.corners_for += match.home_corners

        if match.away_corners is not None:
            profile.corners_against += match.away_corners

        if match.home_yellow_cards is not None:
            profile.yellow_cards += match.home_yellow_cards

        if match.home_red_cards is not None:
            profile.red_cards += match.home_red_cards

        if match.home_xg is not None:
            profile.xg_for += match.home_xg

        if match.away_xg is not None:
            profile.xg_against += match.away_xg

    @staticmethod
    def _update_away(
        profile: FootballTeamProfile,
        match: FootballMatch,
    ):

        profile.matches += 1
        profile.away_matches += 1

        profile.goals_for += match.away_goals
        profile.goals_against += match.home_goals

        if match.away_goals > match.home_goals:

            profile.wins += 1
            profile.away_wins += 1

        elif match.away_goals == match.home_goals:

            profile.draws += 1
            profile.away_draws += 1

        else:

            profile.losses += 1
            profile.away_losses += 1

        if match.home_goals == 0:
            profile.clean_sheets += 1

        if (
            match.home_goals > 0
            and match.away_goals > 0
        ):
            profile.btts_matches += 1

        if match.away_corners is not None:
            profile.corners_for += match.away_corners

        if match.home_corners is not None:
            profile.corners_against += match.home_corners

        if match.away_yellow_cards is not None:
            profile.yellow_cards += match.away_yellow_cards

        if match.away_red_cards is not None:
            profile.red_cards += match.away_red_cards

        if match.away_xg is not None:
            profile.xg_for += match.away_xg

        if match.home_xg is not None:
            profile.xg_against += match.home_xg

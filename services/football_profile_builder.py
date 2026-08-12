import math

from datetime import datetime
from typing import Dict, Iterable, Optional

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
                weight=1.0,
            )

            self._update_away(
                away_profile,
                match,
                weight=1.0,
            )

        return profiles

    def build_recency(
        self,
        matches: Iterable[FootballMatch],
        reference_date: datetime,
        decay: float = 2.0,
    ) -> Dict[str, FootballTeamProfile]:

        profiles: Dict[str, FootballTeamProfile] = {}

        ordered_matches = sorted(
            matches,
            key=lambda item: item.start_time,
        )

        for match in ordered_matches:

            if not match.is_completed:
                continue

            match_date = datetime.fromisoformat(
                match.start_time
            )

            if match_date >= reference_date:
                continue

            age_days = (
                reference_date - match_date
            ).total_seconds() / 86400.0

            age_years = (
                age_days / 365.25
            )

            weight = math.exp(
                -decay * age_years
            )

            if weight <= 0.0:
                continue

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

            self._update_home(
                home_profile,
                match,
                weight=weight,
            )

            self._update_away(
                away_profile,
                match,
                weight=weight,
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
        weight: float = 1.0,
    ):

        profile.matches += weight
        profile.home_matches += weight

        profile.goals_for += (
            match.home_goals * weight
        )

        profile.goals_against += (
            match.away_goals * weight
        )

        if match.home_goals > match.away_goals:

            profile.wins += weight
            profile.home_wins += weight

        elif match.home_goals == match.away_goals:

            profile.draws += weight
            profile.home_draws += weight

        else:

            profile.losses += weight
            profile.home_losses += weight

        if match.away_goals == 0:
            profile.clean_sheets += weight

        if (
            match.home_goals > 0
            and match.away_goals > 0
        ):
            profile.btts_matches += weight

        if match.home_corners is not None:

            profile.corners_for += (
                match.home_corners * weight
            )

        if match.away_corners is not None:

            profile.corners_against += (
                match.away_corners * weight
            )

        if match.home_yellow_cards is not None:

            profile.yellow_cards += (
                match.home_yellow_cards * weight
            )

        if match.home_red_cards is not None:

            profile.red_cards += (
                match.home_red_cards * weight
            )

        if match.home_xg is not None:

            profile.xg_for += (
                match.home_xg * weight
            )

        if match.away_xg is not None:

            profile.xg_against += (
                match.away_xg * weight
            )

    @staticmethod
    def _update_away(
        profile: FootballTeamProfile,
        match: FootballMatch,
        weight: float = 1.0,
    ):

        profile.matches += weight
        profile.away_matches += weight

        profile.goals_for += (
            match.away_goals * weight
        )

        profile.goals_against += (
            match.home_goals * weight
        )

        if match.away_goals > match.home_goals:

            profile.wins += weight
            profile.away_wins += weight

        elif match.away_goals == match.home_goals:

            profile.draws += weight
            profile.away_draws += weight

        else:

            profile.losses += weight
            profile.away_losses += weight

        if match.home_goals == 0:
            profile.clean_sheets += weight

        if (
            match.home_goals > 0
            and match.away_goals > 0
        ):
            profile.btts_matches += weight

        if match.away_corners is not None:

            profile.corners_for += (
                match.away_corners * weight
            )

        if match.home_corners is not None:

            profile.corners_against += (
                match.home_corners * weight
            )

        if match.away_yellow_cards is not None:

            profile.yellow_cards += (
                match.away_yellow_cards * weight
            )

        if match.away_red_cards is not None:

            profile.red_cards += (
                match.away_red_cards * weight
            )

        if match.away_xg is not None:

            profile.xg_for += (
                match.away_xg * weight
            )

        if match.home_xg is not None:

            profile.xg_against += (
                match.home_xg * weight
            )

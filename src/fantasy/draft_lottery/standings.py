"""Standings module for retrieving and classifying ESPN league standings."""

import functools
from dataclasses import dataclass

from espn_api.basketball import League


@dataclass
class TeamRecord:
    """A team's season results including wins, losses, final standing, and playoff status."""

    team_id: int
    team_name: str
    wins: int
    losses: int
    owner: str
    standing: int  # ESPN's playoffSeed: end-of-regular-season ranking (1=best, 12=worst)
    final_standing: int  # Final league placement (1=champion, 12=worst)
    made_playoffs: bool  # Whether the team made the playoffs

    @property
    def win_percentage(self) -> float:
        """Calculate win percentage. Returns 0.0 if no games played."""
        total = self.wins + self.losses
        if total == 0:
            return 0.0
        return self.wins / total


def _extract_owner_name(owners: list) -> str:
    """Extract a readable owner name from the ESPN owners list."""
    if not owners:
        return "Unknown"
    owner = owners[0]
    if isinstance(owner, dict):
        first = owner.get("firstName", "")
        last = owner.get("lastName", "")
        name = f"{first} {last}".strip()
        return name if name else "Unknown"
    return str(owner)


def _h2h_wins(team_a, team_b) -> int:
    """Return how many regular-season matchups team_a won against team_b."""
    wins = 0
    b_id = team_b.team_id
    for matchup in team_a.schedule:
        home = matchup.home_team
        away = matchup.away_team
        home_id = home.team_id if hasattr(home, 'team_id') else home
        away_id = away.team_id if hasattr(away, 'team_id') else away
        if b_id not in (home_id, away_id):
            continue
        a_is_home = (home_id == team_a.team_id)
        if (matchup.winner == 'HOME' and a_is_home) or (matchup.winner == 'AWAY' and not a_is_home):
            wins += 1
    return wins


def get_standings(league_id: int, year: int, espn_s2: str, swid: str) -> list[TeamRecord]:
    """
    Fetch league standings from ESPN for the given season.
    Returns list of TeamRecord sorted by wins ascending (worst first).
    Includes final_standing and made_playoffs from playoff bracket results.

    Raises:
        ConnectionError: If ESPN API is unreachable due to network issues.
        ValueError: If the league is not found for the given season year.
        PermissionError: If the ESPN credentials are invalid.
    """
    try:
        league = League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)
    except ConnectionError:
        raise ConnectionError(
            "Unable to reach the ESPN API. Please check your internet connection and try again."
        )
    except Exception as e:
        error_message = str(e).lower()
        if "invalid" in error_message or "unauthorized" in error_message or "401" in error_message:
            raise PermissionError(
                "Invalid ESPN credentials. Please verify your espn_s2 and swid tokens are correct."
            )
        if "not found" in error_message or "404" in error_message:
            raise ValueError(
                f"League not found for the {year - 1}-{year} season. "
                f"Please verify the league ID and season year."
            )
        raise ValueError(
            f"League not found for the {year - 1}-{year} season. "
            f"Please verify the league ID and season year."
        )

    def _compare(team_a, team_b) -> int:
        if team_a.wins != team_b.wins:
            return team_a.wins - team_b.wins
        if team_a.losses != team_b.losses:
            return team_b.losses - team_a.losses
        a_h2h = _h2h_wins(team_a, team_b)
        b_h2h = _h2h_wins(team_b, team_a)
        return a_h2h - b_h2h

    sorted_espn_teams = sorted(league.teams, key=functools.cmp_to_key(_compare))

    teams: list[TeamRecord] = []
    for team in sorted_espn_teams:
        made_playoffs = team.final_standing <= 6
        teams.append(
            TeamRecord(
                team_id=team.team_id,
                team_name=team.team_name,
                wins=team.wins,
                losses=team.losses,
                owner=_extract_owner_name(team.owners),
                standing=team.standing,
                final_standing=team.final_standing,
                made_playoffs=made_playoffs,
            )
        )

    return teams


def get_lottery_teams(standings: list[TeamRecord], count: int = 3) -> list[TeamRecord]:
    """
    Return the bottom N teams from standings (by regular season record).
    standings must already be sorted worst-first.
    """
    return standings[:count]


def get_non_playoff_non_lottery_teams(
    standings: list[TeamRecord], lottery_count: int = 3
) -> list[TeamRecord]:
    """
    Return teams that missed the playoffs but aren't in the lottery.
    These are teams ranked 4th-6th worst by regular season record.
    Returns sorted by wins ascending (worst first).
    """
    # Skip the lottery teams (first lottery_count), then take non-playoff teams
    non_lottery = standings[lottery_count:]
    non_playoff_non_lottery = [t for t in non_lottery if not t.made_playoffs]
    # Already sorted by wins ascending from the input standings order
    return non_playoff_non_lottery


def get_playoff_teams(standings: list[TeamRecord]) -> list[TeamRecord]:
    """
    Return teams that made the playoffs.
    Returns sorted by final_standing descending (earliest eliminated first).
    Highest final_standing number = earliest eliminated = picks first (7th).
    Champion (final_standing=1) is last = picks 12th.
    """
    playoff = [t for t in standings if t.made_playoffs]
    # Sort by final_standing descending: highest number first (earliest eliminated)
    playoff.sort(key=lambda t: t.final_standing, reverse=True)
    return playoff

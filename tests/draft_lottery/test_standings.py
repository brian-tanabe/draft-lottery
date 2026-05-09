"""Unit tests for the standings module."""

from unittest.mock import MagicMock, patch

import pytest

from fantasy.draft_lottery.standings import (
    TeamRecord,
    get_lottery_teams,
    get_non_playoff_non_lottery_teams,
    get_playoff_teams,
    get_standings,
)


def _make_team(
    team_id: int,
    wins: int,
    losses: int,
    final_standing: int,
    made_playoffs: bool,
    team_name: str = "",
    owner: str = "Owner",
) -> TeamRecord:
    """Helper to create a TeamRecord for testing."""
    if not team_name:
        team_name = f"Team {team_id}"
    return TeamRecord(
        team_id=team_id,
        team_name=team_name,
        wins=wins,
        losses=losses,
        owner=owner,
        final_standing=final_standing,
        made_playoffs=made_playoffs,
    )


def _make_12_team_standings() -> list[TeamRecord]:
    """Create a sorted 12-team standings list (worst first)."""
    # 6 non-playoff teams (bottom 6 by record), 6 playoff teams
    teams = [
        _make_team(1, wins=5, losses=17, final_standing=12, made_playoffs=False),
        _make_team(2, wins=6, losses=16, final_standing=11, made_playoffs=False),
        _make_team(3, wins=7, losses=15, final_standing=10, made_playoffs=False),
        _make_team(4, wins=8, losses=14, final_standing=9, made_playoffs=False),
        _make_team(5, wins=9, losses=13, final_standing=8, made_playoffs=False),
        _make_team(6, wins=10, losses=12, final_standing=7, made_playoffs=False),
        _make_team(7, wins=11, losses=11, final_standing=6, made_playoffs=True),
        _make_team(8, wins=12, losses=10, final_standing=5, made_playoffs=True),
        _make_team(9, wins=13, losses=9, final_standing=4, made_playoffs=True),
        _make_team(10, wins=14, losses=8, final_standing=3, made_playoffs=True),
        _make_team(11, wins=15, losses=7, final_standing=2, made_playoffs=True),
        _make_team(12, wins=16, losses=6, final_standing=1, made_playoffs=True),
    ]
    return teams


# --- Tests for get_standings ---


class TestGetStandings:
    """Tests for the get_standings function."""

    @patch("fantasy.draft_lottery.standings.League")
    def test_returns_12_team_records_sorted_by_wins_ascending(self, mock_league_class):
        """get_standings returns TeamRecords sorted by wins ascending."""
        mock_teams = []
        for i in range(12):
            team = MagicMock()
            team.team_id = i + 1
            team.team_name = f"Team {i + 1}"
            team.wins = 10 + i  # 10 to 21 wins
            team.losses = 22 - (10 + i)  # corresponding losses
            team.owners = [{"firstName": f"Owner", "lastName": f"{i + 1}"}]
            team.final_standing = 12 - i  # 12 down to 1
            mock_teams.append(team)

        mock_league = MagicMock()
        mock_league.teams = mock_teams
        mock_league_class.return_value = mock_league

        result = get_standings(22603, 2025, "fake_s2", "fake_swid")

        assert len(result) == 12
        # Verify sorted by wins ascending
        for i in range(len(result) - 1):
            assert result[i].wins <= result[i + 1].wins

    @patch("fantasy.draft_lottery.standings.League")
    def test_tiebreaker_losses_descending(self, mock_league_class):
        """When wins are tied, teams are sorted by losses descending."""
        mock_teams = []
        # Two teams with same wins but different losses
        team_a = MagicMock()
        team_a.team_id = 1
        team_a.team_name = "Team A"
        team_a.wins = 10
        team_a.losses = 12  # More losses
        team_a.owners = [{"firstName": "Owner", "lastName": "A"}]
        team_a.final_standing = 8
        mock_teams.append(team_a)

        team_b = MagicMock()
        team_b.team_id = 2
        team_b.team_name = "Team B"
        team_b.wins = 10
        team_b.losses = 10  # Fewer losses
        team_b.owners = [{"firstName": "Owner", "lastName": "B"}]
        team_b.final_standing = 7
        mock_teams.append(team_b)

        # Fill remaining 10 teams
        for i in range(3, 13):
            team = MagicMock()
            team.team_id = i
            team.team_name = f"Team {i}"
            team.wins = 10 + i
            team.losses = 22 - (10 + i)
            team.owners = [{"firstName": "Owner", "lastName": f"{i}"}]
            team.final_standing = i
            mock_teams.append(team)

        mock_league = MagicMock()
        mock_league.teams = mock_teams
        mock_league_class.return_value = mock_league

        result = get_standings(22603, 2025, "fake_s2", "fake_swid")

        # Team A (10 wins, 12 losses) should come before Team B (10 wins, 10 losses)
        # because losses descending means more losses = earlier in list
        tied_teams = [t for t in result if t.wins == 10]
        assert len(tied_teams) == 2
        assert tied_teams[0].losses > tied_teams[1].losses

    @patch("fantasy.draft_lottery.standings.League")
    def test_extracts_correct_fields(self, mock_league_class):
        """get_standings extracts all required fields from ESPN team objects."""
        team = MagicMock()
        team.team_id = 5
        team.team_name = "Ty Fighter"
        team.wins = 15
        team.losses = 7
        team.owners = [{"firstName": "Brian", "lastName": "Tanabe"}]
        team.final_standing = 2

        mock_league = MagicMock()
        mock_league.teams = [team] * 12  # 12 identical teams for simplicity
        mock_league_class.return_value = mock_league

        result = get_standings(22603, 2025, "fake_s2", "fake_swid")

        record = result[0]
        assert record.team_id == 5
        assert record.team_name == "Ty Fighter"
        assert record.wins == 15
        assert record.losses == 7
        assert record.owner == "Brian Tanabe"
        assert record.final_standing == 2
        assert record.made_playoffs is True  # final_standing 2 <= 6

    @patch("fantasy.draft_lottery.standings.League")
    def test_playoff_status_based_on_final_standing(self, mock_league_class):
        """Teams with final_standing <= 6 are marked as made_playoffs."""
        mock_teams = []
        for i in range(12):
            team = MagicMock()
            team.team_id = i + 1
            team.team_name = f"Team {i + 1}"
            team.wins = i + 5
            team.losses = 22 - (i + 5)
            team.owners = [{"firstName": "Owner", "lastName": f"{i + 1}"}]
            team.final_standing = i + 1  # 1 through 12
            mock_teams.append(team)

        mock_league = MagicMock()
        mock_league.teams = mock_teams
        mock_league_class.return_value = mock_league

        result = get_standings(22603, 2025, "fake_s2", "fake_swid")

        playoff_teams = [t for t in result if t.made_playoffs]
        non_playoff_teams = [t for t in result if not t.made_playoffs]
        assert len(playoff_teams) == 6
        assert len(non_playoff_teams) == 6
        # All playoff teams have final_standing <= 6
        for t in playoff_teams:
            assert t.final_standing <= 6
        for t in non_playoff_teams:
            assert t.final_standing > 6

    @patch("fantasy.draft_lottery.standings.League")
    def test_network_error_raises_connection_error(self, mock_league_class):
        """Network issues raise ConnectionError with helpful message."""
        mock_league_class.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectionError, match="check your internet connection"):
            get_standings(22603, 2025, "fake_s2", "fake_swid")

    @patch("fantasy.draft_lottery.standings.League")
    def test_invalid_credentials_raises_permission_error(self, mock_league_class):
        """Invalid credentials raise PermissionError."""
        mock_league_class.side_effect = Exception("401 Unauthorized")

        with pytest.raises(PermissionError, match="Invalid ESPN credentials"):
            get_standings(22603, 2025, "fake_s2", "fake_swid")

    @patch("fantasy.draft_lottery.standings.League")
    def test_league_not_found_raises_value_error(self, mock_league_class):
        """League not found raises ValueError."""
        mock_league_class.side_effect = Exception("League not found")

        with pytest.raises(ValueError, match="League not found"):
            get_standings(22603, 2025, "fake_s2", "fake_swid")


# --- Tests for get_lottery_teams ---


class TestGetLotteryTeams:
    """Tests for the get_lottery_teams function."""

    def test_returns_bottom_3_teams(self):
        """Returns the first 3 teams from sorted standings."""
        standings = _make_12_team_standings()
        lottery = get_lottery_teams(standings)

        assert len(lottery) == 3
        assert lottery[0].team_id == 1  # worst record
        assert lottery[1].team_id == 2
        assert lottery[2].team_id == 3

    def test_custom_count(self):
        """Supports custom count parameter."""
        standings = _make_12_team_standings()
        lottery = get_lottery_teams(standings, count=4)

        assert len(lottery) == 4

    def test_preserves_order(self):
        """Returned teams maintain the input order (worst first)."""
        standings = _make_12_team_standings()
        lottery = get_lottery_teams(standings)

        for i in range(len(lottery) - 1):
            assert lottery[i].wins <= lottery[i + 1].wins


# --- Tests for get_non_playoff_non_lottery_teams ---


class TestGetNonPlayoffNonLotteryTeams:
    """Tests for the get_non_playoff_non_lottery_teams function."""

    def test_returns_non_playoff_teams_not_in_lottery(self):
        """Returns teams that missed playoffs and aren't in bottom 3."""
        standings = _make_12_team_standings()
        middle = get_non_playoff_non_lottery_teams(standings)

        # Teams 4, 5, 6 are non-playoff but not in bottom 3
        assert len(middle) == 3
        for team in middle:
            assert not team.made_playoffs
            assert team.team_id not in [1, 2, 3]  # not lottery teams

    def test_sorted_by_wins_ascending(self):
        """Returned teams are sorted by wins ascending."""
        standings = _make_12_team_standings()
        middle = get_non_playoff_non_lottery_teams(standings)

        for i in range(len(middle) - 1):
            assert middle[i].wins <= middle[i + 1].wins

    def test_custom_lottery_count(self):
        """Respects custom lottery_count parameter."""
        standings = _make_12_team_standings()
        middle = get_non_playoff_non_lottery_teams(standings, lottery_count=4)

        # With 4 lottery teams, only 2 non-playoff non-lottery teams remain
        assert len(middle) == 2

    def test_disjoint_from_lottery(self):
        """No overlap with lottery teams."""
        standings = _make_12_team_standings()
        lottery = get_lottery_teams(standings, count=3)
        middle = get_non_playoff_non_lottery_teams(standings, lottery_count=3)

        lottery_ids = {t.team_id for t in lottery}
        middle_ids = {t.team_id for t in middle}
        assert lottery_ids.isdisjoint(middle_ids)


# --- Tests for get_playoff_teams ---


class TestGetPlayoffTeams:
    """Tests for the get_playoff_teams function."""

    def test_returns_only_playoff_teams(self):
        """Returns only teams where made_playoffs is True."""
        standings = _make_12_team_standings()
        playoff = get_playoff_teams(standings)

        assert len(playoff) == 6
        for team in playoff:
            assert team.made_playoffs is True

    def test_sorted_by_final_standing_descending(self):
        """Sorted by final_standing descending (earliest eliminated first)."""
        standings = _make_12_team_standings()
        playoff = get_playoff_teams(standings)

        # First team should have highest final_standing (earliest eliminated)
        for i in range(len(playoff) - 1):
            assert playoff[i].final_standing > playoff[i + 1].final_standing

    def test_champion_is_last(self):
        """The champion (final_standing=1) is last in the list."""
        standings = _make_12_team_standings()
        playoff = get_playoff_teams(standings)

        assert playoff[-1].final_standing == 1

    def test_earliest_eliminated_is_first(self):
        """The earliest eliminated team (highest final_standing) is first."""
        standings = _make_12_team_standings()
        playoff = get_playoff_teams(standings)

        # Team with final_standing=6 is earliest eliminated playoff team
        assert playoff[0].final_standing == 6


# --- Tests for tier classification producing disjoint sets ---


class TestTierClassification:
    """Tests that tier classification produces disjoint sets covering all 12 teams."""

    def test_all_teams_covered(self):
        """All 12 teams appear in exactly one tier."""
        standings = _make_12_team_standings()
        lottery = get_lottery_teams(standings)
        middle = get_non_playoff_non_lottery_teams(standings)
        playoff = get_playoff_teams(standings)

        all_ids = {t.team_id for t in lottery} | {t.team_id for t in middle} | {t.team_id for t in playoff}
        assert len(all_ids) == 12

    def test_tiers_are_disjoint(self):
        """No team appears in more than one tier."""
        standings = _make_12_team_standings()
        lottery = get_lottery_teams(standings)
        middle = get_non_playoff_non_lottery_teams(standings)
        playoff = get_playoff_teams(standings)

        lottery_ids = {t.team_id for t in lottery}
        middle_ids = {t.team_id for t in middle}
        playoff_ids = {t.team_id for t in playoff}

        assert lottery_ids.isdisjoint(middle_ids)
        assert lottery_ids.isdisjoint(playoff_ids)
        assert middle_ids.isdisjoint(playoff_ids)

    def test_total_count_equals_12(self):
        """Total teams across all tiers equals 12."""
        standings = _make_12_team_standings()
        lottery = get_lottery_teams(standings)
        middle = get_non_playoff_non_lottery_teams(standings)
        playoff = get_playoff_teams(standings)

        assert len(lottery) + len(middle) + len(playoff) == 12

"""Unit tests for the format_results and format_standings functions."""

from fantasy.draft_lottery.cli import format_results, format_standings
from fantasy.draft_lottery.simulator import LotteryResult
from fantasy.draft_lottery.standings import TeamRecord


def _make_team(
    team_id: int,
    team_name: str,
    wins: int,
    losses: int,
    owner: str,
    final_standing: int,
    made_playoffs: bool,
) -> TeamRecord:
    """Helper to create a TeamRecord."""
    return TeamRecord(
        team_id=team_id,
        team_name=team_name,
        wins=wins,
        losses=losses,
        owner=owner,
        final_standing=final_standing,
        made_playoffs=made_playoffs,
    )


def _build_sample_draft_order() -> list[LotteryResult]:
    """Build a full 12-pick sample draft order for testing."""
    team1 = _make_team(1, "The Detroit Pistons", 5, 17, "Matt Sollars", 12, False)
    team2 = _make_team(2, "Flat World Champions", 6, 16, "Xiaofeng Tao", 11, False)
    team3 = _make_team(3, "Houston We Have Problems", 7, 15, "Kenny Vottero", 10, False)
    team4 = _make_team(4, "Big Dawgs", 8, 14, "Alberto Chavez", 9, False)
    team5 = _make_team(5, "I AM NEGAN", 9, 13, "Phil Nealey", 8, False)
    team6 = _make_team(6, "Sxton Harden", 10, 12, "Mike Bailey, Jr.", 7, False)
    team7 = _make_team(7, "OH MY!", 12, 10, "Kurt Schmitt", 6, True)
    team8 = _make_team(8, "Alley KATs", 13, 9, "Sam Courtney", 5, True)
    team9 = _make_team(9, "Tyrese's Pieces", 14, 8, "Ben Courtney", 4, True)
    team10 = _make_team(10, "The Process", 15, 7, "Will Chaney", 3, True)
    team11 = _make_team(11, "Ty Fighter", 16, 6, "Brian Tanabe", 2, True)
    team12 = _make_team(12, "One Big Mob", 18, 4, "Kenley Schmitt", 1, True)

    return [
        LotteryResult(pick_number=1, team=team2, odds=0.30),
        LotteryResult(pick_number=2, team=team1, odds=0.80),
        LotteryResult(pick_number=3, team=team3, odds=1.0),
        LotteryResult(pick_number=4, team=team4, odds=0.0),
        LotteryResult(pick_number=5, team=team5, odds=0.0),
        LotteryResult(pick_number=6, team=team6, odds=0.0),
        LotteryResult(pick_number=7, team=team7, odds=0.0),
        LotteryResult(pick_number=8, team=team8, odds=0.0),
        LotteryResult(pick_number=9, team=team9, odds=0.0),
        LotteryResult(pick_number=10, team=team10, odds=0.0),
        LotteryResult(pick_number=11, team=team11, odds=0.0),
        LotteryResult(pick_number=12, team=team12, odds=0.0),
    ]


def _build_sample_standings() -> list[TeamRecord]:
    """Build a sample standings list sorted worst-first."""
    return [
        _make_team(1, "The Detroit Pistons", 5, 17, "Matt Sollars", 12, False),
        _make_team(2, "Flat World Champions", 6, 16, "Xiaofeng Tao", 11, False),
        _make_team(3, "Houston We Have Problems", 7, 15, "Kenny Vottero", 10, False),
        _make_team(4, "Big Dawgs", 8, 14, "Alberto Chavez", 9, False),
        _make_team(5, "I AM NEGAN", 9, 13, "Phil Nealey", 8, False),
        _make_team(6, "Sxton Harden", 10, 12, "Mike Bailey, Jr.", 7, False),
        _make_team(7, "OH MY!", 12, 10, "Kurt Schmitt", 6, True),
        _make_team(8, "Alley KATs", 13, 9, "Sam Courtney", 5, True),
        _make_team(9, "Tyrese's Pieces", 14, 8, "Ben Courtney", 4, True),
        _make_team(10, "The Process", 15, 7, "Will Chaney", 3, True),
        _make_team(11, "Ty Fighter", 16, 6, "Brian Tanabe", 2, True),
        _make_team(12, "One Big Mob", 18, 4, "Kenley Schmitt", 1, True),
    ]


class TestFormatResults:
    """Tests for the simplified format_results function."""

    def test_all_12_picks_present(self):
        """Output should contain all 12 pick numbers."""
        draft_order = _build_sample_draft_order()
        output = format_results(draft_order)

        for i in range(1, 13):
            assert f"Pick #{i}" in output

    def test_picks_in_order(self):
        """Picks should appear in order from 1 to 12."""
        draft_order = _build_sample_draft_order()
        output = format_results(draft_order)

        positions = []
        for i in range(1, 13):
            pos = output.find(f"Pick #{i}")
            assert pos != -1
            positions.append(pos)

        for i in range(1, len(positions)):
            assert positions[i] > positions[i - 1]

    def test_includes_team_name_and_owner(self):
        """Each pick shows team name and owner."""
        draft_order = _build_sample_draft_order()
        output = format_results(draft_order)

        assert "Flat World Champions" in output
        assert "Xiaofeng Tao" in output
        assert "One Big Mob" in output
        assert "Kenley Schmitt" in output

    def test_starts_with_header(self):
        """Output starts with the draft order header."""
        draft_order = _build_sample_draft_order()
        output = format_results(draft_order)

        assert output.startswith("Draft Order:")


class TestFormatStandings:
    """Tests for the format_standings function."""

    def test_includes_season_label(self):
        """Output includes the season year range."""
        standings = _build_sample_standings()
        output = format_standings(standings, 2025)

        assert "2024-2025 Season Standings:" in output

    def test_includes_all_teams(self):
        """Output includes all 12 team names."""
        standings = _build_sample_standings()
        output = format_standings(standings, 2025)

        assert "The Detroit Pistons" in output
        assert "One Big Mob" in output
        assert "Ty Fighter" in output

    def test_includes_records(self):
        """Output includes win-loss records."""
        standings = _build_sample_standings()
        output = format_standings(standings, 2025)

        assert "18-4" in output  # Best team
        assert "5-17" in output  # Worst team

    def test_best_team_listed_first(self):
        """Best record appears before worst record."""
        standings = _build_sample_standings()
        output = format_standings(standings, 2025)

        best_pos = output.find("18-4")
        worst_pos = output.find("5-17")
        assert best_pos < worst_pos

    def test_numbered_list(self):
        """Teams are numbered 1 through 12."""
        standings = _build_sample_standings()
        output = format_standings(standings, 2025)

        assert "  1." in output
        assert "  12." in output

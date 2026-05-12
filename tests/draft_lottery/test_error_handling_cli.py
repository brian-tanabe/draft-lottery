"""Unit tests for CLI error handling functions."""

from unittest.mock import patch

from fantasy.draft_lottery.cli import run_with_error_handling, sanitize_error_message
from fantasy.draft_lottery.standings import TeamRecord


def _make_team(team_id: int, wins: int, losses: int, made_playoffs: bool, final_standing: int) -> TeamRecord:
    """Helper to create a TeamRecord for testing."""
    return TeamRecord(
        team_id=team_id,
        team_name=f"Team {team_id}",
        wins=wins,
        losses=losses,
        owner=f"Owner {team_id}",
        standing=final_standing,
        final_standing=final_standing,
        made_playoffs=made_playoffs,
    )


def _make_full_standings() -> list[TeamRecord]:
    """Create a full 12-team standings list sorted by wins ascending."""
    teams = [
        _make_team(1, wins=5, losses=17, made_playoffs=False, final_standing=12),
        _make_team(2, wins=6, losses=16, made_playoffs=False, final_standing=11),
        _make_team(3, wins=7, losses=15, made_playoffs=False, final_standing=10),
        _make_team(4, wins=8, losses=14, made_playoffs=False, final_standing=9),
        _make_team(5, wins=9, losses=13, made_playoffs=False, final_standing=8),
        _make_team(6, wins=10, losses=12, made_playoffs=False, final_standing=7),
        _make_team(7, wins=11, losses=11, made_playoffs=True, final_standing=6),
        _make_team(8, wins=12, losses=10, made_playoffs=True, final_standing=5),
        _make_team(9, wins=13, losses=9, made_playoffs=True, final_standing=4),
        _make_team(10, wins=14, losses=8, made_playoffs=True, final_standing=3),
        _make_team(11, wins=15, losses=7, made_playoffs=True, final_standing=2),
        _make_team(12, wins=16, losses=6, made_playoffs=True, final_standing=1),
    ]
    return teams


class TestSanitizeErrorMessage:
    """Tests for sanitize_error_message function."""

    def test_removes_espn_s2_token(self):
        token = "AEAIFXoK%2BFtTY123456"
        message = f"Error connecting with token {token}"
        result = sanitize_error_message(message, espn_s2=token, swid="")
        assert token not in result
        assert "[REDACTED]" in result

    def test_removes_swid_token(self):
        swid = "{2C871453-D3F6-433B-884C-F72D75438C03}"
        message = f"Authentication failed for {swid}"
        result = sanitize_error_message(message, espn_s2="", swid=swid)
        assert swid not in result
        assert "[REDACTED]" in result

    def test_removes_both_tokens(self):
        espn_s2 = "secret_espn_token_value"
        swid = "{GUID-TOKEN-VALUE}"
        message = f"Failed with {espn_s2} and {swid}"
        result = sanitize_error_message(message, espn_s2=espn_s2, swid=swid)
        assert espn_s2 not in result
        assert swid not in result
        assert result.count("[REDACTED]") == 2

    def test_preserves_message_without_tokens(self):
        message = "League not found for the 2024-2025 season."
        result = sanitize_error_message(message, espn_s2="abc123", swid="{xyz}")
        assert result == message

    def test_handles_empty_tokens(self):
        message = "Some error occurred"
        result = sanitize_error_message(message, espn_s2="", swid="")
        assert result == message


class TestRunWithErrorHandling:
    """Tests for run_with_error_handling function."""

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_network_error_returns_exit_code_1(self, mock_get_standings, capsys):
        """Network errors produce user-friendly message and exit code 1."""
        mock_get_standings.side_effect = ConnectionError("Connection refused")

        exit_code = run_with_error_handling(2025, "token_s2", "{swid_token}")

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Unable to reach the ESPN API" in captured.out
        assert "internet connection" in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_network_error_does_not_leak_tokens(self, mock_get_standings, capsys):
        """Network error messages never include tokens."""
        espn_s2 = "my_secret_espn_s2_token"
        swid = "{MY-SECRET-SWID-GUID}"
        mock_get_standings.side_effect = ConnectionError("Connection refused")

        run_with_error_handling(2025, espn_s2, swid)

        captured = capsys.readouterr()
        assert espn_s2 not in captured.out
        assert swid not in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_league_not_found_returns_exit_code_1(self, mock_get_standings, capsys):
        """League not found produces descriptive error and exit code 1."""
        mock_get_standings.side_effect = ValueError(
            "League not found for the 2024-2025 season. "
            "Please verify the league ID and season year."
        )

        exit_code = run_with_error_handling(2025, "token_s2", "{swid}")

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "League not found" in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_league_not_found_does_not_leak_tokens(self, mock_get_standings, capsys):
        """League not found error messages never include tokens."""
        espn_s2 = "secret_token_abc"
        swid = "{SECRET-SWID-123}"
        mock_get_standings.side_effect = ValueError(
            f"League not found. Token was {espn_s2} with swid {swid}"
        )

        run_with_error_handling(2025, espn_s2, swid)

        captured = capsys.readouterr()
        assert espn_s2 not in captured.out
        assert swid not in captured.out
        assert "[REDACTED]" in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_permission_error_returns_exit_code_1(self, mock_get_standings, capsys):
        """Invalid credentials produce descriptive error and exit code 1."""
        mock_get_standings.side_effect = PermissionError("Invalid credentials")

        exit_code = run_with_error_handling(2025, "token_s2", "{swid}")

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "Invalid ESPN credentials" in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_permission_error_does_not_leak_tokens(self, mock_get_standings, capsys):
        """Permission error messages never include tokens."""
        espn_s2 = "super_secret_espn_s2"
        swid = "{SUPER-SECRET-SWID}"
        mock_get_standings.side_effect = PermissionError("Invalid credentials")

        run_with_error_handling(2025, espn_s2, swid)

        captured = capsys.readouterr()
        assert espn_s2 not in captured.out
        assert swid not in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_insufficient_teams_returns_exit_code_1(self, mock_get_standings, capsys):
        """Insufficient teams (fewer than 3) produces descriptive error and exit code 1."""
        # Return only 2 teams
        mock_get_standings.return_value = [
            _make_team(1, wins=5, losses=17, made_playoffs=False, final_standing=2),
            _make_team(2, wins=6, losses=16, made_playoffs=False, final_standing=1),
        ]

        exit_code = run_with_error_handling(2025, "token_s2", "{swid}")

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "not have enough teams" in captured.out
        assert "lottery" in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_insufficient_teams_does_not_leak_tokens(self, mock_get_standings, capsys):
        """Insufficient teams error messages never include tokens."""
        espn_s2 = "token_that_should_not_appear"
        swid = "{SWID-SHOULD-NOT-APPEAR}"
        mock_get_standings.return_value = [
            _make_team(1, wins=5, losses=17, made_playoffs=False, final_standing=1),
        ]

        run_with_error_handling(2025, espn_s2, swid)

        captured = capsys.readouterr()
        assert espn_s2 not in captured.out
        assert swid not in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_successful_execution_returns_exit_code_0(self, mock_get_standings, capsys):
        """Successful execution returns exit code 0."""
        mock_get_standings.return_value = _make_full_standings()

        exit_code = run_with_error_handling(2025, "token_s2", "{swid}")

        assert exit_code == 0
        captured = capsys.readouterr()
        assert "Draft Order" in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_successful_execution_does_not_leak_tokens(self, mock_get_standings, capsys):
        """Successful output never includes tokens."""
        espn_s2 = "secret_espn_s2_value_xyz"
        swid = "{SECRET-SWID-VALUE-XYZ}"
        mock_get_standings.return_value = _make_full_standings()

        run_with_error_handling(2025, espn_s2, swid)

        captured = capsys.readouterr()
        assert espn_s2 not in captured.out
        assert swid not in captured.out

    @patch("fantasy.draft_lottery.cli.get_standings")
    def test_league_no_history_returns_exit_code_1(self, mock_get_standings, capsys):
        """League has no history for the given year produces descriptive error and exit code 1."""
        mock_get_standings.side_effect = ValueError(
            "League not found for the 2001-2002 season. "
            "Please verify the league ID and season year."
        )

        exit_code = run_with_error_handling(2002, "token_s2", "{swid}")

        assert exit_code == 1
        captured = capsys.readouterr()
        assert "League not found" in captured.out
        assert "2001-2002" in captured.out

"""Unit tests for season year input validation."""

from datetime import datetime
from unittest.mock import patch

import pytest

from fantasy.draft_lottery.cli import get_season_year, validate_year


class TestValidateYear:
    """Tests for the validate_year helper function."""

    def test_valid_current_year(self):
        """Accepts the current year."""
        current_year = str(datetime.now().year)
        is_valid, error = validate_year(current_year)
        assert is_valid is True
        assert error is None

    def test_valid_next_year(self):
        """Accepts current year + 1."""
        next_year = str(datetime.now().year + 1)
        is_valid, error = validate_year(next_year)
        assert is_valid is True
        assert error is None

    def test_valid_year_2000(self):
        """Accepts the minimum valid year (2000)."""
        is_valid, error = validate_year("2000")
        assert is_valid is True
        assert error is None

    def test_valid_year_2025(self):
        """Accepts a typical valid year."""
        is_valid, error = validate_year("2025")
        assert is_valid is True
        assert error is None

    def test_rejects_non_numeric_alpha(self):
        """Rejects alphabetic input."""
        is_valid, error = validate_year("abc")
        assert is_valid is False
        assert error is not None
        assert "numeric" in error.lower()

    def test_rejects_non_numeric_empty(self):
        """Rejects empty string."""
        is_valid, error = validate_year("")
        assert is_valid is False
        assert error is not None

    def test_rejects_non_numeric_special_chars(self):
        """Rejects special characters."""
        is_valid, error = validate_year("20!5")
        assert is_valid is False
        assert error is not None

    def test_rejects_non_numeric_float(self):
        """Rejects float-like input."""
        is_valid, error = validate_year("2025.5")
        assert is_valid is False
        assert error is not None

    def test_rejects_year_too_far_future(self):
        """Rejects year after current year + 1."""
        future_year = str(datetime.now().year + 2)
        is_valid, error = validate_year(future_year)
        assert is_valid is False
        assert error is not None
        assert "cannot be after" in error.lower()

    def test_rejects_year_before_2000(self):
        """Rejects year before 2000."""
        is_valid, error = validate_year("1999")
        assert is_valid is False
        assert error is not None

    def test_rejects_negative_year(self):
        """Rejects negative year."""
        is_valid, error = validate_year("-1")
        assert is_valid is False
        assert error is not None

    def test_handles_whitespace(self):
        """Handles leading/trailing whitespace."""
        is_valid, error = validate_year("  2025  ")
        assert is_valid is True
        assert error is None

    def test_rejects_spaces_only(self):
        """Rejects whitespace-only input."""
        is_valid, error = validate_year("   ")
        assert is_valid is False
        assert error is not None


class TestGetSeasonYear:
    """Tests for the get_season_year interactive function."""

    @patch("fantasy.draft_lottery.cli.input", return_value="2025")
    def test_accepts_valid_year_first_try(self, mock_input):
        """Returns valid year on first attempt."""
        result = get_season_year()
        assert result == 2025
        assert mock_input.call_count == 1

    @patch("fantasy.draft_lottery.cli.input", side_effect=["abc", "2025"])
    @patch("fantasy.draft_lottery.cli.print")
    def test_reprompts_on_non_numeric(self, mock_print, mock_input):
        """Re-prompts after non-numeric input."""
        result = get_season_year()
        assert result == 2025
        assert mock_input.call_count == 2
        # Verify error message was printed
        mock_print.assert_called_once()
        assert "Error:" in mock_print.call_args[0][0]

    @patch("fantasy.draft_lottery.cli.input", side_effect=["9999", "2025"])
    @patch("fantasy.draft_lottery.cli.print")
    def test_reprompts_on_future_year(self, mock_print, mock_input):
        """Re-prompts after year too far in the future."""
        result = get_season_year()
        assert result == 2025
        assert mock_input.call_count == 2
        mock_print.assert_called_once()
        assert "Error:" in mock_print.call_args[0][0]

    @patch("fantasy.draft_lottery.cli.input", side_effect=["", "not_a_year", "2024"])
    @patch("fantasy.draft_lottery.cli.print")
    def test_reprompts_multiple_times(self, mock_print, mock_input):
        """Re-prompts multiple times until valid input."""
        result = get_season_year()
        assert result == 2024
        assert mock_input.call_count == 3
        assert mock_print.call_count == 2

    @patch("fantasy.draft_lottery.cli.input", return_value="2000")
    def test_accepts_minimum_year(self, mock_input):
        """Accepts the minimum valid year."""
        result = get_season_year()
        assert result == 2000

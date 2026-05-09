"""Tests for the main() entry point in scripts/draft_lottery.py."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the script module directly since scripts/ isn't a package
_script_path = Path(__file__).resolve().parents[2] / "scripts" / "draft_lottery.py"
_spec = importlib.util.spec_from_file_location("draft_lottery_script", _script_path)
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
sys.modules["draft_lottery_script"] = _module
main = _module.main


class TestMain:
    """Tests for the main() function."""

    @patch("draft_lottery_script.run_with_error_handling", return_value=0)
    @patch("draft_lottery_script.get_credentials", return_value=("token123", "{swid}"))
    @patch("draft_lottery_script.get_season_year", return_value=2025)
    def test_main_success_exits_zero(
        self, mock_year, mock_creds, mock_run, capsys
    ):
        """main() exits with code 0 on successful workflow."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        mock_year.assert_called_once()
        mock_creds.assert_called_once()
        mock_run.assert_called_once_with(2025, "token123", "{swid}")

    @patch("draft_lottery_script.run_with_error_handling", return_value=1)
    @patch("draft_lottery_script.get_credentials", return_value=("bad", "{bad}"))
    @patch("draft_lottery_script.get_season_year", return_value=2025)
    def test_main_error_exits_nonzero(
        self, mock_year, mock_creds, mock_run, capsys
    ):
        """main() exits with code 1 when workflow returns error."""
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1

    @patch("draft_lottery_script.run_with_error_handling", return_value=0)
    @patch("draft_lottery_script.get_credentials", return_value=("t", "{s}"))
    @patch("draft_lottery_script.get_season_year", return_value=2024)
    def test_main_prints_banner(self, mock_year, mock_creds, mock_run, capsys):
        """main() prints the welcome banner before collecting input."""
        with pytest.raises(SystemExit):
            main()

        captured = capsys.readouterr()
        assert "Fantasy Basketball Draft Lottery" in captured.out
        assert "====================================" in captured.out

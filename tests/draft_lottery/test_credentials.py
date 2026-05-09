"""Tests for credential collection and LEAGUE_ID constant."""

from unittest.mock import patch

from fantasy.draft_lottery.cli import LEAGUE_ID, get_credentials


class TestLeagueIdConstant:
    """Tests for the LEAGUE_ID constant."""

    def test_league_id_equals_22603(self):
        assert LEAGUE_ID == 22603


class TestGetCredentials:
    """Tests for the get_credentials function."""

    @patch("fantasy.draft_lottery.cli.input")
    def test_prompts_for_espn_s2(self, mock_input):
        mock_input.side_effect = ["my_espn_s2_token", "my_swid_token"]
        get_credentials()
        assert "espn_s2" in mock_input.call_args_list[0][0][0]

    @patch("fantasy.draft_lottery.cli.input")
    def test_prompts_for_swid(self, mock_input):
        mock_input.side_effect = ["my_espn_s2_token", "my_swid_token"]
        get_credentials()
        assert "swid" in mock_input.call_args_list[1][0][0]

    @patch("fantasy.draft_lottery.cli.input")
    def test_input_called_twice(self, mock_input):
        mock_input.side_effect = ["token1", "token2"]
        get_credentials()
        assert mock_input.call_count == 2

    @patch("fantasy.draft_lottery.cli.input")
    def test_returns_correct_tuple(self, mock_input):
        mock_input.side_effect = ["espn_s2_value", "swid_value"]
        result = get_credentials()
        assert result == ("espn_s2_value", "swid_value")

    @patch("fantasy.draft_lottery.cli.input")
    def test_returns_tuple_type(self, mock_input):
        mock_input.side_effect = ["a", "b"]
        result = get_credentials()
        assert isinstance(result, tuple)
        assert len(result) == 2

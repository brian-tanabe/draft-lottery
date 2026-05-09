"""Unit tests for the refactored lottery simulator."""

import pytest

from fantasy.draft_lottery.simulator import (
    LotteryResult,
    build_full_draft_order,
    run_lottery,
)
from fantasy.draft_lottery.standings import TeamRecord


def make_team(team_id, name, wins, losses, standing, playoffs=False):
    """Create a TeamRecord fixture for testing."""
    return TeamRecord(
        team_id=team_id,
        team_name=name,
        wins=wins,
        losses=losses,
        owner=f"Owner {team_id}",
        final_standing=standing,
        made_playoffs=playoffs,
    )


@pytest.fixture
def lottery_teams():
    """3 lottery teams sorted worst-first."""
    return [
        make_team(1, "Worst Team", 3, 17, 12),
        make_team(2, "Second Worst", 5, 15, 11),
        make_team(3, "Third Worst", 7, 13, 10),
    ]


class TestRunLotteryResults:
    """6.1 - Test run_lottery returns exactly 3 results with distinct teams and pick numbers 1, 2, 3."""

    def test_returns_exactly_3_results(self, lottery_teams):
        results = run_lottery(lottery_teams)
        assert len(results) == 3

    def test_pick_numbers_are_1_2_3(self, lottery_teams):
        results = run_lottery(lottery_teams)
        pick_numbers = [r.pick_number for r in results]
        assert pick_numbers == [1, 2, 3]

    def test_all_3_teams_appear_exactly_once(self, lottery_teams):
        results = run_lottery(lottery_teams)
        team_ids = [r.team.team_id for r in results]
        assert sorted(team_ids) == [1, 2, 3]

    def test_no_duplicate_teams(self, lottery_teams):
        results = run_lottery(lottery_teams)
        team_ids = [r.team.team_id for r in results]
        assert len(set(team_ids)) == 3


class TestRunLotteryValidation:
    """6.2 - Test run_lottery raises ValueError for non-3-team input."""

    def test_raises_for_0_teams(self):
        with pytest.raises(ValueError, match="Lottery requires exactly 3 teams"):
            run_lottery([])

    def test_raises_for_1_team(self):
        teams = [make_team(1, "Solo", 3, 17, 12)]
        with pytest.raises(ValueError, match="Lottery requires exactly 3 teams"):
            run_lottery(teams)

    def test_raises_for_2_teams(self):
        teams = [
            make_team(1, "Team A", 3, 17, 12),
            make_team(2, "Team B", 5, 15, 11),
        ]
        with pytest.raises(ValueError, match="Lottery requires exactly 3 teams"):
            run_lottery(teams)

    def test_raises_for_4_teams(self):
        teams = [
            make_team(1, "Team A", 3, 17, 12),
            make_team(2, "Team B", 5, 15, 11),
            make_team(3, "Team C", 7, 13, 10),
            make_team(4, "Team D", 8, 12, 9),
        ]
        with pytest.raises(ValueError, match="Lottery requires exactly 3 teams"):
            run_lottery(teams)


class TestLotteryResultCombination:
    """6.3 - Test LotteryResult.combination is populated for lottery picks."""

    def test_combination_is_not_none(self, lottery_teams):
        results = run_lottery(lottery_teams)
        for result in results:
            assert result.combination is not None

    def test_combination_is_frozenset(self, lottery_teams):
        results = run_lottery(lottery_teams)
        for result in results:
            assert isinstance(result.combination, frozenset)

    def test_combination_contains_3_ints(self, lottery_teams):
        results = run_lottery(lottery_teams)
        for result in results:
            assert len(result.combination) == 3
            for ball in result.combination:
                assert isinstance(ball, int)
                assert 1 <= ball <= 10


class TestBuildFullDraftOrder:
    """6.4 - Test build_full_draft_order works with new LotteryResult (combination field present)."""

    def test_returns_12_picks_total(self, lottery_teams):
        # Run lottery to get results with combination field populated
        lottery_results = run_lottery(lottery_teams)

        non_playoff_teams = [
            make_team(4, "4th Worst", 8, 12, 9),
            make_team(5, "5th Worst", 9, 11, 8),
            make_team(6, "6th Worst", 10, 10, 7),
        ]
        playoff_teams = [
            make_team(7, "Playoff 6th", 12, 8, 6, playoffs=True),
            make_team(8, "Playoff 5th", 13, 7, 5, playoffs=True),
            make_team(9, "Playoff 4th", 14, 6, 4, playoffs=True),
            make_team(10, "Playoff 3rd", 15, 5, 3, playoffs=True),
            make_team(11, "Playoff 2nd", 16, 4, 2, playoffs=True),
            make_team(12, "Champion", 17, 3, 1, playoffs=True),
        ]

        full_order = build_full_draft_order(lottery_results, non_playoff_teams, playoff_teams)
        assert len(full_order) == 12

    def test_pick_numbers_are_sequential_1_to_12(self, lottery_teams):
        lottery_results = run_lottery(lottery_teams)

        non_playoff_teams = [
            make_team(4, "4th Worst", 8, 12, 9),
            make_team(5, "5th Worst", 9, 11, 8),
            make_team(6, "6th Worst", 10, 10, 7),
        ]
        playoff_teams = [
            make_team(7, "Playoff 6th", 12, 8, 6, playoffs=True),
            make_team(8, "Playoff 5th", 13, 7, 5, playoffs=True),
            make_team(9, "Playoff 4th", 14, 6, 4, playoffs=True),
            make_team(10, "Playoff 3rd", 15, 5, 3, playoffs=True),
            make_team(11, "Playoff 2nd", 16, 4, 2, playoffs=True),
            make_team(12, "Champion", 17, 3, 1, playoffs=True),
        ]

        full_order = build_full_draft_order(lottery_results, non_playoff_teams, playoff_teams)
        pick_numbers = [r.pick_number for r in full_order]
        assert pick_numbers == list(range(1, 13))

    def test_lottery_picks_have_combination(self, lottery_teams):
        lottery_results = run_lottery(lottery_teams)

        non_playoff_teams = [
            make_team(4, "4th Worst", 8, 12, 9),
        ]
        playoff_teams = [
            make_team(7, "Playoff 6th", 12, 8, 6, playoffs=True),
        ]

        full_order = build_full_draft_order(lottery_results, non_playoff_teams, playoff_teams)

        # First 3 picks (lottery) should have combinations
        for result in full_order[:3]:
            assert result.combination is not None

        # Non-lottery picks should have combination=None
        for result in full_order[3:]:
            assert result.combination is None

    def test_non_lottery_picks_have_zero_odds(self, lottery_teams):
        lottery_results = run_lottery(lottery_teams)

        non_playoff_teams = [
            make_team(4, "4th Worst", 8, 12, 9),
        ]
        playoff_teams = [
            make_team(7, "Playoff 6th", 12, 8, 6, playoffs=True),
        ]

        full_order = build_full_draft_order(lottery_results, non_playoff_teams, playoff_teams)

        # Non-lottery picks should have 0.0 odds
        for result in full_order[3:]:
            assert result.odds == 0.0

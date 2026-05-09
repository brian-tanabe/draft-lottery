"""Unit tests for the draw_combination function."""

import random
from unittest.mock import patch

import pytest

from fantasy.draft_lottery.combinations import (
    INVALID_COMBINATION,
    build_combination_pool,
    draw_combination,
)


class TestDrawCombinationSeeded:
    """Tests for draw_combination using seeded random."""

    def test_returns_valid_team_not_in_already_selected(self):
        """5.1 - draw_combination returns a team_index not in already_selected
        and the combination maps to that team."""
        pool = build_combination_pool()
        already_selected = {0}

        random.seed(42)
        team_index, combination = draw_combination(pool, already_selected)

        # The returned team must not be in already_selected
        assert team_index not in already_selected
        # The combination must map to the returned team_index
        assert pool.assignments[combination] == team_index
        # The team_index must be valid (0, 1, or 2)
        assert team_index in {0, 1, 2}
        # The combination must not be the invalid one
        assert combination != INVALID_COMBINATION


class TestDrawCombinationSkipsInvalid:
    """Tests for draw_combination skipping the invalid combination."""

    def test_skips_invalid_combination(self):
        """5.2 - draw_combination skips the invalid combination {8, 9, 10}
        and returns the next valid draw."""
        pool = build_combination_pool()
        already_selected: set[int] = set()

        # First call returns the invalid combination [8, 9, 10],
        # second call returns a valid combination [1, 2, 3]
        valid_combo = frozenset({1, 2, 3})
        expected_team = pool.assignments[valid_combo]

        with patch("fantasy.draft_lottery.combinations.random.sample") as mock_sample:
            mock_sample.side_effect = [[8, 9, 10], [1, 2, 3]]
            team_index, combination = draw_combination(pool, already_selected)

        assert combination == valid_combo
        assert team_index == expected_team
        # random.sample should have been called twice (invalid then valid)
        assert mock_sample.call_count == 2


class TestDrawCombinationSkipsAlreadySelected:
    """Tests for draw_combination skipping already-selected teams."""

    def test_skips_already_selected_team(self):
        """5.3 - draw_combination skips combinations belonging to
        already-selected teams and returns one for an unselected team."""
        pool = build_combination_pool()

        # Find a combination belonging to team 0
        combo_for_team_0 = None
        for combo, team_idx in pool.assignments.items():
            if team_idx == 0:
                combo_for_team_0 = sorted(combo)
                break

        # Find a combination belonging to team 1
        combo_for_team_1 = None
        for combo, team_idx in pool.assignments.items():
            if team_idx == 1:
                combo_for_team_1 = sorted(combo)
                break

        already_selected = {0}  # Team 0 is already selected

        with patch("fantasy.draft_lottery.combinations.random.sample") as mock_sample:
            # First return a combo for team 0 (should be skipped),
            # then return a combo for team 1 (should be accepted)
            mock_sample.side_effect = [combo_for_team_0, combo_for_team_1]
            team_index, combination = draw_combination(pool, already_selected)

        assert team_index == 1
        assert combination == frozenset(combo_for_team_1)
        # random.sample should have been called twice
        assert mock_sample.call_count == 2


class TestDrawCombinationAllSelected:
    """Tests for draw_combination when all teams are selected."""

    def test_raises_value_error_when_all_teams_selected(self):
        """5.4 - draw_combination raises ValueError when all teams
        are already selected."""
        pool = build_combination_pool()
        already_selected = {0, 1, 2}

        with pytest.raises(ValueError, match="No teams remaining"):
            draw_combination(pool, already_selected)

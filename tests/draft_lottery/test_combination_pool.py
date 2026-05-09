"""Unit tests for the combination pool construction and validation."""

import pytest

from fantasy.draft_lottery.combinations import (
    INVALID_COMBINATION,
    TEAM_COMBINATION_COUNTS,
    VALID_COMBINATIONS,
    CombinationPool,
    build_combination_pool,
    validate_combination_pool,
)


class TestBuildCombinationPool:
    """Tests for build_combination_pool()."""

    def test_produces_exactly_119_combinations(self):
        """4.1 - Pool contains exactly 119 valid combinations."""
        pool = build_combination_pool()
        assert len(pool.assignments) == 119

    def test_correct_team_counts(self):
        """4.1 - Team 0 has 48, Team 1 has 48, Team 2 has 23 combinations."""
        pool = build_combination_pool()

        team_counts = {0: 0, 1: 0, 2: 0}
        for team_index in pool.assignments.values():
            team_counts[team_index] += 1

        assert team_counts[0] == 48
        assert team_counts[1] == 48
        assert team_counts[2] == 23

    def test_invalid_combination_excluded(self):
        """4.2 - The invalid combination {8, 9, 10} is not in the pool."""
        pool = build_combination_pool()
        assert INVALID_COMBINATION not in pool.assignments

    def test_all_combinations_have_3_distinct_integers(self):
        """4.3 - Every combination contains exactly 3 distinct integers."""
        pool = build_combination_pool()
        for combo in pool.assignments:
            assert len(combo) == 3

    def test_all_ball_numbers_in_valid_range(self):
        """4.3 - All ball numbers are in [1, 10]."""
        pool = build_combination_pool()
        for combo in pool.assignments:
            for ball in combo:
                assert 1 <= ball <= 10

    def test_assignments_are_deterministic(self):
        """4.5 - Repeated calls produce the same assignments."""
        pool1 = build_combination_pool()
        pool2 = build_combination_pool()
        assert pool1.assignments == pool2.assignments


class TestValidateCombinationPool:
    """Tests for validate_combination_pool()."""

    def test_valid_pool_returns_true(self):
        """4.4 - A correctly built pool passes validation."""
        pool = build_combination_pool()
        assert validate_combination_pool(pool) is True

    def test_wrong_total_count_returns_false(self):
        """4.4 - Pool with wrong total combination count fails validation."""
        pool = build_combination_pool()
        # Remove one assignment to corrupt the count
        corrupted_assignments = dict(pool.assignments)
        first_key = next(iter(corrupted_assignments))
        del corrupted_assignments[first_key]

        corrupted_pool = CombinationPool(
            num_balls=pool.num_balls,
            draw_size=pool.draw_size,
            invalid_combination=pool.invalid_combination,
            assignments=corrupted_assignments,
            team_combination_counts=pool.team_combination_counts,
            total_valid=pool.total_valid,
        )
        assert validate_combination_pool(corrupted_pool) is False

    def test_invalid_combination_included_returns_false(self):
        """4.4 - Pool containing the invalid combination fails validation."""
        pool = build_combination_pool()
        corrupted_assignments = dict(pool.assignments)
        # Add the invalid combination
        corrupted_assignments[INVALID_COMBINATION] = 0
        # Remove another to keep count correct
        for key in corrupted_assignments:
            if key != INVALID_COMBINATION:
                del corrupted_assignments[key]
                break

        corrupted_pool = CombinationPool(
            num_balls=pool.num_balls,
            draw_size=pool.draw_size,
            invalid_combination=pool.invalid_combination,
            assignments=corrupted_assignments,
            team_combination_counts=pool.team_combination_counts,
            total_valid=pool.total_valid,
        )
        assert validate_combination_pool(corrupted_pool) is False

    def test_wrong_team_counts_returns_false(self):
        """4.4 - Pool with incorrect team distribution fails validation."""
        pool = build_combination_pool()
        corrupted_assignments = dict(pool.assignments)
        # Reassign one combination from team 2 to team 0
        for combo, team_idx in corrupted_assignments.items():
            if team_idx == 2:
                corrupted_assignments[combo] = 0
                break

        corrupted_pool = CombinationPool(
            num_balls=pool.num_balls,
            draw_size=pool.draw_size,
            invalid_combination=pool.invalid_combination,
            assignments=corrupted_assignments,
            team_combination_counts=pool.team_combination_counts,
            total_valid=pool.total_valid,
        )
        assert validate_combination_pool(corrupted_pool) is False

    def test_out_of_range_ball_numbers_returns_false(self):
        """4.4 - Pool with ball numbers outside [1, 10] fails validation."""
        pool = build_combination_pool()
        corrupted_assignments = dict(pool.assignments)
        # Remove a valid combination and add one with out-of-range balls
        first_key = next(iter(corrupted_assignments))
        team_idx = corrupted_assignments[first_key]
        del corrupted_assignments[first_key]
        corrupted_assignments[frozenset({0, 11, 5})] = team_idx

        corrupted_pool = CombinationPool(
            num_balls=pool.num_balls,
            draw_size=pool.draw_size,
            invalid_combination=pool.invalid_combination,
            assignments=corrupted_assignments,
            team_combination_counts=pool.team_combination_counts,
            total_valid=pool.total_valid,
        )
        assert validate_combination_pool(corrupted_pool) is False

"""NBA-style combination-based lottery engine.

This module implements the combination pool construction and validation
for a permutation-based draft lottery. It uses 10 numbered balls with
3-ball draws to form combinations, pre-assigned to lottery teams.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass

# --- Module-level constants ---

NUM_BALLS: int = 10
DRAW_SIZE: int = 3
TOTAL_COMBINATIONS: int = 120  # C(10, 3)
INVALID_COMBINATION: frozenset[int] = frozenset({8, 9, 10})
VALID_COMBINATIONS: int = 119  # 120 - 1
TEAM_COMBINATION_COUNTS: tuple[int, int, int] = (48, 48, 23)


# --- Data structures ---


@dataclass(frozen=True)
class CombinationPool:
    """Complete assignment of combinations to lottery teams."""

    num_balls: int  # 10
    draw_size: int  # 3
    invalid_combination: frozenset[int]  # {8, 9, 10}
    assignments: dict[frozenset[int], int]  # combination → team_index
    team_combination_counts: tuple[int, ...]  # (48, 48, 23)
    total_valid: int  # 119


@dataclass
class DraftResult:
    """Result of a single ball draw in the lottery."""

    team_index: int
    combination: frozenset[int]


# --- Core functions ---


def build_combination_assignments(
    num_balls: int,
    draw_size: int,
    invalid: frozenset[int],
    team_counts: list[int],
) -> dict[frozenset[int], int]:
    """Assign combinations to teams in a deterministic order.

    Combinations are generated in lexicographic order, the invalid one
    is removed, and then distributed sequentially to teams based on counts.

    Args:
        num_balls: Total number of balls (10).
        draw_size: Balls drawn per combination (3).
        invalid: The one invalid combination to exclude.
        team_counts: Number of combinations per team [48, 48, 23].

    Returns:
        Dict mapping each valid combination (as frozenset) to team index.
    """
    # Generate all C(num_balls, draw_size) combinations in lexicographic order
    all_combos = list(itertools.combinations(range(1, num_balls + 1), draw_size))

    # Remove the invalid combination
    valid_combos = [
        frozenset(c) for c in all_combos if frozenset(c) != invalid
    ]

    # Verify counts add up
    if sum(team_counts) != len(valid_combos):
        raise ValueError(
            f"Team counts sum ({sum(team_counts)}) does not equal "
            f"valid combinations ({len(valid_combos)})"
        )

    # Assign combinations to teams sequentially based on counts
    assignments: dict[frozenset[int], int] = {}
    idx = 0
    for team_index, count in enumerate(team_counts):
        for _ in range(count):
            assignments[valid_combos[idx]] = team_index
            idx += 1

    return assignments


def build_combination_pool() -> CombinationPool:
    """Construct the complete combination pool with team assignments.

    Uses the module-level constants to generate all C(10,3) = 120 combinations
    in lexicographic order, removes the invalid combination {8,9,10}, and assigns
    the remaining 119 combinations to teams: 48 to worst, 48 to 2nd worst,
    23 to 3rd worst.

    Returns:
        A complete CombinationPool instance ready for lottery draws.
    """
    assignments = build_combination_assignments(
        num_balls=NUM_BALLS,
        draw_size=DRAW_SIZE,
        invalid=INVALID_COMBINATION,
        team_counts=list(TEAM_COMBINATION_COUNTS),
    )

    return CombinationPool(
        num_balls=NUM_BALLS,
        draw_size=DRAW_SIZE,
        invalid_combination=INVALID_COMBINATION,
        assignments=assignments,
        team_combination_counts=TEAM_COMBINATION_COUNTS,
        total_valid=VALID_COMBINATIONS,
    )


def validate_combination_pool(pool: CombinationPool) -> bool:
    """Verify all pool invariants.

    Checks:
        - Total combination count equals pool.total_valid (119)
        - Each combination has exactly draw_size distinct balls in [1, num_balls]
        - The invalid combination is excluded
        - Team assignment counts match pool.team_combination_counts
        - No combination is assigned to multiple teams

    Args:
        pool: A CombinationPool instance to validate.

    Returns:
        True if all invariants hold, False otherwise.
    """
    # Verify total combination count
    if len(pool.assignments) != pool.total_valid:
        return False

    # Verify each combination has exactly draw_size distinct balls in [1, num_balls]
    for combo in pool.assignments:
        if len(combo) != pool.draw_size:
            return False
        if not all(1 <= ball <= pool.num_balls for ball in combo):
            return False

    # Verify the invalid combination is excluded
    if pool.invalid_combination in pool.assignments:
        return False

    # Verify team assignment counts match
    team_counts: dict[int, int] = {}
    for team_index in pool.assignments.values():
        team_counts[team_index] = team_counts.get(team_index, 0) + 1

    for i, expected_count in enumerate(pool.team_combination_counts):
        if team_counts.get(i, 0) != expected_count:
            return False

    # No combination can be assigned to multiple teams by construction (dict keys are unique),
    # but verify the total matches the sum of team counts
    if sum(pool.team_combination_counts) != pool.total_valid:
        return False

    return True


def draw_combination(
    pool: CombinationPool,
    already_selected: set[int],
) -> tuple[int, frozenset[int]]:
    """Draw balls until a valid combination belonging to an unselected team is found.

    Args:
        pool: The combination pool with team assignments.
        already_selected: Set of team indices that have already been assigned picks.

    Returns:
        Tuple of (team_index, combination) for the winning draw.

    Raises:
        ValueError: If all teams are already selected (no teams remaining).
    """
    # Guard clause: check if all teams are already selected
    num_teams = len(pool.team_combination_counts)
    if len(already_selected) >= num_teams:
        raise ValueError("No teams remaining for selection")

    while True:
        # Draw DRAW_SIZE balls from NUM_BALLS without replacement
        balls = random.sample(range(1, pool.num_balls + 1), pool.draw_size)
        combination = frozenset(balls)

        # Check if this is the invalid combination
        if combination == pool.invalid_combination:
            continue  # Redraw

        # Look up which team owns this combination
        team_index = pool.assignments[combination]

        # Check if this team has already been selected
        if team_index in already_selected:
            continue  # Redraw

        return team_index, combination

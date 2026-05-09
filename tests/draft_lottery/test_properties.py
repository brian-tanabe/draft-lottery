"""Property-based tests for the permutation-based lottery system.

Uses Hypothesis to verify structural and statistical properties of the
combination pool, drawing logic, and full lottery execution.
"""

import random
from collections import Counter

import hypothesis.strategies as st
from hypothesis import given, settings

from fantasy.draft_lottery.combinations import (
    build_combination_pool,
    draw_combination,
    validate_combination_pool,
)
from fantasy.draft_lottery.simulator import run_lottery
from fantasy.draft_lottery.standings import TeamRecord


def make_team(team_id, name, wins, losses, standing, playoffs=False):
    return TeamRecord(
        team_id=team_id,
        team_name=name,
        wins=wins,
        losses=losses,
        owner=f"Owner {team_id}",
        final_standing=standing,
        made_playoffs=playoffs,
    )


# --- 7.1 Property: pool always contains exactly 119 combinations with valid structure ---


@given(st.just(None))
def test_pool_always_has_119_valid_combinations(_):
    """
    **Validates: Requirements 1.1, 1.2, 1.3, 6.1**

    The combination pool must always contain exactly 119 combinations
    with valid structure: each combination is a frozenset of 3 distinct
    integers in [1, 10], the invalid combination {8, 9, 10} is excluded,
    and team counts are exactly (48, 48, 23).
    """
    pool = build_combination_pool()

    # Pool has exactly 119 combinations
    assert len(pool.assignments) == 119
    assert pool.total_valid == 119

    # Each combination has exactly 3 distinct integers in [1, 10]
    for combo in pool.assignments:
        assert len(combo) == 3
        assert all(1 <= ball <= 10 for ball in combo)

    # Invalid combination is excluded
    assert frozenset({8, 9, 10}) not in pool.assignments

    # Team counts are exactly (48, 48, 23)
    team_counts = Counter(pool.assignments.values())
    assert team_counts[0] == 48
    assert team_counts[1] == 48
    assert team_counts[2] == 23

    # validate_combination_pool agrees
    assert validate_combination_pool(pool) is True


# --- 7.2 Property: draw_combination always returns a team not in already_selected ---


@given(st.frozensets(st.sampled_from([0, 1, 2]), max_size=2))
def test_draw_combination_never_returns_already_selected(already_selected):
    """
    **Validates: Requirements 2.3, 2.4**

    For any valid subset of {0, 1, 2} with size < 3, draw_combination
    must return a team_index that is NOT in already_selected, and the
    returned combination must be valid and map to that team.
    """
    pool = build_combination_pool()
    team_index, combination = draw_combination(pool, set(already_selected))

    # Returned team is not in already_selected
    assert team_index not in already_selected

    # Returned team is a valid team index
    assert team_index in {0, 1, 2}

    # Returned combination is valid (not the invalid one)
    assert combination != frozenset({8, 9, 10})

    # Returned combination maps to the returned team
    assert pool.assignments[combination] == team_index

    # Combination has correct structure
    assert len(combination) == 3
    assert all(1 <= ball <= 10 for ball in combination)


# --- 7.3 Property: run_lottery always assigns all 3 teams exactly once ---


@settings(max_examples=200)
@given(st.integers(min_value=0, max_value=2**32 - 1))
def test_run_lottery_assigns_all_teams_exactly_once(seed):
    """
    **Validates: Requirements 3.1, 4.2**

    For any random seed, run_lottery must assign all 3 lottery teams
    exactly once, with pick numbers 1, 2, 3.
    """
    random.seed(seed)

    teams = [
        make_team(1, "Worst Team", 5, 15, 12),
        make_team(2, "Second Worst", 6, 14, 11),
        make_team(3, "Third Worst", 7, 13, 10),
    ]

    results = run_lottery(teams)

    # Exactly 3 results
    assert len(results) == 3

    # Pick numbers are 1, 2, 3
    pick_numbers = [r.pick_number for r in results]
    assert pick_numbers == [1, 2, 3]

    # All 3 teams appear exactly once
    result_team_ids = [r.team.team_id for r in results]
    expected_team_ids = [t.team_id for t in teams]
    assert sorted(result_team_ids) == sorted(expected_team_ids)
    assert len(set(result_team_ids)) == 3

    # Each result has a valid combination
    for r in results:
        assert r.combination is not None
        assert len(r.combination) == 3
        assert all(1 <= ball <= 10 for ball in r.combination)
        assert r.combination != frozenset({8, 9, 10})

    # Odds are correct
    for r in results:
        assert r.odds > 0.0
        assert r.odds <= 1.0


# --- 7.4 Property: statistical test — Pick 1 frequencies approximate expected odds ---


def test_pick1_frequencies_approximate_expected_odds():
    """
    **Validates: Requirements 4.1**

    Over N=10000 simulations, Pick 1 frequencies should approximate
    48/119 ≈ 0.4034 for teams 0 and 1, and 23/119 ≈ 0.1933 for team 2,
    within a tolerance of 0.02 (2 percentage points).
    """
    N = 10000
    teams = [
        make_team(1, "Worst Team", 5, 15, 12),
        make_team(2, "Second Worst", 6, 14, 11),
        make_team(3, "Third Worst", 7, 13, 10),
    ]

    pick1_counts = Counter()

    for _ in range(N):
        results = run_lottery(teams)
        pick1_winner = results[0].team.team_id
        pick1_counts[pick1_winner] += 1

    # Expected frequencies
    expected_worst = 48 / 119  # ≈ 0.4034
    expected_second = 48 / 119  # ≈ 0.4034
    expected_third = 23 / 119  # ≈ 0.1933

    # Observed frequencies
    observed_worst = pick1_counts[1] / N
    observed_second = pick1_counts[2] / N
    observed_third = pick1_counts[3] / N

    tolerance = 0.02

    assert abs(observed_worst - expected_worst) < tolerance, (
        f"Worst team Pick 1 frequency {observed_worst:.4f} "
        f"deviates from expected {expected_worst:.4f} by more than {tolerance}"
    )
    assert abs(observed_second - expected_second) < tolerance, (
        f"Second worst team Pick 1 frequency {observed_second:.4f} "
        f"deviates from expected {expected_second:.4f} by more than {tolerance}"
    )
    assert abs(observed_third - expected_third) < tolerance, (
        f"Third worst team Pick 1 frequency {observed_third:.4f} "
        f"deviates from expected {expected_third:.4f} by more than {tolerance}"
    )

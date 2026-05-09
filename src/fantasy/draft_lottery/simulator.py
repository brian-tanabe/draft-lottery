"""Lottery simulator using NBA-style combination-based draws."""

from __future__ import annotations

from dataclasses import dataclass

from fantasy.draft_lottery.combinations import build_combination_pool, draw_combination
from fantasy.draft_lottery.standings import TeamRecord


@dataclass
class LotteryResult:
    """Result of a single draft pick assignment."""

    pick_number: int  # Draft position (1-12)
    team: TeamRecord  # The team assigned this pick
    odds: float  # Probability this team had for Pick 1 (0.0-1.0)
    combination: frozenset[int] | None = None  # The drawn combination (None for non-lottery picks)


def run_lottery(lottery_teams: list[TeamRecord], year: int | None = None) -> list[LotteryResult]:
    """
    Run the draft lottery using NBA-style combination draws.

    Uses a combination pool of 119 valid 3-ball combinations (from 10 balls)
    assigned to teams: 48 to worst, 48 to 2nd worst, 23 to 3rd worst.
    Balls are drawn for each pick; if the combination belongs to an already-selected
    team or is invalid, it is discarded and redrawn.

    Args:
        lottery_teams: Exactly 3 teams sorted by wins ascending (worst first).
        year: Season year (unused, kept for API compatibility).

    Returns:
        List of LotteryResult in pick order (1st, 2nd, 3rd).
    """
    if len(lottery_teams) != 3:
        raise ValueError("Lottery requires exactly 3 teams")

    pool = build_combination_pool()
    already_selected: set[int] = set()
    results: list[LotteryResult] = []

    for pick_number in range(1, 4):  # Picks 1, 2, 3
        team_index, combination = draw_combination(pool, already_selected)
        already_selected.add(team_index)

        team = lottery_teams[team_index]
        odds = pool.team_combination_counts[team_index] / pool.total_valid

        results.append(LotteryResult(
            pick_number=pick_number,
            team=team,
            odds=odds,
            combination=combination,
        ))

    return results


def build_full_draft_order(
    lottery_results: list[LotteryResult],
    non_playoff_non_lottery_teams: list[TeamRecord],
    playoff_teams: list[TeamRecord],
) -> list[LotteryResult]:
    """
    Combine lottery results (picks 1-3) with:
    - Non-playoff, non-lottery teams (picks 4-6) ordered by regular season record (worst first)
    - Playoff teams (picks 7-12) ordered by final placement (earliest eliminated first)

    Returns complete 12-pick draft order.
    """
    full_order = list(lottery_results)
    next_pick = len(lottery_results) + 1

    # Picks 4-6: Non-playoff, non-lottery teams by regular season record (worst first)
    for team in non_playoff_non_lottery_teams:
        full_order.append(
            LotteryResult(
                pick_number=next_pick,
                team=team,
                odds=0.0,  # Not lottery-determined
            )
        )
        next_pick += 1

    # Picks 7-12: Playoff teams by final placement (earliest eliminated first)
    for team in playoff_teams:
        full_order.append(
            LotteryResult(
                pick_number=next_pick,
                team=team,
                odds=0.0,  # Not lottery-determined
            )
        )
        next_pick += 1

    return full_order

"""CLI utilities for the fantasy basketball draft lottery."""

from __future__ import annotations

import sys
from datetime import datetime

from fantasy.draft_lottery.simulator import LotteryResult, build_full_draft_order, run_lottery
from fantasy.draft_lottery.standings import (
    get_lottery_teams,
    get_non_playoff_non_lottery_teams,
    get_playoff_teams,
    get_standings,
)

LEAGUE_ID = 22603


def validate_year(year_str: str) -> tuple[bool, str | None]:
    """
    Validate a season year input string.

    Returns a tuple of (is_valid, error_message).
    If valid, error_message is None.
    If invalid, error_message describes the problem.

    Valid years are numeric values between 2000 and current year + 1 (inclusive).
    """
    stripped = year_str.strip()

    # Check if the input is a valid integer
    try:
        year = int(stripped)
    except ValueError:
        return False, "Invalid input. Please enter a numeric year (e.g., 2025)."

    current_year = datetime.now().year
    max_year = current_year + 1

    if year > max_year:
        return False, (
            f"Invalid year. Year cannot be after {max_year}. "
            f"Please enter a year between 2000 and {max_year}."
        )

    if year < 2000:
        return False, (
            f"Invalid year. Please enter a year between 2000 and {max_year}."
        )

    return True, None


def get_season_year() -> int:
    """
    Interactively prompt the user for a valid season year.

    Loops until a valid numeric year between 2000 and current year + 1 is entered.
    Returns the validated year as an integer.
    """
    while True:
        year_input = input("Enter the season year (e.g., 2025 for 2024-2025 season): ")
        is_valid, error_message = validate_year(year_input)
        if is_valid:
            return int(year_input.strip())
        print(f"Error: {error_message}")


def get_credentials() -> tuple[str, str]:
    """
    Prompt the user for ESPN authentication credentials.

    Returns:
        A tuple of (espn_s2, swid) tokens.
    """
    espn_s2 = input("Enter your ESPN espn_s2 token: ")
    swid = input("Enter your ESPN swid token: ")
    return espn_s2, swid


def format_results(draft_order: list[LotteryResult]) -> str:
    """
    Format the complete draft order as a simple numbered list.

    Args:
        draft_order: List of LotteryResult sorted by pick_number.

    Returns:
        Formatted string showing all picks in order.
    """
    lines: list[str] = []
    lines.append("Draft Order:")

    for result in draft_order:
        pick = result.pick_number
        team = result.team
        lines.append(f"  Pick #{pick}: {team.team_name} ({team.owner})")

    return "\n".join(lines)


def format_standings(standings: list, year: int) -> str:
    """
    Format the league standings as a numbered list with records.

    Args:
        standings: List of TeamRecord sorted by wins ascending (worst first).
        year: The season year.

    Returns:
        Formatted string showing standings from best to worst.
    """
    lines: list[str] = []
    lines.append(f"{year - 1}-{year} Season Standings:")

    # Display from best to worst (reverse the worst-first order)
    sorted_best_first = list(reversed(standings))
    for i, team in enumerate(sorted_best_first, start=1):
        lines.append(f"  {i}. {team.team_name} ({team.owner}) - {team.wins}-{team.losses}")

    return "\n".join(lines)


def sanitize_error_message(message: str, espn_s2: str, swid: str) -> str:
    """
    Strip any token values from an error message to prevent credential leakage.

    Replaces occurrences of espn_s2 or swid token values with '[REDACTED]'.

    Args:
        message: The error message to sanitize.
        espn_s2: The ESPN espn_s2 token value to redact.
        swid: The ESPN swid token value to redact.

    Returns:
        The sanitized message with token values replaced.
    """
    sanitized = message
    if espn_s2:
        sanitized = sanitized.replace(espn_s2, "[REDACTED]")
    if swid:
        sanitized = sanitized.replace(swid, "[REDACTED]")
    return sanitized


def run_with_error_handling(year: int, espn_s2: str, swid: str) -> int:
    """
    Execute the draft lottery workflow with comprehensive error handling.

    Calls get_standings, get_lottery_teams, runs the lottery, and builds
    the full draft order. Catches known error types and prints user-friendly
    messages without exposing authentication tokens.

    Args:
        year: The season year to fetch standings for.
        espn_s2: ESPN authentication token.
        swid: ESPN authentication identifier.

    Returns:
        Exit code: 0 on success, 1 on error.
    """
    try:
        standings = get_standings(
            league_id=LEAGUE_ID, year=year, espn_s2=espn_s2, swid=swid
        )
    except ConnectionError:
        print(
            "Error: Unable to reach the ESPN API. "
            "Please check your internet connection and try again."
        )
        return 1
    except ValueError as e:
        error_msg = sanitize_error_message(str(e), espn_s2, swid)
        print(f"Error: {error_msg}")
        return 1
    except PermissionError:
        print(
            "Error: Invalid ESPN credentials. "
            "Please verify your espn_s2 and swid tokens are correct."
        )
        return 1

    # Check for insufficient teams
    if len(standings) < 3:
        print(
            "Error: The league does not have enough teams for a lottery. "
            "At least 3 teams are required."
        )
        return 1

    # Classify teams into tiers
    lottery_teams = get_lottery_teams(standings, count=3)
    non_playoff_teams = get_non_playoff_non_lottery_teams(standings, lottery_count=3)
    playoff_teams = get_playoff_teams(standings)

    # Display standings
    print(format_standings(standings, year))
    print()

    # Run the lottery
    lottery_results = run_lottery(lottery_teams, year=year)

    # Build full draft order
    full_order = build_full_draft_order(lottery_results, non_playoff_teams, playoff_teams)

    # Display results
    print(format_results(full_order))

    return 0

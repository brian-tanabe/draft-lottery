"""CLI entry point for the fantasy basketball draft lottery."""

import sys

from fantasy.draft_lottery.cli import (
    get_credentials,
    get_season_year,
    run_with_error_handling,
    validate_year,
)

__all__ = ["get_season_year", "main", "validate_year"]


def main() -> None:
    """
    Entry point for the draft lottery CLI.

    Prints a welcome banner, collects user inputs (season year and ESPN
    credentials), then delegates to run_with_error_handling which orchestrates
    standings retrieval, tier classification, lottery simulation, and results
    display. Exits with the appropriate status code.
    """
    print("Fantasy Basketball Draft Lottery")
    print("====================================")

    year = get_season_year()
    espn_s2, swid = get_credentials()

    exit_code = run_with_error_handling(year, espn_s2, swid)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

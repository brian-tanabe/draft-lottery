# Draft Lottery

A CLI tool that determines the fantasy basketball draft order for an ESPN league using an NBA-style combination-based lottery.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

## Installation

```bash
uv sync
```

## Usage

```bash
uv run python scripts/draft_lottery.py
```

The tool will prompt you for:

1. **Season year** — e.g., `2025` for the 2024–2025 season
2. **ESPN `espn_s2` token** — your ESPN authentication cookie
3. **ESPN `swid` token** — your ESPN identity cookie

It fetches standings from ESPN, runs the lottery for the bottom 3 teams, and prints the full 12-pick draft order.

### Finding your ESPN credentials

1. Log in to your ESPN fantasy league in a browser
2. Open Developer Tools → Application → Cookies
3. Copy the values for `espn_s2` and `SWID`

## Building a Standalone Binary

You can package the tool as a single executable using PyInstaller (included in dev dependencies).

**Mac:**

```bash
./build/build_mac.sh
```

**Windows:**

```bat
build\build_windows.bat
```

The binary is output to `dist/draft_lottery` (Mac) or `dist\draft_lottery.exe` (Windows). It runs without needing Python or any dependencies installed:

```bash
./dist/draft_lottery
```

## Running Tests

```bash
uv run pytest
```

To run only the property-based tests:

```bash
uv run pytest tests/draft_lottery/test_properties.py
```

## Methodology

The draft order is determined using an NBA-style permutation-based lottery for the bottom 3 teams (by regular season record). The remaining picks are assigned by record and playoff finish.

Teams are ranked worst-first by wins, then losses (more losses = worse), then head-to-head record (more H2H losses = worse) as a tiebreaker. This matches what our ESPN league currently uses for its own playoff tie brekaing records (based on me reverse engineering the second-level tie breaker after head-to-head results).

### Lottery (Picks 1–3)

Ten ping-pong balls numbered 1–10 are used. Three balls are drawn at random (order doesn't matter) to form a combination. There are C(10, 3) = 120 possible combinations. One combination ({8, 9, 10}) is designated invalid and discarded if drawn, leaving 119 valid combinations.

These 119 combinations are pre-assigned to the 3 lottery teams:

| Team | Combinations | Pick 1 Odds |
|------|-------------|-------------|
| Worst record | 48 | 48/119 ≈ 40.3% |
| 2nd worst record | 48 | 48/119 ≈ 40.3% |
| 3rd worst record | 23 | 23/119 ≈ 19.3% |

Combinations are assigned in lexicographic order:
1. The first 48 go to the worst team
2. The next 48 to the second worst
3. The remaining 23 to the third worst

**Drawing process:**

1. Draw 3 balls to form a combination
2. If the combination is invalid ({8, 9, 10}), discard and redraw
3. If the combination belongs to a team that already has a pick, discard and redraw
4. Otherwise, that team receives the current pick
5. Repeat for the next pick until all 3 lottery picks are assigned

### Non-lottery picks (Picks 4–12)

| Picks | Assignment |
|-------|-----------|
| 4–6 | Non-playoff, non-lottery teams by regular season record (worst first) |
| 7–12 | Playoff teams by finish (earliest eliminated picks first, champion picks last) |

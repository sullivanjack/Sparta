"""The custom Sparta tournament handicap model."""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Iterable, Mapping, Sequence

SPARTA_PAR = 70
SPARTA_ALLOWANCE = 0.875
DEFAULT_LOOKBACK_YEARS = 2


def round_handicap(gross_total: int, par: int = SPARTA_PAR) -> float:
    """Return the Sparta handicap value produced by one gross round."""
    if gross_total <= 0:
        raise ValueError("gross total must be positive")
    return (gross_total - par) * SPARTA_ALLOWANCE


def playing_handicap(value: float) -> int:
    """Round a calculated value to the whole stroke used on a scorecard."""
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def next_day_handicap(current_handicap: float, gross_total: int) -> float:
    """Blend the current handicap equally with the latest round value."""
    return (current_handicap + round_handicap(gross_total)) / 2


def next_season_handicap(gross_totals: Iterable[int]) -> float:
    """Average exactly three round values for the following season."""
    totals = tuple(gross_totals)
    if len(totals) != 3:
        raise ValueError("a Sparta season handicap requires exactly three rounds")
    return sum(round_handicap(total) for total in totals) / len(totals)


def handicap_breakdown(
    seasons: Mapping[int, Sequence[tuple[int, int]]],
    target_year: int,
    lookback_years: int = DEFAULT_LOOKBACK_YEARS,
) -> dict:
    """Describe the most recent complete season and whether it is still current.

    ``seasons`` maps a year to ``(day, gross_total)`` pairs. A complete season
    has three distinct days. The latest complete calculation is returned even
    when it is older than the active lookback window so profiles can explain
    why a current Sparta handicap is unavailable.
    """
    if lookback_years < 1:
        raise ValueError("lookback years must be positive")
    complete = []
    for year, values in seasons.items():
        ordered = sorted(values)
        if len(ordered) == 3 and len({day for day, _ in ordered}) == 3:
            complete.append((year, ordered))
    if not complete:
        return {
            "available": False,
            "current": False,
            "target_year": target_year,
            "lookback_years": lookback_years,
        }

    source_year, rounds = max(complete, key=lambda item: item[0])
    value = next_season_handicap(gross for _, gross in rounds)
    current = 1 <= target_year - source_year <= lookback_years
    return {
        "available": True,
        "current": current,
        "target_year": target_year,
        "source_year": source_year,
        "lookback_years": lookback_years,
        "value": value,
        "playing_handicap": playing_handicap(value),
        "rounds": [
            {
                "day": day,
                "gross_total": gross,
                "round_handicap": round_handicap(gross),
            }
            for day, gross in rounds
        ],
    }

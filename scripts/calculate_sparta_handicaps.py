#!/usr/bin/env python3
"""Populate a scorecard's handicap column using the Sparta handicap model."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sparta import handicap_breakdown, load_round, next_day_handicap, playing_handicap  # noqa: E402
from sparta.names import canonical_name  # noqa: E402

ROUND_PATTERN = re.compile(r"Sparta(?P<year>\d{4})_Day(?P<day>\d+)\.csv$")


def archived_scores(root: Path) -> dict[str, dict[int, dict[int, dict[str, int]]]]:
    scores: dict[str, dict[int, dict[int, dict[str, int]]]] = defaultdict(
        lambda: defaultdict(dict)
    )
    for source in sorted(root.glob("data/rounds/[0-9][0-9][0-9][0-9]/Sparta*_Day*.csv")):
        if "_Output" in source.stem:
            continue
        match = ROUND_PATTERN.fullmatch(source.name)
        if not match:
            continue
        year, day = int(match.group("year")), int(match.group("day"))
        _, players = load_round(source)
        for player in players:
            scores[canonical_name(player.name)][year][day] = {
                "gross_total": player.gross_total,
                "handicap": player.handicap,
            }
    return scores


def calculated_handicaps(
    root: Path, target_year: int, day: int, names: list[str]
) -> dict[str, int]:
    if day not in (1, 2, 3):
        raise ValueError("day must be 1, 2, or 3")
    scores = archived_scores(root)
    calculated = {}
    for supplied_name in names:
        name = canonical_name(supplied_name)
        player_scores = scores.get(name, {})
        prior_seasons = {
            year: sorted((season_day, values["gross_total"]) for season_day, values in days.items())
            for year, days in player_scores.items()
            if year < target_year
        }
        breakdown = handicap_breakdown(prior_seasons, target_year)
        current_year = player_scores.get(target_year, {})
        if breakdown.get("current"):
            # The prior season first becomes a whole-stroke Day 1 handicap.
            # In-tournament averages start from that rounded playing value,
            # matching the workbook, then retain precision between later days.
            value = breakdown["playing_handicap"]
        elif day > 1 and 1 in current_year:
            # A new golfer's manually supplied Day 1 handicap seeds the model.
            value = current_year[1]["handicap"]
        else:
            continue
        missing_prior_day = False
        for prior_day in range(1, day):
            prior_round = current_year.get(prior_day)
            if prior_round is None:
                missing_prior_day = True
                break
            value = next_day_handicap(value, prior_round["gross_total"])
        if not missing_prior_day:
            calculated[supplied_name] = playing_handicap(value)
    return calculated


def update_scorecard(path: Path, handicaps: dict[str, int]) -> int:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if not rows or len(rows[0]) != 20 or rows[0][-1] != "Handicap":
        raise ValueError(f"{path}: expected a 20-column Sparta scorecard")
    updated = 0
    for row in rows[2:]:
        if len(row) != 20:
            raise ValueError(f"{path}: every scorecard row must have 20 columns")
        if row[0] in handicaps:
            row[-1] = str(handicaps[row[0]])
            updated += 1
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        csv.writer(handle, lineterminator="\n").writerows(rows)
    temporary.replace(path)
    return updated


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scorecard", type=Path, help="scorecard template to update")
    parser.add_argument("--year", type=int, required=True, help="tournament year")
    parser.add_argument("--day", type=int, choices=(1, 2, 3), required=True)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    with args.scorecard.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    names = [row[0] for row in rows[2:] if row]
    try:
        handicaps = calculated_handicaps(args.root, args.year, args.day, names)
        count = update_scorecard(args.scorecard, handicaps)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"error: {exc}") from exc
    print(f"Updated {count} handicaps in {args.scorecard}")
    missing = [name for name in names if name not in handicaps]
    if missing:
        print(f"Needs manual handicap: {', '.join(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

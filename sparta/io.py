"""CSV input handling for historical and current Sparta scorecards."""

from __future__ import annotations

import csv
from pathlib import Path

from .game import PlayerRound, apply_handicap


class InputError(ValueError):
    """A scorecard cannot be interpreted safely."""


def _integer(value: str, description: str) -> int:
    cleaned = value.strip().replace("+AC0-", "-")
    try:
        return int(cleaned)
    except ValueError as exc:
        raise InputError(f"invalid {description}: {value!r}") from exc


def load_round(path: str | Path) -> tuple[tuple[int, ...], tuple[PlayerRound, ...]]:
    source = Path(path)
    with source.open(newline="", encoding="utf-8-sig") as handle:
        rows = [[cell.strip() for cell in row] for row in csv.reader(handle)]

    if not rows or rows[0] != ["Name", *map(str, range(1, 19)), "Handicap"]:
        raise InputError(f"{source}: expected Name, holes 1-18, Handicap header")

    body = [row for row in rows[1:] if any(row)]
    if not body:
        raise InputError(f"{source}: no score data")

    # Some 2023 exports wrote the handicap row as 20 separate one-cell rows.
    if len(body[0]) == 1 and body[0][0].rstrip("\\") == "Handicap":
        if len(body) < 20 or any(len(row) != 1 for row in body[:20]):
            raise InputError(f"{source}: incomplete vertical handicap row")
        rank_values = [row[0].rstrip("\\") for row in body[1:19]]
        body = [["Handicap", *rank_values, body[19][0].rstrip("\\")], *body[20:]]

    handicap_row = body[0]
    if len(handicap_row) != 20 or handicap_row[0] != "Handicap":
        raise InputError(f"{source}: first data row must contain hole handicap ranks")
    hole_ranks = tuple(_integer(value, "hole handicap rank") for value in handicap_row[1:19])
    if sorted(hole_ranks) != list(range(1, 19)):
        raise InputError(f"{source}: hole handicap ranks must be the numbers 1-18")

    players: list[PlayerRound] = []
    seen_names: set[str] = set()
    for line_number, row in enumerate(body[1:], start=3):
        if len(row) != 20:
            raise InputError(f"{source}:{line_number}: expected 20 columns, found {len(row)}")
        name = row[0].strip()
        if not name:
            raise InputError(f"{source}:{line_number}: player name is blank")
        if name.casefold() in seen_names:
            raise InputError(f"{source}:{line_number}: duplicate player {name!r}")
        seen_names.add(name.casefold())
        gross = tuple(_integer(value, f"score for {name}") for value in row[1:19])
        if any(score <= 0 for score in gross):
            raise InputError(f"{source}:{line_number}: scores must be positive")
        handicap = _integer(row[19], f"handicap for {name}")
        players.append(PlayerRound(name, handicap, gross, apply_handicap(gross, handicap, hole_ranks)))

    if len(players) < 2:
        raise InputError(f"{source}: at least two players are required")
    return hole_ranks, tuple(players)

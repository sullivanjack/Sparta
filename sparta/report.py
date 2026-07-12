"""Serialization helpers for settlements."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from .game import RoundResult


def result_dict(result: RoundResult) -> dict:
    return {
        "player_count": len(result.players),
        "balance_cents": result.balance_cents,
        "wagers": {
            "hole_cents": result.wagers.hole,
            "front_nine_cents": result.wagers.front_nine,
            "back_nine_cents": result.wagers.back_nine,
            "full_round_cents": result.wagers.full_round,
        },
        "players": [
            {
                "name": item.player.name,
                "handicap": item.player.handicap,
                "gross_scores": list(item.player.gross_scores),
                "net_scores": list(item.player.net_scores),
                "gross_total": item.player.gross_total,
                "net_total": item.player.net_total,
                "holes": item.holes.as_dict(),
                "front_nine": item.front_nine.as_dict(),
                "back_nine": item.back_nine.as_dict(),
                "full_round": item.full_round.as_dict(),
                "total_cents": item.total_cents,
                "total": item.total_cents / 100,
            }
            for item in result.players
        ],
        "holes": [
            {"hole": hole.hole, "ranking": [list(group) for group in hole.ranking]}
            for hole in result.holes
        ],
    }


def write_json(result: RoundResult, path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        json.dump(result_dict(result), handle, indent=2)
        handle.write("\n")


def write_csv(result: RoundResult, path: str | Path) -> None:
    with Path(path).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "Player", "Handicap", "Gross", "Net", "Hole Wins", "Hole Losses",
                "Holes", "Front 9", "Back 9", "Full 18", "Total",
            ]
        )
        for item in sorted(result.players, key=lambda player: player.total_cents, reverse=True):
            writer.writerow(
                [
                    item.player.name,
                    item.player.handicap,
                    item.player.gross_total,
                    item.player.net_total,
                    item.holes.wins,
                    item.holes.losses,
                    f"{item.holes.amount_cents / 100:.2f}",
                    f"{item.front_nine.amount_cents / 100:.2f}",
                    f"{item.back_nine.amount_cents / 100:.2f}",
                    f"{item.full_round.amount_cents / 100:.2f}",
                    f"{item.total_cents / 100:.2f}",
                ]
            )

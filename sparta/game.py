"""Pure scoring rules for the Sparta golf game.

Money is represented as integer cents throughout so a settlement never acquires
floating-point rounding artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Wagers:
    hole: int = 10
    front_nine: int = 50
    back_nine: int = 50
    full_round: int = 100


DEFAULT_WAGERS = Wagers()


@dataclass(frozen=True)
class PlayerRound:
    name: str
    handicap: int
    gross_scores: tuple[int, ...]
    net_scores: tuple[int, ...]

    @property
    def gross_total(self) -> int:
        return sum(self.gross_scores)

    @property
    def net_total(self) -> int:
        return sum(self.net_scores)


@dataclass(frozen=True)
class BetResult:
    wins: int
    losses: int
    amount_cents: int

    def as_dict(self) -> dict[str, int | float]:
        return {
            "wins": self.wins,
            "losses": self.losses,
            "amount_cents": self.amount_cents,
            "amount": self.amount_cents / 100,
        }


@dataclass(frozen=True)
class PlayerResult:
    player: PlayerRound
    holes: BetResult
    front_nine: BetResult
    back_nine: BetResult
    full_round: BetResult

    @property
    def total_cents(self) -> int:
        return sum(
            bet.amount_cents
            for bet in (self.holes, self.front_nine, self.back_nine, self.full_round)
        )


@dataclass(frozen=True)
class HoleResult:
    hole: int
    ranking: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class RoundResult:
    players: tuple[PlayerResult, ...]
    holes: tuple[HoleResult, ...]
    wagers: Wagers

    @property
    def balance_cents(self) -> int:
        return sum(player.total_cents for player in self.players)


def apply_handicap(
    gross_scores: Iterable[int], handicap: int, hole_ranks: Iterable[int]
) -> tuple[int, ...]:
    """Return net scores using standard stroke allocation by hole rank."""
    gross = tuple(gross_scores)
    ranks = tuple(hole_ranks)
    if len(gross) != 18 or len(ranks) != 18:
        raise ValueError("a round and its handicap ranks must each contain 18 holes")
    if handicap < 0:
        raise ValueError("player handicap cannot be negative")

    full_strokes, extra_strokes = divmod(handicap, 18)
    return tuple(
        score - full_strokes - (1 if rank <= extra_strokes else 0)
        for score, rank in zip(gross, ranks)
    )


def _pairwise(values: list[int], stake: int) -> list[BetResult]:
    results: list[BetResult] = []
    for value in values:
        wins = sum(value < other for other in values)
        losses = sum(value > other for other in values)
        results.append(BetResult(wins, losses, (wins - losses) * stake))
    return results


def _hole_outcomes(players: tuple[PlayerRound, ...]) -> tuple[list[BetResult], tuple[HoleResult, ...]]:
    wins = [0] * len(players)
    losses = [0] * len(players)
    hole_results: list[HoleResult] = []

    for hole_index in range(18):
        # Sparta ties are broken by the next hole, then the next, through 18.
        keys = [player.net_scores[hole_index:] for player in players]
        for index, key in enumerate(keys):
            wins[index] += sum(key < other for other in keys)
            losses[index] += sum(key > other for other in keys)

        ordered = sorted(range(len(players)), key=lambda index: keys[index])
        ranking: list[tuple[str, ...]] = []
        for position, index in enumerate(ordered):
            previous_index = ordered[position - 1] if position else None
            if previous_index is not None and keys[index] == keys[previous_index]:
                ranking[-1] = (*ranking[-1], players[index].name)
            else:
                ranking.append((players[index].name,))
        hole_results.append(HoleResult(hole_index + 1, tuple(ranking)))

    return [BetResult(w, l, 0) for w, l in zip(wins, losses)], tuple(hole_results)


def settle_round(
    players: Iterable[PlayerRound], wagers: Wagers = DEFAULT_WAGERS
) -> RoundResult:
    players_tuple = tuple(players)
    if len(players_tuple) < 2:
        raise ValueError("a Sparta round requires at least two players")

    hole_counts, hole_results = _hole_outcomes(players_tuple)
    hole_bets = [
        BetResult(result.wins, result.losses, (result.wins - result.losses) * wagers.hole)
        for result in hole_counts
    ]
    front = _pairwise([sum(p.net_scores[:9]) for p in players_tuple], wagers.front_nine)
    back = _pairwise([sum(p.net_scores[9:]) for p in players_tuple], wagers.back_nine)
    full = _pairwise([sum(p.net_scores) for p in players_tuple], wagers.full_round)

    results = tuple(
        PlayerResult(player, hole_bets[i], front[i], back[i], full[i])
        for i, player in enumerate(players_tuple)
    )
    round_result = RoundResult(results, hole_results, wagers)
    if round_result.balance_cents != 0:
        raise AssertionError("settlement is not balanced")
    return round_result

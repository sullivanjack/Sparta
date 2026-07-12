#!/usr/bin/env python3
"""Build the static site's historical dataset from source scorecards."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sparta import InputError, load_round, settle_round  # noqa: E402
from sparta.report import result_dict  # noqa: E402

ROUND_PATTERN = re.compile(r"Sparta(?P<year>\d{4})_Day(?P<day>\d+)\.csv$")
ALIASES = {
    "Leo": "Leo Berhost",
    "Ralph": "Ralph Reis",
    "Tim Stefl": "Tim Steffl",
}
COURSE_PARS = (4, 4, 4, 5, 3, 3, 4, 4, 4) * 2
COURSE_RATING = 67.6
SLOPE_RATING = 112
PCC_ADJUSTMENT = 0


def canonical_name(name: str) -> str:
    return ALIASES.get(name, name)


def round_tenth(value: float) -> float:
    return float(Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def handicap_index(differentials: list[float]) -> dict:
    count = min(len(differentials), 20)
    recent = differentials[:20]
    if count < 3:
        return {"eligible": False, "score_count": count, "index": None, "differentials_used": 0}
    if count == 3:
        used, adjustment = 1, -2.0
    elif count == 4:
        used, adjustment = 1, -1.0
    elif count == 5:
        used, adjustment = 1, 0.0
    elif count == 6:
        used, adjustment = 2, -1.0
    elif count <= 8:
        used, adjustment = 2, 0.0
    elif count <= 11:
        used, adjustment = 3, 0.0
    elif count <= 14:
        used, adjustment = 4, 0.0
    elif count <= 16:
        used, adjustment = 5, 0.0
    elif count <= 18:
        used, adjustment = 6, 0.0
    elif count == 19:
        used, adjustment = 7, 0.0
    else:
        used, adjustment = 8, 0.0
    selected = sorted(recent)[:used]
    index = min(54.0, round_tenth(sum(selected) / used + adjustment))
    return {
        "eligible": True,
        "score_count": count,
        "index": index,
        "differentials_used": used,
        "best_differential": min(recent),
        "counting_differentials": selected,
    }


def adjustment_lookup(adjustments: list[dict]) -> dict[tuple[int, int, str], int]:
    return {
        (item["year"], item["day"], canonical_name(item["player"])): item["net_strokes"]
        for item in adjustments
    }


def build_seasons(rounds: list[dict], adjustments: list[dict]) -> list[dict]:
    adjustment_by_player = adjustment_lookup(adjustments)
    seasons = []
    for year in sorted({round_["year"] for round_ in rounds}, reverse=True):
        year_rounds = sorted(
            (round_ for round_ in rounds if round_["year"] == year),
            key=lambda round_: round_["day"],
        )
        players: dict[str, dict] = {}
        for round_ in year_rounds:
            for player in round_["players"]:
                name = player["canonical_name"]
                adjustment = adjustment_by_player.get((year, round_["day"], name), 0)
                official_net = player["net_total"] + adjustment
                item = players.setdefault(
                    name,
                    {
                        "name": name, "rounds": 0, "total_cents": 0, "total_net": 0,
                        "hole_wins": 0, "hole_losses": 0, "day_scores": {}, "day_handicaps": {},
                    },
                )
                item["rounds"] += 1
                item["total_cents"] += player["total_cents"]
                item["total_net"] += official_net
                item["hole_wins"] += player["holes"]["wins"]
                item["hole_losses"] += player["holes"]["losses"]
                item["day_scores"][str(round_["day"])] = official_net
                item["day_handicaps"][str(round_["day"])] = player["handicap"]

        standings = list(players.values())
        for player in standings:
            player["complete"] = player["rounds"] == len(year_rounds)
            player["average_net"] = player["total_net"] / player["rounds"]
        standings.sort(key=lambda player: (not player["complete"], player["total_net"], player["name"]))
        for rank, player in enumerate(standings, 1):
            player["rank"] = rank
        money_standings = sorted(
            standings, key=lambda player: (-player["total_cents"], player["name"])
        )
        for rank, player in enumerate(money_standings, 1):
            player["money_rank"] = rank
        seasons.append(
            {
                "year": year,
                "round_count": len(year_rounds),
                "competitor_count": len(standings),
                "scorecard_count": sum(round_["player_count"] for round_ in year_rounds),
                "standings": standings,
                "money_standings": money_standings,
            }
        )
    return seasons


def build_player_profiles(rounds: list[dict], seasons: list[dict]) -> dict[str, dict]:
    profiles: dict[str, dict] = {}
    for round_ in rounds:
        for player in round_["players"]:
            name = player["canonical_name"]
            profile = profiles.setdefault(
                name,
                {
                    "name": name, "rounds": 0, "total_cents": 0, "hole_wins": 0,
                    "hole_losses": 0, "gross_total": 0, "net_total": 0,
                    "best_net": None, "best_gross": None, "worst_gross": None,
                    "birdies": 0, "eagles": 0, "double_bogeys_or_worse": 0,
                    "years": {}, "score_differentials": [],
                },
            )
            profile["rounds"] += 1
            profile["total_cents"] += player["total_cents"]
            profile["hole_wins"] += player["holes"]["wins"]
            profile["hole_losses"] += player["holes"]["losses"]
            profile["gross_total"] += player["gross_total"]
            profile["net_total"] += player["net_total"]
            profile["best_net"] = min(profile["best_net"], player["net_total"]) if profile["best_net"] is not None else player["net_total"]
            profile["best_gross"] = min(profile["best_gross"], player["gross_total"]) if profile["best_gross"] is not None else player["gross_total"]
            profile["worst_gross"] = max(profile["worst_gross"], player["gross_total"]) if profile["worst_gross"] is not None else player["gross_total"]
            relative_scores = [score - par for score, par in zip(player["gross_scores"], round_["pars"])]
            profile["birdies"] += sum(score == -1 for score in relative_scores)
            profile["eagles"] += sum(score <= -2 for score in relative_scores)
            profile["double_bogeys_or_worse"] += sum(score >= 2 for score in relative_scores)
            profile["score_differentials"].append(player["score_differential"])
            year = profile["years"].setdefault(
                str(round_["year"]),
                {"year": round_["year"], "rounds": 0, "total_cents": 0, "net_total": 0, "hole_wins": 0, "hole_losses": 0},
            )
            year["rounds"] += 1
            year["total_cents"] += player["total_cents"]
            year["net_total"] += player["net_total"]
            year["hole_wins"] += player["holes"]["wins"]
            year["hole_losses"] += player["holes"]["losses"]

    standings_by_year = {season["year"]: season["standings"] for season in seasons}
    for profile in profiles.values():
        profile["average_net"] = profile["net_total"] / profile["rounds"]
        profile["season_count"] = len(profile["years"])
        finishes = []
        for year in profile["years"].values():
            year["average_net"] = year["net_total"] / year["rounds"]
            standing = next(item for item in standings_by_year[year["year"]] if item["name"] == profile["name"])
            year["finish"] = standing["rank"]
            finishes.append(standing["rank"])
        profile["seasons"] = sorted(profile.pop("years").values(), key=lambda item: item["year"], reverse=True)
        profile["first_place_finishes"] = finishes.count(1)
        profile["second_place_finishes"] = finishes.count(2)
        profile["third_place_finishes"] = finishes.count(3)
        profile["best_finish"] = min(finishes)
        profile["worst_finish"] = max(finishes)
        profile["world_handicap"] = handicap_index(profile.pop("score_differentials"))
    return profiles


def build(root: Path) -> dict:
    adjustments_path = root / "data/tournament_adjustments.json"
    with adjustments_path.open(encoding="utf-8") as handle:
        tournament_adjustments = json.load(handle)
    rounds = []
    errors = []
    stats: dict[str, dict] = defaultdict(
        lambda: {
            "rounds": 0, "total_cents": 0, "hole_wins": 0, "hole_losses": 0,
            "gross_total": 0, "net_total": 0, "best_net": None, "years": set(),
        }
    )

    inputs = sorted(root.glob("data/rounds/[0-9][0-9][0-9][0-9]/Sparta*_Day*.csv"))
    for source in inputs:
        if "_Output" in source.stem:
            continue
        match = ROUND_PATTERN.search(source.name)
        if not match:
            continue
        year, day = int(match.group("year")), int(match.group("day"))
        try:
            hole_ranks, players = load_round(source)
            result = settle_round(players)
        except (InputError, ValueError) as exc:
            errors.append({"source": str(source.relative_to(root)), "error": str(exc)})
            continue

        serialized = result_dict(result)
        serialized.update(
            {
                "id": f"{year}-day-{day}", "year": year, "day": day,
                "label": f"{year} · Day {day}", "source": str(source.relative_to(root)),
                "hole_handicaps": list(hole_ranks), "pars": list(COURSE_PARS),
            }
        )
        for player in serialized["players"]:
            player["canonical_name"] = canonical_name(player["name"])
            player["gross_front"] = sum(player["gross_scores"][:9])
            player["gross_back"] = sum(player["gross_scores"][9:])
            player["net_front"] = sum(player["net_scores"][:9])
            player["net_back"] = sum(player["net_scores"][9:])
            adjusted_scores = [
                min(gross, par + 2 + (gross - net))
                for gross, net, par in zip(player["gross_scores"], player["net_scores"], COURSE_PARS)
            ]
            player["adjusted_gross_total"] = sum(adjusted_scores)
            player["score_differential"] = round_tenth(
                (113 / SLOPE_RATING)
                * (player["adjusted_gross_total"] - COURSE_RATING - PCC_ADJUSTMENT)
            )
        net_order = sorted(
            serialized["players"],
            key=lambda player: (player["net_total"], player["gross_total"], player["name"]),
        )
        for rank, player in enumerate(net_order, 1):
            player["net_rank"] = rank
        serialized["players"].sort(key=lambda player: player["net_rank"])
        rounds.append(serialized)

        for item in result.players:
            name = canonical_name(item.player.name)
            stat = stats[name]
            stat["rounds"] += 1
            stat["total_cents"] += item.total_cents
            stat["hole_wins"] += item.holes.wins
            stat["hole_losses"] += item.holes.losses
            stat["gross_total"] += item.player.gross_total
            stat["net_total"] += item.player.net_total
            stat["best_net"] = min(stat["best_net"], item.player.net_total) if stat["best_net"] is not None else item.player.net_total
            stat["years"].add(year)

    leaderboard = []
    for name, stat in stats.items():
        rounds_played = stat["rounds"]
        leaderboard.append(
            {
                "name": name,
                "rounds": rounds_played,
                "years": sorted(stat["years"]),
                "total_cents": stat["total_cents"],
                "total": stat["total_cents"] / 100,
                "average": stat["total_cents"] / rounds_played / 100,
                "hole_wins": stat["hole_wins"],
                "hole_losses": stat["hole_losses"],
                "average_gross": stat["gross_total"] / rounds_played,
                "average_net": stat["net_total"] / rounds_played,
                "best_net": stat["best_net"],
            }
        )
    leaderboard.sort(key=lambda player: (-player["total_cents"], player["name"]))
    rounds.sort(key=lambda round_: (round_["year"], round_["day"]), reverse=True)
    seasons = build_seasons(rounds, tournament_adjustments)
    player_profiles = build_player_profiles(rounds, seasons)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rules_version": 1,
        "course": {
            "holes": 18, "par": sum(COURSE_PARS), "pars": list(COURSE_PARS),
            "rating": COURSE_RATING, "slope": SLOPE_RATING, "pcc": PCC_ADJUSTMENT,
        },
        "round_count": len(rounds),
        "years": sorted({round_["year"] for round_ in rounds}, reverse=True),
        "aliases": ALIASES,
        "tournament_adjustments": tournament_adjustments,
        "errors": errors,
        "leaderboard": leaderboard,
        "seasons": seasons,
        "player_profiles": player_profiles,
        "rounds": rounds,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/data/sparta.json")
    args = parser.parse_args()
    data = build(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")
    print(f"Built {len(data['rounds'])} rounds with {len(data['errors'])} errors → {args.output}")
    for error in data["errors"]:
        print(f"warning: {error['source']}: {error['error']}", file=sys.stderr)
    return 1 if data["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())

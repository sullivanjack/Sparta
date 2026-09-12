from pathlib import Path
import json
import tempfile
import unittest

from sparta.game import PlayerRound, Wagers, apply_handicap, settle_round
from sparta.handicap import (
    handicap_breakdown,
    next_day_handicap,
    next_season_handicap,
    playing_handicap,
    round_handicap,
)
from sparta.io import load_round
from scripts.calculate_sparta_handicaps import calculated_handicaps
from scripts.build_site_data import build


ROOT = Path(__file__).resolve().parents[1]


def player(name, scores):
    values = tuple(scores)
    return PlayerRound(name, 0, values, values)


class HandicapTests(unittest.TestCase):
    def test_allocates_multiple_strokes_and_remainder(self):
        gross = (5,) * 18
        ranks = tuple(range(1, 19))
        self.assertEqual(apply_handicap(gross, 20, ranks), (3, 3, *(4,) * 16))

    def test_rejects_negative_handicap(self):
        with self.assertRaises(ValueError):
            apply_handicap((5,) * 18, -1, range(1, 19))

    def test_sparta_handicap_matches_workbook_model(self):
        self.assertEqual(round_handicap(108), 33.25)
        day_two = next_day_handicap(23.666666666666668, 108)
        self.assertAlmostEqual(day_two, 28.458333333333336)
        self.assertEqual(playing_handicap(day_two), 28)
        self.assertAlmostEqual(next_season_handicap([108, 102, 94]), 27.416666666666668)

    def test_sparta_handicap_supports_two_year_fallback(self):
        result = handicap_breakdown(
            {2024: [(1, 96), (2, 99), (3, 98)]}, target_year=2026
        )
        self.assertTrue(result["current"])
        self.assertEqual((result["source_year"], result["playing_handicap"]), (2024, 24))

    def test_new_golfer_day_one_handicap_seeds_day_two(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rounds = root / "data/rounds/2026"
            rounds.mkdir(parents=True)
            (rounds / "Sparta2026_Day1.csv").write_text(
                "Name,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,Handicap\n"
                "Handicap,16,18,6,10,12,8,2,4,14,15,17,3,9,11,7,1,5,13,-1\n"
                "Jon Moreau,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,5,18\n"
                "Sam Sullivan,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,6,24\n",
                encoding="utf-8",
            )
            result = calculated_handicaps(root, 2026, 2, ["Jon Moreau"])
            self.assertEqual(result, {"Jon Moreau": 18})


class SettlementTests(unittest.TestCase):
    def test_lower_score_wins_and_round_balances(self):
        result = settle_round(
            [player("A", (3,) * 18), player("B", (4,) * 18)],
            Wagers(hole=10, front_nine=50, back_nine=50, full_round=100),
        )
        self.assertEqual(result.balance_cents, 0)
        self.assertEqual(result.players[0].total_cents, 380)
        self.assertEqual(result.players[1].total_cents, -380)

    def test_hole_tie_uses_next_hole(self):
        a = player("A", (4, 3, *(4,) * 16))
        b = player("B", (4, 5, *(4,) * 16))
        result = settle_round([a, b])
        self.assertEqual(result.holes[0].ranking, (("A",), ("B",)))

    def test_tie_through_eighteen_is_a_push(self):
        result = settle_round([player("A", (4,) * 18), player("B", (4,) * 18)])
        self.assertEqual(result.players[0].total_cents, 0)
        self.assertEqual(result.holes[0].ranking, (("A", "B"),))


class HistoricalDataTests(unittest.TestCase):
    def test_every_historical_input_loads_and_balances(self):
        sources = sorted(ROOT.glob("data/rounds/[0-9][0-9][0-9][0-9]/Sparta*_Day*.csv"))
        sources = [source for source in sources if "_Output" not in source.stem]
        self.assertEqual(len(sources), 19)
        for source in sources:
            with self.subTest(source=source):
                _, players = load_round(source)
                self.assertEqual(settle_round(players).balance_cents, 0)

    def test_tournament_adjustments_reference_real_rounds_and_players(self):
        with (ROOT / "data/tournament_adjustments.json").open() as handle:
            adjustments = json.load(handle)
        for adjustment in adjustments:
            source = ROOT / f"data/rounds/{adjustment['year']}/Sparta{adjustment['year']}_Day{adjustment['day']}.csv"
            _, players = load_round(source)
            self.assertIn(adjustment["player"], {player.name for player in players})
            self.assertIsInstance(adjustment["net_strokes"], int)

    def test_generated_rankings_and_profiles_share_the_same_finishes(self):
        data = build(ROOT)
        for season in data["seasons"]:
            for standing in season["standings"]:
                profile = data["player_profiles"][standing["name"]]
                profile_season = next(item for item in profile["seasons"] if item["year"] == season["year"])
                self.assertEqual(profile_season["finish"], standing["rank"])

    def test_partial_historical_scores_are_ranked_and_pre_2019(self):
        seasons = build(ROOT)["historical_seasons"]
        self.assertEqual([season["year"] for season in seasons], list(range(2018, 2000, -1)))
        self.assertEqual(sum(season["competitor_count"] for season in seasons), 236)
        for season in seasons:
            self.assertEqual(
                season["standings"],
                sorted(season["standings"], key=lambda player: (player["net_total"], player["name"])),
            )
            for player in season["standings"]:
                expected_rank = 1 + sum(
                    other["net_total"] < player["net_total"] for other in season["standings"]
                )
                self.assertEqual(player["rank"], expected_rank)

    def test_2026_sparta_handicaps_use_latest_season_within_two_years(self):
        calculated = calculated_handicaps(
            ROOT, 2026, 1, ["Davie Brauer", "Bob Breslin", "Greg Nestor", "Grant Flynn", "Jon Moreau"]
        )
        self.assertEqual(
            calculated,
            {"Davie Brauer": 27, "Bob Breslin": 24, "Greg Nestor": 20, "Grant Flynn": 32},
        )
        data = build(ROOT)
        for name, source_year, handicap in (
            ("Davie Brauer", 2025, 27),
            ("Bob Breslin", 2024, 24),
            ("Greg Nestor", 2024, 20),
        ):
            result = data["player_profiles"][name]["sparta_handicap"]
            self.assertTrue(result["current"])
            self.assertEqual((result["source_year"], result["playing_handicap"]), (source_year, handicap))

    def test_2026_is_an_in_progress_one_round_season(self):
        data = build(ROOT)
        season = next(item for item in data["seasons"] if item["year"] == 2026)
        self.assertEqual((season["round_count"], season["complete"]), (1, False))
        self.assertEqual(season["competitor_count"], 24)
        self.assertTrue(all(player["up_to_date"] for player in season["standings"]))

    def test_official_2023_adjustment_is_applied_once(self):
        data = build(ROOT)
        season = next(item for item in data["seasons"] if item["year"] == 2023)
        chris = next(item for item in season["standings"] if item["name"] == "Chris Flynn")
        self.assertEqual(chris["day_scores"]["1"], 68)
        self.assertEqual(chris["day_handicaps"]["1"], 21)
        self.assertEqual(chris["total_net"], 199)
        self.assertEqual(chris["rank"], 1)

    def test_2021_day_one_is_not_the_duplicated_day_two_export(self):
        _, day_one = load_round(ROOT / "data/rounds/2021/Sparta2021_Day1.csv")
        _, day_two = load_round(ROOT / "data/rounds/2021/Sparta2021_Day2.csv")
        day_one_scores = {player.name: player.gross_scores for player in day_one}
        day_two_scores = {player.name: player.gross_scores for player in day_two}
        self.assertNotEqual(day_one_scores["Jack Sullivan"], day_two_scores["Jack Sullivan"])
        jack = next(player for player in day_one if player.name == "Jack Sullivan")
        self.assertEqual((jack.gross_total, jack.handicap, jack.net_total), (109, 31, 78))

    def test_reconstructed_2021_finish_for_jack(self):
        data = build(ROOT)
        season = next(item for item in data["seasons"] if item["year"] == 2021)
        jack = next(item for item in season["standings"] if item["name"] == "Jack Sullivan")
        self.assertEqual(jack["day_scores"], {"1": 78, "2": 66, "3": 69})
        self.assertEqual((jack["total_net"], jack["rank"]), (213, 6))

    def test_round_display_totals_are_precomputed(self):
        data = build(ROOT)
        for round_ in data["rounds"]:
            self.assertEqual(
                [player["net_rank"] for player in round_["players"]],
                list(range(1, round_["player_count"] + 1)),
            )
            for player in round_["players"]:
                self.assertEqual(player["gross_front"] + player["gross_back"], player["gross_total"])
                self.assertEqual(player["net_front"] + player["net_back"], player["net_total"])


if __name__ == "__main__":
    unittest.main()

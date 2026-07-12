from pathlib import Path
import json
import unittest

from sparta.game import PlayerRound, Wagers, apply_handicap, settle_round
from sparta.io import load_round
from scripts.build_site_data import build, handicap_index


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
        self.assertEqual(len(sources), 18)
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
                self.assertIn("adjusted_gross_total", player)
                self.assertIsInstance(player["score_differential"], float)

    def test_world_handicap_fewer_than_twenty_table(self):
        self.assertFalse(handicap_index([10.0, 11.0])["eligible"])
        self.assertEqual(handicap_index([10.0, 12.0, 14.0])["index"], 8.0)
        six_scores = handicap_index([10.0, 12.0, 14.0, 16.0, 18.0, 20.0])
        self.assertEqual((six_scores["differentials_used"], six_scores["index"]), (2, 10.0))
        twenty_scores = handicap_index([float(value) for value in range(1, 21)])
        self.assertEqual((twenty_scores["differentials_used"], twenty_scores["index"]), (8, 4.5))


if __name__ == "__main__":
    unittest.main()

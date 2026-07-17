import unittest
from dataclasses import replace
from pathlib import Path

from services.analytics.fantaanalytics.importer import import_csv
from services.analytics.fantaanalytics.pricing import LeagueConfig, predict_prices
from services.analytics.fantaanalytics.scoring import score_players


class ScoringAndPricingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.players, cls.issues = import_csv(Path("data/samples/demo_players.csv"))
        cls.scores = score_players(cls.players)

    def test_demo_players_receive_explainable_bounded_scores(self):
        self.assertEqual(self.issues, [])
        self.assertEqual(len(self.scores), len(self.players))
        for score in self.scores:
            self.assertGreaterEqual(score.score, 0)
            self.assertLessEqual(score.score, 100)
            self.assertAlmostEqual(
                score.score, sum(item.value for item in score.components), places=1
            )
            self.assertIn("Profilo", score.explanation_it)

    def test_partial_pool_only_allocates_its_covered_budget(self):
        predictions = predict_prices(self.scores, LeagueConfig())
        self.assertEqual(len(predictions), len(self.scores))
        self.assertLess(sum(item.baseline_price for item in predictions), 10_000)
        self.assertTrue(all(item.maximum_recommended_price >= 1 for item in predictions))

    def test_complete_pool_distribution_matches_league_budget(self):
        league = LeagueConfig()
        complete_scores = []
        for role, required_slots in league.role_slots.items():
            template = next(score for score in self.scores if score.fantasy_role == role)
            for index in range(league.participants * required_slots):
                complete_scores.append(replace(template, external_id=f"{role}-{index}"))
        predictions = predict_prices(complete_scores, league)
        self.assertAlmostEqual(sum(item.baseline_price for item in predictions), 10_000, places=2)

    def test_rejects_invalid_role_budget_weights(self):
        invalid = LeagueConfig(role_budget_shares={"P": 0.1, "D": 0.1, "C": 0.1, "A": 0.1})
        with self.assertRaises(ValueError):
            predict_prices(self.scores, invalid)

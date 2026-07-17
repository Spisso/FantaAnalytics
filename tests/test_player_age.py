import unittest
from datetime import date

from models.player import Player
from services.analytics.fantaanalytics.normalization import calculate_age


class PlayerAgeTest(unittest.TestCase):
    def test_age_is_derived_from_explicit_reference_date(self):
        player = Player("Mario", "Rossi", "Roma", "C", date(2000, 7, 18))
        self.assertEqual(player.age_on(date(2026, 7, 17)), 25)
        self.assertEqual(calculate_age(date(2000, 7, 18), date(2026, 7, 18)), 26)

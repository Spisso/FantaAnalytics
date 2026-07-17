import json
import unittest
from pathlib import Path

from services.analytics.fantaanalytics.contracts import validate_player_v1


class PlayerContractTest(unittest.TestCase):
    def _example(self, filename):
        path = Path("contracts/examples") / filename
        return json.loads(path.read_text(encoding="utf-8"))

    def test_valid_player_example_satisfies_contract(self):
        self.assertEqual(validate_player_v1(self._example("player.v1.valid.json")), [])

    def test_invalid_player_example_reports_contract_errors(self):
        errors = validate_player_v1(self._example("player.v1.invalid.json"))
        self.assertGreaterEqual(len(errors), 4)
        self.assertTrue(any(error.startswith("schema_version") for error in errors))

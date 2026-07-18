import unittest
from unittest.mock import patch

import main


class MainPipelineTest(unittest.TestCase):
    def test_main_delegates_to_canonical_transfermarkt_command(self):
        with patch.object(main, "analytics_cli", return_value=0) as cli:
            self.assertEqual(main.main(), 0)
        arguments = cli.call_args.args[0]
        self.assertEqual(arguments[0], "scrape-transfermarkt")
        self.assertIn("data/processed/fantaanalytics.db", arguments)


if __name__ == "__main__":
    unittest.main()

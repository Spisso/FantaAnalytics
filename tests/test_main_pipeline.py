import os
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd
import requests

import main


class MainPipelineTest(unittest.TestCase):

    def test_load_players_uses_csv_backup_when_scraping_fails(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            csv_path = os.path.join(tmp_dir, "players.csv")
            pd.DataFrame([
                {"name": "Lautaro", "team": "Inter", "birth_date": "22/08/1997", "position": "Punta centrale", "nationality": "Argentina"}
            ]).to_csv(csv_path, index=False)

            with patch.object(main, "CSV_PATH", csv_path), patch("main.TransfermarktScraper") as scraper_cls:
                scraper_cls.return_value.get_players.side_effect = requests.RequestException("boom")
                players = main.load_players()

            self.assertEqual(players[0]["name"], "Lautaro")


if __name__ == "__main__":
    unittest.main()

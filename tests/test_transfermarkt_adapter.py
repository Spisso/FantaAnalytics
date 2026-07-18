import csv
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import requests

from services.analytics.fantaanalytics.cli import main as cli_main
from services.analytics.fantaanalytics.import_service import PlayerImportService
from services.analytics.fantaanalytics.importer import normalize_row
from services.analytics.fantaanalytics.normalization import parse_market_value
from services.analytics.fantaanalytics.persistence import CanonicalRepository, MigrationRunner
from services.analytics.fantaanalytics.transfermarkt_adapter import (
    canonicalize_players,
    write_canonical_csv,
)


class TransfermarktAdapterTest(unittest.TestCase):
    def setUp(self):
        self.player = {
            "external_id": "transfermarkt:406625",
            "profile_url": "https://www.transfermarkt.it/lautaro/profil/spieler/406625",
            "full_name": "Lautaro Martínez",
            "team": "Inter",
            "birth_date": "22/08/1997",
            "source_role": "Punta centrale",
            "nationality": "Argentina",
            "market_value": "95,00 mln €",
        }

    def test_maps_fields_date_value_and_deduplicates_by_external_id(self):
        rows = canonicalize_players([self.player, {**self.player, "full_name": "Duplicate"}])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["full_name"], "Lautaro Martínez")
        self.assertEqual(rows[0]["source_role"], "Punta centrale")
        self.assertEqual(rows[0]["birth_date"], "1997-08-22")
        self.assertEqual(parse_market_value(rows[0]["market_value"]), 95_000_000)
        self.assertEqual(normalize_row(rows[0], 2).market_value_eur, 95_000_000)

    def test_generates_canonical_csv_and_import_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path, _ = write_canonical_csv([self.player], root / "players.csv")
            with csv_path.open(encoding="utf-8", newline="") as handle:
                row = next(csv.DictReader(handle))
            self.assertEqual(row["external_id"], "transfermarkt:406625")
            database = root / "canonical.test.db"
            MigrationRunner(database).upgrade()
            repository = CanonicalRepository(database)
            service = PlayerImportService(repository)
            first = service.import_file(csv_path, "transfermarkt", "2026-27")
            changed_player = {
                **self.player,
                "profile_url": "https://www.transfermarkt.it/nuovo/profil/spieler/406625",
            }
            write_canonical_csv([changed_player], csv_path)
            repeated = service.import_file(
                csv_path, "transfermarkt", "2026-27", force=True
            )
            self.assertEqual(first.inserted_rows, 1)
            self.assertEqual(repeated.skipped_rows, 1)
            self.assertEqual(repository.count_rows("players"), 1)
            with repository._connect() as connection:
                mapping = connection.execute(
                    "SELECT external_source_id, source_url FROM player_source_mappings"
                ).fetchone()
            self.assertEqual(mapping._mapping["external_source_id"], "transfermarkt:406625")
            self.assertEqual(mapping._mapping["source_url"], changed_player["profile_url"])

    def test_cli_imports_mocked_scrape_without_real_http(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = root / "canonical.test.db"
            MigrationRunner(database).upgrade()
            with (
                patch(
                    "scraper.transfermarkt.TransfermarktScraper.get_players",
                    return_value=[self.player],
                ),
                redirect_stdout(StringIO()) as output,
            ):
                status = cli_main(
                    [
                        "scrape-transfermarkt",
                        "--season",
                        "2026-27",
                        "--database",
                        str(database),
                        "--output",
                        str(root / "raw.csv"),
                    ]
                )
            self.assertEqual(status, 0)
            self.assertIn("inseriti: 1", output.getvalue())
            self.assertEqual(CanonicalRepository(database).count_rows("players"), 1)

    def test_cli_reports_http_failure_readably(self):
        with (
            patch(
                "scraper.transfermarkt.TransfermarktScraper.get_players",
                side_effect=requests.ConnectionError("offline"),
            ),
            redirect_stderr(StringIO()) as errors,
        ):
            status = cli_main(
                [
                    "scrape-transfermarkt",
                    "--season",
                    "2026-27",
                    "--database",
                    "/tmp/not-used.db",
                ]
            )
        self.assertEqual(status, 1)
        self.assertIn("Transfermarkt non raggiungibile", errors.getvalue())


if __name__ == "__main__":
    unittest.main()

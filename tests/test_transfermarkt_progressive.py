import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from services.analytics.fantaanalytics.cli import main as cli_main
from services.analytics.fantaanalytics.persistence import CanonicalRepository, MigrationRunner
from services.analytics.fantaanalytics.transfermarkt_checkpoint import (
    CheckpointError,
    load_checkpoint,
    new_checkpoint,
    save_checkpoint,
)
from services.analytics.fantaanalytics.transfermarkt_progressive import run_progressive_scrape


def player(identifier, name):
    return {
        "external_id": f"transfermarkt:{identifier}",
        "profile_url": f"https://www.transfermarkt.it/p/profil/spieler/{identifier}",
        "full_name": name,
        "team": "Inter",
        "birth_date": "01/01/2000",
        "source_role": "Portiere",
        "nationality": "Italia",
        "market_value": "1,00 mln €",
    }


class FakeScraper:
    descriptors = [
        {"external_id": "transfermarkt-club:1", "name": "Alpha", "roster_url": "/alpha"},
        {"external_id": "transfermarkt-club:2", "name": "Beta", "roster_url": "/beta"},
        {"external_id": "transfermarkt-club:3", "name": "Gamma", "roster_url": "/gamma"},
    ]
    failures = set()
    calls = []

    def __init__(self, **_kwargs):
        type(self).calls = []

    def get_club_descriptors(self):
        return list(self.descriptors)

    def get_players_for_club(self, roster_url, max_players=None):
        type(self).calls.append(roster_url)
        if roster_url in self.failures:
            raise RuntimeError("temporary failure")
        identifier = {"/alpha": "1", "/beta": "2", "/gamma": "3"}[roster_url]
        rows = [player(identifier, f"Player {identifier}")]
        return rows[:max_players] if max_players else rows, {"discovered": 1, "errors": [], "team": "Inter"}


def args(root, **overrides):
    values = dict(
        season="2026-27", database=str(root / "canonical.test.db"), output=None,
        force=False, pause=0, retries=1, max_clubs=None, max_players=None, dry_run=False,
        resume=False, checkpoint=str(root / "checkpoint.json"), club=None, start_club=None,
        retry_failed=False, continue_on_error=False,
    )
    values.update(overrides)
    return Namespace(**values)


class ProgressiveImportTest(unittest.TestCase):
    def setUp(self):
        FakeScraper.failures = set()
        FakeScraper.calls = []

    def test_checkpoint_creation_and_resume_are_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            MigrationRunner(root / "canonical.test.db").upgrade()
            with patch("services.analytics.fantaanalytics.transfermarkt_progressive.TransfermarktScraper", FakeScraper):
                first = run_progressive_scrape(args(root, max_clubs=1))
                second = run_progressive_scrape(args(root, resume=True))
            self.assertEqual(first["clubs_completed"], 1)
            self.assertEqual(second["clubs_skipped"], 1)
            self.assertEqual(CanonicalRepository(root / "canonical.test.db").count_rows("players"), 3)
            self.assertEqual(len(json.loads((root / "checkpoint.json").read_text())["completed_clubs"]), 3)

    def test_max_clubs_and_max_players_limit_work(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("services.analytics.fantaanalytics.transfermarkt_progressive.TransfermarktScraper", FakeScraper):
                result = run_progressive_scrape(args(root, dry_run=True, max_clubs=2, max_players=1))
            self.assertEqual(result["clubs_considered"], 2)
            self.assertEqual(result["profiles_requested"], 2)

    def test_club_and_start_club_selection(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("services.analytics.fantaanalytics.transfermarkt_progressive.TransfermarktScraper", FakeScraper):
                result = run_progressive_scrape(args(root, dry_run=True, club="2"))
            self.assertEqual(result["clubs_considered"], 1)
            self.assertEqual(FakeScraper.calls, ["/beta"])
            with patch("services.analytics.fantaanalytics.transfermarkt_progressive.TransfermarktScraper", FakeScraper):
                result = run_progressive_scrape(args(root, dry_run=True, start_club="Beta"))
            self.assertEqual(result["clubs_considered"], 2)
            self.assertEqual(FakeScraper.calls, ["/beta", "/gamma"])

    def test_retry_failed_retries_only_failed_club_and_records_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            MigrationRunner(root / "canonical.test.db").upgrade()
            FakeScraper.failures = {"/beta"}
            with patch("services.analytics.fantaanalytics.transfermarkt_progressive.TransfermarktScraper", FakeScraper):
                failed = run_progressive_scrape(args(root, max_clubs=2, continue_on_error=True))
            self.assertEqual(failed["clubs_failed"], 1)
            FakeScraper.failures = set()
            with patch("services.analytics.fantaanalytics.transfermarkt_progressive.TransfermarktScraper", FakeScraper):
                retried = run_progressive_scrape(args(root, retry_failed=True))
            self.assertEqual(retried["clubs_considered"], 1)
            self.assertEqual(FakeScraper.calls, ["/beta"])
            payload = json.loads((root / "checkpoint.json").read_text())
            self.assertFalse(payload["failed_clubs"])

    def test_continue_on_error_and_checkpoint_stop(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            MigrationRunner(root / "canonical.test.db").upgrade()
            FakeScraper.failures = {"/alpha"}
            with patch("services.analytics.fantaanalytics.transfermarkt_progressive.TransfermarktScraper", FakeScraper):
                result = run_progressive_scrape(args(root, continue_on_error=True))
            self.assertEqual(result["clubs_failed"], 1)
            self.assertEqual(result["clubs_completed"], 2)
            fresh = root / "fresh.json"
            with self.assertRaises(RuntimeError):
                with patch("services.analytics.fantaanalytics.transfermarkt_progressive.TransfermarktScraper", FakeScraper):
                    run_progressive_scrape(args(root, checkpoint=str(fresh), continue_on_error=False))
            FakeScraper.failures = set()

    def test_dry_run_writes_output_without_database_or_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "preview.csv"
            with patch("services.analytics.fantaanalytics.transfermarkt_progressive.TransfermarktScraper", FakeScraper):
                result = run_progressive_scrape(args(root, dry_run=True, output=str(output)))
            self.assertTrue(output.exists())
            self.assertFalse((root / "canonical.test.db").exists())
            self.assertEqual(result["checkpoint"], "nessuno (dry-run)")


class CheckpointTest(unittest.TestCase):
    def test_mismatch_corruption_and_atomic_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "state.json"
            payload = new_checkpoint("2026-27")
            save_checkpoint(path, payload)
            self.assertEqual(load_checkpoint(path, "2026-27")["version"], 1)
            with self.assertRaises(CheckpointError):
                load_checkpoint(path, "2025-26")
            path.write_text("{bad", encoding="utf-8")
            with self.assertRaises(CheckpointError):
                load_checkpoint(path, "2026-27")
            self.assertFalse(list(path.parent.glob("*.tmp")))

    def test_cli_exposes_progressive_options(self):
        with patch("services.analytics.fantaanalytics.cli.run_progressive_scrape") as runner:
            runner.return_value = {
                "clubs_discovered": 1, "clubs_considered": 1, "clubs_completed": 1,
                "clubs_skipped": 0, "clubs_failed": 0, "profiles_requested": 1,
                "valid_players": 1, "inserted_players": 1, "updated_players": 0,
                "skipped_players": 0, "errors": [], "checkpoint": "state.json",
            }
            self.assertEqual(cli_main([
                "scrape-transfermarkt", "--season", "2026-27", "--database", "/tmp/x.db",
                "--resume", "--checkpoint", "/tmp/state.json", "--club", "1",
                "--start-club", "1", "--retry-failed", "--continue-on-error",
            ]), 0)
            parsed = runner.call_args.args[0]
            self.assertTrue(parsed.resume)
            self.assertTrue(parsed.retry_failed)


if __name__ == "__main__":
    unittest.main()

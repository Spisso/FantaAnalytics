import csv
import tempfile
import unittest
from pathlib import Path

from services.analytics.fantaanalytics.import_service import PlayerImportService
from services.analytics.fantaanalytics.persistence import CanonicalRepository, MigrationRunner


class CanonicalImportTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.database = Path(self.temporary_directory.name) / "canonical.test.db"
        MigrationRunner(self.database).upgrade()
        self.repository = CanonicalRepository(self.database)
        self.service = PlayerImportService(self.repository)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _write_rows(self, rows):
        path = Path(self.temporary_directory.name) / "players.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=["external_id", "full_name", "team", "birth_date", "source_role"]
            )
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_import_persists_provenance_and_reimport_is_idempotent(self):
        source = Path("data/samples/demo_players.csv")
        first = self.service.import_file(source, "demo", "2026-27")
        repeated = self.service.import_file(source, "demo", "2026-27")
        self.assertEqual(first.status, "completed")
        self.assertEqual(first.inserted_rows, 11)
        self.assertEqual(repeated.status, "skipped_duplicate_file")
        self.assertEqual(self.repository.count_rows("players"), 11)
        self.assertEqual(self.repository.count_rows("raw_records"), 11)
        self.assertEqual(self.repository.count_rows("player_source_mappings"), 11)
        self.assertEqual(self.repository.count_rows("data_import_runs"), 1)
        listed = self.repository.list_players(role="A", season="2026-27")
        self.assertEqual(len(listed), 3)

    def test_force_import_updates_existing_external_id(self):
        source = Path("data/samples/demo_players.csv")
        self.service.import_file(source, "demo", "2026-27")
        with source.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        rows[0]["team"] = "Juventus"
        changed = Path(self.temporary_directory.name) / "changed.csv"
        with changed.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        result = self.service.import_file(changed, "demo", "2026-27", force=True)
        self.assertEqual(result.updated_rows, 1)
        self.assertEqual(result.inserted_rows, 0)
        self.assertEqual(self.repository.count_rows("players"), 11)
        self.assertEqual(
            self.repository.list_players(team="Juventus", season="2026-27")[0][
                "canonical_full_name"
            ],
            "Marco Aurora",
        )

    def test_best_effort_persists_raw_and_errors_but_imports_valid_rows(self):
        source = self._write_rows(
            [
                {
                    "external_id": "ok",
                    "full_name": "Mario Rossi",
                    "team": "Inter",
                    "birth_date": "1990-01-01",
                    "source_role": "Punta centrale",
                },
                {
                    "external_id": "bad",
                    "full_name": "Errore Ruolo",
                    "team": "Roma",
                    "birth_date": "1990-01-01",
                    "source_role": "Ruolo sconosciuto",
                },
            ]
        )
        result = self.service.import_file(source, "manual", "2026-27")
        self.assertEqual((result.inserted_rows, result.error_rows), (1, 1))
        self.assertEqual(result.status, "completed_with_errors")
        self.assertEqual(self.repository.count_rows("raw_records"), 2)
        self.assertEqual(self.repository.count_rows("data_import_errors"), 1)

    def test_strict_mode_persists_diagnostics_without_persisting_players(self):
        source = self._write_rows(
            [
                {
                    "external_id": "ok",
                    "full_name": "Mario Rossi",
                    "team": "Inter",
                    "birth_date": "1990-01-01",
                    "source_role": "Punta centrale",
                },
                {
                    "external_id": "bad",
                    "full_name": "Errore Ruolo",
                    "team": "Roma",
                    "birth_date": "1990-01-01",
                    "source_role": "Ruolo sconosciuto",
                },
            ]
        )
        result = self.service.import_file(source, "manual", "2026-27", strict=True)
        self.assertEqual(result.status, "failed")
        self.assertEqual(self.repository.count_rows("players"), 0)
        self.assertEqual(self.repository.count_rows("raw_records"), 2)
        self.assertEqual(self.repository.count_rows("data_import_errors"), 1)

    def test_name_birth_date_matches_across_known_team_aliases(self):
        source = self._write_rows(
            [
                {
                    "external_id": "",
                    "full_name": "D'Angelo Test",
                    "team": "Inter",
                    "birth_date": "1990-01-01",
                    "source_role": "Punta centrale",
                },
                {
                    "external_id": "",
                    "full_name": "D’Angelo   Test",
                    "team": "FC Internazionale",
                    "birth_date": "1990-01-01",
                    "source_role": "Punta centrale",
                },
            ]
        )
        result = self.service.import_file(source, "manual", "2026-27")
        self.assertEqual(result.inserted_rows, 1)
        self.assertEqual(result.skipped_rows, 1)
        self.assertEqual(self.repository.count_rows("players"), 1)

    def test_same_name_different_dates_in_different_teams_are_not_merged(self):
        source = self._write_rows(
            [
                {
                    "external_id": "one",
                    "full_name": "Andrea Bianchi",
                    "team": "Roma",
                    "birth_date": "1990-01-01",
                    "source_role": "Punta centrale",
                },
                {
                    "external_id": "two",
                    "full_name": "Andrea Bianchi",
                    "team": "Milan",
                    "birth_date": "1992-01-01",
                    "source_role": "Punta centrale",
                },
            ]
        )
        result = self.service.import_file(source, "manual", "2026-27")
        self.assertEqual(result.inserted_rows, 2)
        self.assertEqual(self.repository.count_rows("players"), 2)

    def test_infrastructure_failure_rolls_back_transaction(self):
        with self.assertRaises(RuntimeError):
            with self.repository.transaction() as connection:
                self.repository.get_or_create_source(connection, "rollback")
                raise RuntimeError("database failure")
        self.assertEqual(self.repository.count_rows("data_sources"), 0)

    def test_migration_can_be_downgraded_and_reapplied(self):
        runner = MigrationRunner(self.database)
        self.assertEqual(runner.downgrade(), "001")
        self.assertEqual(runner.upgrade(), ["001"])
        self.assertEqual(self.repository.count_rows("players"), 0)

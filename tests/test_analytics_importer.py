import csv
import tempfile
import unittest
from pathlib import Path

from services.analytics.fantaanalytics.importer import import_csv
from services.analytics.fantaanalytics.normalization import (
    infer_fantasy_role,
    normalize_name,
    parse_market_value,
)


class NormalizationTest(unittest.TestCase):
    def test_normalizes_accents_and_apostrophes(self):
        self.assertEqual(normalize_name("Lautaro Martínez"), "lautaro martinez")
        self.assertEqual(normalize_name("D'Ángelo"), "d angelo")

    def test_parses_italian_market_values(self):
        self.assertEqual(parse_market_value("20,00 mln €"), 20_000_000)
        self.assertEqual(parse_market_value("400 mila €"), 400_000)
        self.assertIsNone(parse_market_value("Free transfer"))

    def test_maps_source_roles_and_prefers_official_role(self):
        self.assertEqual(infer_fantasy_role("Punta centrale"), "A")
        self.assertEqual(infer_fantasy_role("Punta centrale", "C"), "C")
        self.assertEqual(infer_fantasy_role("Terzino sinistro"), "D")
        self.assertEqual(infer_fantasy_role("Mediano"), "C")
        self.assertEqual(infer_fantasy_role("Centrocampista"), "C")
        self.assertEqual(infer_fantasy_role("Esterno di destra"), "A")


class CsvImporterTest(unittest.TestCase):
    def test_imports_valid_records_and_reports_invalid_rows(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "players.csv"
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["full_name", "team", "source_role"])
                writer.writeheader()
                writer.writerow(
                    {"full_name": "Mario Rossi", "team": "Roma", "source_role": "Punta centrale"}
                )
                writer.writerow({"full_name": "", "team": "Roma", "source_role": "Punta centrale"})
            players, issues = import_csv(path)
        self.assertEqual(len(players), 1)
        self.assertEqual(players[0].fantasy_role, "A")
        self.assertEqual(issues[0].row_number, 3)

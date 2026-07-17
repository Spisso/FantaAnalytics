import json
import tempfile
import unittest
from pathlib import Path

from services.analytics.fantaanalytics.api import create_app
from services.analytics.fantaanalytics.import_service import PlayerImportService
from services.analytics.fantaanalytics.persistence import CanonicalRepository, MigrationRunner


class ReadApiTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        database = Path(self.temporary_directory.name) / "api.test.db"
        MigrationRunner(database).upgrade()
        PlayerImportService(CanonicalRepository(database)).import_file(
            Path("data/samples/demo_players.csv"), "demo", "2026-27"
        )
        self.application = create_app(database)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def _get(self, path, query=""):
        response = {}

        def start_response(status, headers):
            response["status"] = status
            response["headers"] = headers

        body = b"".join(
            self.application(
                {"REQUEST_METHOD": "GET", "PATH_INFO": path, "QUERY_STRING": query}, start_response
            )
        )
        return response["status"], json.loads(body)

    def test_health_and_players_endpoints(self):
        status, health = self._get("/health")
        self.assertEqual(status, "200 OK")
        self.assertTrue(health["database"])
        status, players = self._get("/api/v1/players", "role=A&season=2026-27")
        self.assertEqual(status, "200 OK")
        self.assertEqual(players["count"], 3)

    def test_player_detail_and_import_runs(self):
        status, player = self._get("/api/v1/players/1")
        self.assertEqual(status, "200 OK")
        self.assertEqual(player["data"]["canonical_full_name"], "Marco Aurora")
        status, runs = self._get("/api/v1/import-runs")
        self.assertEqual(status, "200 OK")
        self.assertEqual(runs["count"], 1)

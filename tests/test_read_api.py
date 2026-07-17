import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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
        self.assertEqual(health, {"status": "ok", "service": "analytics"})
        status, readiness = self._get("/ready")
        self.assertEqual(status, "200 OK")
        self.assertEqual(readiness, {"status": "ready", "database": True})
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

    def test_health_stays_live_when_database_is_not_ready(self):
        unavailable = create_app(Path(self.temporary_directory.name) / "missing.test.db")
        self.application = unavailable
        status, health = self._get("/health")
        self.assertEqual(status, "200 OK")
        self.assertNotIn("database", health)
        with self.assertLogs("services.analytics.fantaanalytics.api", level="WARNING") as logs:
            status, readiness = self._get("/ready")
        self.assertEqual(status, "503 Service Unavailable")
        self.assertEqual(readiness, {"status": "unavailable", "database": False})
        self.assertNotIn("known-secret", json.dumps(readiness))
        self.assertNotIn("known-secret", " ".join(logs.output))

    def test_readiness_does_not_expose_database_password(self):
        self.application = create_app(
            "postgresql+psycopg://user:known-secret@postgres.invalid:5432/database"
        )
        with patch.object(self.application.repository, "is_ready", return_value=False):
            with self.assertLogs("services.analytics.fantaanalytics.api", level="WARNING") as logs:
                status, readiness = self._get("/ready")
        self.assertEqual(status, "503 Service Unavailable")
        output = json.dumps(readiness) + " ".join(logs.output)
        self.assertNotIn("known-secret", output)

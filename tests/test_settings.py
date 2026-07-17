import os
import unittest
from unittest.mock import patch

from services.analytics.fantaanalytics.settings import DEFAULT_DATABASE_URL, Settings


class SettingsTest(unittest.TestCase):
    def test_database_url_defaults_to_local_sqlite(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(Settings.from_env().database_url, DEFAULT_DATABASE_URL)

    def test_database_url_from_environment_has_priority(self):
        database_url = "postgresql+psycopg://user:known-secret@postgres:5432/database"
        with patch.dict(os.environ, {"DATABASE_URL": database_url}, clear=True):
            self.assertEqual(Settings.from_env().database_url, database_url)

import os
import sqlite3
import tempfile
import unittest

from services.database_service import DatabaseService


class DatabaseServiceTest(unittest.TestCase):
    def test_save_creates_database_and_stores_raw_player_fields(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = os.path.join(tmp_dir, "players.db")
            service = DatabaseService(db_path=db_path)

            data = [
                {
                    "name": "Lautaro Martínez",
                    "team": "Inter",
                    "birth_date": "22/08/1997",
                    "birth_place": "Bahía Blanca",
                    "height": "1,74 m",
                    "position": "Punta centrale",
                    "nationality": "Argentina",
                    "foot": "destro",
                }
            ]

            service.save(data, table_name="players")

            self.assertTrue(os.path.exists(db_path))

            with sqlite3.connect(db_path) as conn:
                rows = conn.execute(
                    "SELECT name, team, birth_date, birth_place, height, position, nationality, foot FROM players"
                ).fetchall()

            self.assertEqual(rows[0][0], "Lautaro Martínez")
            self.assertEqual(rows[0][1], "Inter")
            self.assertEqual(rows[0][2], "22/08/1997")
            self.assertEqual(rows[0][3], "Bahía Blanca")
            self.assertEqual(rows[0][4], "1,74 m")
            self.assertEqual(rows[0][5], "Punta centrale")
            self.assertEqual(rows[0][6], "Argentina")
            self.assertEqual(rows[0][7], "destro")

    def test_save_rejects_unsafe_table_identifier(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            service = DatabaseService(db_path=os.path.join(tmp_dir, "players.db"))
            with self.assertRaises(ValueError):
                service.save([{"name": "Mario Rossi"}], table_name="players; DROP TABLE players")


if __name__ == "__main__":
    unittest.main()

import os
import sqlite3
from typing import List, Dict, Optional


class DatabaseService:

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join("database", "transfermarkt.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def save(self, data: List[Dict], table_name: str = "players"):
        if not data:
            return

        columns = list(data[0].keys())
        columns_sql = ", ".join(f'"{col}" TEXT' for col in columns)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql})')
            placeholders = ", ".join(["?"] * len(columns))
            quoted_columns = ", ".join(f'"{col}"' for col in columns)
            insert_sql = f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})'

            for item in data:
                values = [item.get(col) for col in columns]
                conn.execute(insert_sql, values)

            conn.commit()

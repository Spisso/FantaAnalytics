import os
import re
import sqlite3
from typing import Dict, List, Optional

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class DatabaseService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or os.path.join("database", "transfermarkt.db")
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def save(self, data: List[Dict], table_name: str = "players"):
        if not data:
            return

        if not _IDENTIFIER_PATTERN.fullmatch(table_name):
            raise ValueError("Nome tabella non valido")

        columns = list(data[0].keys())
        if not columns or any(not _IDENTIFIER_PATTERN.fullmatch(column) for column in columns):
            raise ValueError("Nomi colonna non validi")
        columns_sql = ", ".join(f'"{col}" TEXT' for col in columns)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(f'CREATE TABLE IF NOT EXISTS "{table_name}" ({columns_sql})')
            placeholders = ", ".join(["?"] * len(columns))
            quoted_columns = ", ".join(f'"{col}"' for col in columns)
            insert_sql = f'INSERT INTO "{table_name}" ({quoted_columns}) VALUES ({placeholders})'

            conn.executemany(insert_sql, ([item.get(col) for col in columns] for item in data))

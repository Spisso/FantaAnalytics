"""Repository abstraction for canonical import data on SQLite and PostgreSQL."""

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from sqlalchemy import JSON, bindparam, create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from .matching import AMBIGUOUS, CREATED, INVALID, MATCHED, MatchResult
from .normalization import normalize_name
from .team_resolution import resolve_team_name


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class MigrationRunner:
    """Applies numbered SQL migrations; schema creation is never implicit in imports."""

    def __init__(self, database_path: Path, migrations_path: Optional[Path] = None):
        self.database_path = Path(database_path)
        self.migrations_path = migrations_path or Path(__file__).parents[1] / "migrations"

    def _connect(self) -> sqlite3.Connection:
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database_path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def upgrade(self) -> List[str]:
        with self._connect() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL)"
            )
            applied = {
                row[0] for row in connection.execute("SELECT version FROM schema_migrations")
            }
            migrations = sorted(self.migrations_path.glob("*.up.sql"))
            completed = []
            for path in migrations:
                version = path.name.split("_", 1)[0]
                if version in applied:
                    continue
                connection.executescript(path.read_text(encoding="utf-8"))
                connection.execute(
                    "INSERT INTO schema_migrations(version, applied_at) VALUES (?, ?)",
                    (version, utc_now()),
                )
                completed.append(version)
            return completed

    def downgrade(self) -> Optional[str]:
        with self._connect() as connection:
            exists = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
            ).fetchone()
            if not exists:
                return None
            row = connection.execute(
                "SELECT version FROM schema_migrations ORDER BY version DESC LIMIT 1"
            ).fetchone()
            if not row:
                return None
            version = row[0]
            candidates = list(self.migrations_path.glob(f"{version}_*.down.sql"))
            if not candidates:
                raise RuntimeError(f"Downgrade non trovato per migrazione {version}")
            connection.executescript(candidates[0].read_text(encoding="utf-8"))
            connection.execute("DELETE FROM schema_migrations WHERE version = ?", (version,))
            return version


class _ConnectionAdapter:
    """Small compatibility layer while repository queries migrate to SQLAlchemy binds."""

    def __init__(self, connection: Connection):
        self.connection = connection

    def execute(self, statement: str, parameters=None):
        if parameters is None:
            return self.connection.execute(text(statement))
        if isinstance(parameters, (tuple, list)):
            values = list(parameters)
            parts = statement.split("?")
            if len(parts) - 1 != len(values):
                raise ValueError("Numero di parametri SQL non coerente")
            rewritten = parts[0]
            binds = {}
            for index, value in enumerate(values):
                key = f"value_{index}"
                rewritten += f":{key}{parts[index + 1]}"
                binds[key] = value
            statement, parameters = rewritten, binds
        clause = text(statement)
        if isinstance(parameters, dict):
            json_keys = [
                key for key, value in parameters.items() if isinstance(value, (dict, list))
            ]
            if json_keys:
                clause = clause.bindparams(*(bindparam(key, type_=JSON) for key in json_keys))
        return self.connection.execute(clause, parameters)


class CanonicalRepository:
    """One persistence boundary shared by SQLite locally and PostgreSQL in Docker."""

    def __init__(self, database):
        value = str(database)
        if "://" not in value:
            path = Path(value)
            path.parent.mkdir(parents=True, exist_ok=True)
            value = f"sqlite:///{path}"
        self.database_url = value
        self.engine: Engine = create_engine(value, future=True)

    @contextmanager
    def _connect(self) -> Iterator[_ConnectionAdapter]:
        with self.engine.connect() as connection:
            if connection.dialect.name == "sqlite":
                connection.exec_driver_sql("PRAGMA foreign_keys = ON")
            yield _ConnectionAdapter(connection)

    @contextmanager
    def transaction(self) -> Iterator[_ConnectionAdapter]:
        with self.engine.begin() as connection:
            if connection.dialect.name == "sqlite":
                connection.exec_driver_sql("PRAGMA foreign_keys = ON")
            yield _ConnectionAdapter(connection)

    @staticmethod
    def _insert_id(connection: _ConnectionAdapter, statement: str, parameters: dict) -> int:
        result = connection.execute(f"{statement} RETURNING id", parameters)
        return int(result.scalar_one())

    def _dump(self, value: Any):
        if self.engine.dialect.name == "postgresql":
            return value
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)

    def get_or_create_source(self, connection: sqlite3.Connection, code: str) -> int:
        row = connection.execute("SELECT id FROM data_sources WHERE code = ?", (code,)).fetchone()
        if row:
            return int(row._mapping["id"])
        now = utc_now()
        return self._insert_id(
            connection,
            """INSERT INTO data_sources(code, name, source_type, base_url, active, created_at, updated_at)
               VALUES (:code, :name, 'file', NULL, true, :created_at, :updated_at)""",
            {"code": code, "name": code.replace("_", " ").title(), "created_at": now, "updated_at": now},
        )

    def find_duplicate_run(
        self, connection: sqlite3.Connection, source_id: int, checksum: str, season: str
    ) -> Optional[int]:
        row = connection.execute(
            """SELECT id FROM data_import_runs
               WHERE data_source_id = ? AND input_checksum = ? AND season = ?
               AND status IN ('completed', 'completed_with_errors')
               ORDER BY id DESC LIMIT 1""",
            (source_id, checksum, season),
        ).fetchone()
        return int(row._mapping["id"]) if row else None

    def create_import_run(
        self,
        connection: sqlite3.Connection,
        source_id: int,
        schema_version: str,
        season: str,
        filename: str,
        checksum: str,
        parser_version: str,
    ) -> int:
        now = utc_now()
        return self._insert_id(
            connection,
            """INSERT INTO data_import_runs(
                data_source_id, schema_version, season, status, started_at, input_filename,
                input_checksum, parser_version, created_at, updated_at
            ) VALUES (:source_id, :schema_version, :season, 'running', :started_at, :filename,
                      :checksum, :parser_version, :created_at, :updated_at)""",
            {"source_id": source_id, "schema_version": schema_version, "season": season,
             "started_at": now, "filename": filename, "checksum": checksum,
             "parser_version": parser_version, "created_at": now, "updated_at": now},
        )

    def finalize_import_run(self, connection: sqlite3.Connection, run_id: int, result: Any) -> None:
        now = utc_now()
        connection.execute(
            """UPDATE data_import_runs SET status=?, completed_at=?, total_rows=?, valid_rows=?,
               inserted_rows=?, updated_rows=?, skipped_rows=?, error_rows=?, metadata=?, updated_at=?
               WHERE id=?""",
            (
                result.status,
                now,
                result.total_rows,
                result.valid_rows,
                result.inserted_rows,
                result.updated_rows,
                result.skipped_rows,
                result.error_rows,
                self._dump({"strict": result.strict, "force": result.force}),
                now,
                run_id,
            ),
        )

    def save_raw_record(
        self,
        connection: sqlite3.Connection,
        run_id: int,
        row_number: int,
        external_id: Optional[str],
        payload: Dict[str, Any],
        checksum: str,
    ) -> None:
        connection.execute(
            """INSERT INTO raw_records(import_run_id, row_number, source_external_id, payload, payload_checksum, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (run_id, row_number, external_id, self._dump(payload), checksum, utc_now()),
        )

    def save_error(
        self,
        connection: sqlite3.Connection,
        run_id: int,
        row_number: int,
        code: str,
        message: str,
        raw_record: Dict[str, Any],
        field_name: str = "record",
        raw_value: Optional[str] = None,
    ) -> None:
        connection.execute(
            """INSERT INTO data_import_errors(import_run_id,row_number,error_code,field_name,raw_value,message,raw_record,created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                row_number,
                code,
                field_name,
                raw_value,
                message,
                self._dump(raw_record),
                utc_now(),
            ),
        )

    def _resolve_team(
        self,
        connection: sqlite3.Connection,
        team_name: str,
        season: str,
        competition: str = "Serie A",
    ) -> int:
        canonical_name = resolve_team_name(team_name)
        normalized = normalize_name(canonical_name)
        row = connection.execute(
            """SELECT id FROM football_teams WHERE normalized_name=? AND competition=? AND season=?""",
            (normalized, competition, season),
        ).fetchone()
        if row:
            return int(row._mapping["id"])
        now = utc_now()
        return self._insert_id(
            connection,
            """INSERT INTO football_teams(canonical_name, normalized_name, short_name, competition, season, active, created_at, updated_at)
               VALUES (:canonical_name, :normalized_name, :short_name, :competition, :season, true, :created_at, :updated_at)""",
            {"canonical_name": canonical_name, "normalized_name": normalized,
             "short_name": canonical_name, "competition": competition, "season": season,
             "created_at": now, "updated_at": now},
        )

    def match_player(
        self, connection: sqlite3.Connection, source_id: int, payload: Dict[str, Any], season: str
    ) -> MatchResult:
        external_id = payload.get("external_id")
        if external_id:
            row = connection.execute(
                "SELECT player_id FROM player_source_mappings WHERE data_source_id=? AND external_source_id=?",
                (source_id, external_id),
            ).fetchone()
            if row:
                return MatchResult(MATCHED, int(row._mapping["player_id"]), "source_external_id")
        normalized_name = normalize_name(payload["full_name"])
        birth_date = payload.get("birth_date")
        if birth_date:
            rows = connection.execute(
                "SELECT id FROM players WHERE normalized_name=? AND birth_date=?",
                (normalized_name, birth_date),
            ).fetchall()
            if len(rows) == 1:
                return MatchResult(MATCHED, int(rows[0]._mapping["id"]), "name_birth_date")
            if len(rows) > 1:
                return MatchResult(AMBIGUOUS, reason="name_birth_date")
        team_id = self._resolve_team(connection, payload["team"], season)
        rows = connection.execute(
            "SELECT id FROM players WHERE normalized_name=? AND current_team_id=?",
            (normalized_name, team_id),
        ).fetchall()
        if len(rows) == 1:
            existing_birth_date = connection.execute(
                "SELECT birth_date FROM players WHERE id=?", (rows[0]._mapping["id"],)
            ).fetchone()._mapping["birth_date"]
            if birth_date and existing_birth_date and existing_birth_date != birth_date:
                return MatchResult(AMBIGUOUS, reason="name_team_birth_date_conflict")
            return MatchResult(MATCHED, int(rows[0]._mapping["id"]), "name_team")
        if len(rows) > 1:
            return MatchResult(AMBIGUOUS, reason="name_team")
        return MatchResult(CREATED, reason="no_candidate")

    def upsert_player(
        self,
        connection: sqlite3.Connection,
        source_id: int,
        payload: Dict[str, Any],
        season: str,
        match: MatchResult,
    ) -> str:
        if match.status == AMBIGUOUS:
            return AMBIGUOUS
        if match.status == INVALID:
            return INVALID
        now = utc_now()
        team_id = self._resolve_team(connection, payload["team"], season)
        nationalities = payload.get("nationalities", [])
        values = {
            "canonical_full_name": payload["full_name"],
            "first_name": payload.get("first_name"),
            "last_name": payload.get("last_name"),
            "normalized_name": normalize_name(payload["full_name"]),
            "birth_date": payload.get("birth_date"),
            "nationality": nationalities[0] if nationalities else None,
            "secondary_nationality": nationalities[1] if len(nationalities) > 1 else None,
            "preferred_foot": payload.get("preferred_foot"),
            "height_cm": payload.get("height_cm"),
            "source_role": payload.get("source_role"),
            "inferred_fantasy_role": payload.get("inferred_fantasy_role"),
            "official_fantasy_role": payload.get("official_fantasy_role"),
            "effective_fantasy_role": payload.get("official_fantasy_role")
            or payload["inferred_fantasy_role"],
            "current_team_id": team_id,
        }
        if match.status == CREATED:
            player_id = self._insert_id(
                connection,
                """INSERT INTO players(
                    canonical_full_name,first_name,last_name,normalized_name,birth_date,nationality,secondary_nationality,
                    preferred_foot,height_cm,source_role,inferred_fantasy_role,official_fantasy_role,effective_fantasy_role,
                    current_team_id,active,notes,created_at,updated_at
                ) VALUES (:canonical_full_name,:first_name,:last_name,:normalized_name,:birth_date,:nationality,:secondary_nationality,
                    :preferred_foot,:height_cm,:source_role,:inferred_fantasy_role,:official_fantasy_role,:effective_fantasy_role,
                    :current_team_id,true,NULL,:created_at,:updated_at)""",
                {**values, "created_at": now, "updated_at": now},
            )
            outcome = "inserted"
        else:
            player_id = int(match.player_id)
            existing = connection.execute(
                "SELECT * FROM players WHERE id=?", (player_id,)
            ).fetchone()
            comparison_fields = list(values)
            unchanged = all(existing._mapping[field] == values[field] for field in comparison_fields)
            if unchanged:
                outcome = "skipped"
            else:
                assignments = ", ".join(f"{field}=:{field}" for field in values)
                connection.execute(
                    f"UPDATE players SET {assignments}, updated_at=:updated_at WHERE id=:id",
                    {**values, "updated_at": now, "id": player_id},
                )
                outcome = "updated"
        external_id = payload.get("external_id")
        if external_id:
            mapping = connection.execute(
                "SELECT id FROM player_source_mappings WHERE data_source_id=? AND external_source_id=?",
                (source_id, external_id),
            ).fetchone()
            if not mapping:
                connection.execute(
                    """INSERT INTO player_source_mappings(
                        player_id,data_source_id,external_source_id,source_url,source_display_name,
                        matching_confidence,manually_confirmed,created_at,updated_at
                    ) VALUES (?, ?, ?, ?, ?, 1.0, false, ?, ?)""",
                    (
                        player_id,
                        source_id,
                        external_id,
                        payload.get("source_url"),
                        payload["full_name"],
                        now,
                        now,
                    ),
                )
        return outcome

    def list_players(
        self,
        role: Optional[str] = None,
        team: Optional[str] = None,
        season: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        clauses = ["1=1"]
        parameters: List[Any] = []
        if role:
            clauses.append("p.effective_fantasy_role = ?")
            parameters.append(role)
        if team:
            clauses.append("t.normalized_name = ?")
            parameters.append(normalize_name(resolve_team_name(team)))
        if season:
            clauses.append("t.season = ?")
            parameters.append(season)
        parameters.append(max(1, min(limit, 200)))
        query = f"""SELECT p.id, p.canonical_full_name, p.birth_date, p.nationality, p.effective_fantasy_role,
                            t.canonical_name AS team, t.season
                     FROM players p JOIN football_teams t ON t.id=p.current_team_id
                     WHERE {" AND ".join(clauses)} ORDER BY p.canonical_full_name LIMIT ?"""
        with self._connect() as connection:
            return [dict(row._mapping) for row in connection.execute(query, parameters).fetchall()]

    def get_player(self, player_id: int) -> Optional[Dict[str, Any]]:
        query = """SELECT p.id, p.canonical_full_name, p.first_name, p.last_name, p.normalized_name,
                          p.birth_date, p.nationality, p.secondary_nationality, p.preferred_foot,
                          p.height_cm, p.source_role, p.inferred_fantasy_role, p.official_fantasy_role,
                          p.effective_fantasy_role, p.active, p.notes, p.created_at, p.updated_at,
                          t.canonical_name AS team, t.season
                   FROM players p JOIN football_teams t ON t.id=p.current_team_id WHERE p.id=?"""
        with self._connect() as connection:
            row = connection.execute(query, (player_id,)).fetchone()
            return dict(row._mapping) if row else None

    def list_import_runs(self, limit: int = 50) -> List[Dict[str, Any]]:
        query = """SELECT r.id, s.code AS source, r.season, r.status, r.input_filename,
                          r.total_rows, r.valid_rows, r.inserted_rows, r.updated_rows, r.skipped_rows,
                          r.error_rows, r.started_at, r.completed_at
                   FROM data_import_runs r JOIN data_sources s ON s.id=r.data_source_id
                   ORDER BY r.id DESC LIMIT ?"""
        with self._connect() as connection:
            return [
                dict(row._mapping)
                for row in connection.execute(query, (max(1, min(limit, 200)),)).fetchall()
            ]

    def is_available(self) -> bool:
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1").fetchone()
            return True
        except SQLAlchemyError:
            return False

    def is_ready(self) -> bool:
        try:
            with self._connect() as connection:
                connection.execute("SELECT 1").fetchone()
                if self.engine.dialect.name == "sqlite":
                    connection.execute("SELECT version FROM schema_migrations LIMIT 1").fetchone()
                else:
                    connection.execute("SELECT version_num FROM alembic_version LIMIT 1").fetchone()
                connection.execute("SELECT 1 FROM players LIMIT 1").fetchone()
            return True
        except SQLAlchemyError:
            return False

    def count_rows(self, table: str) -> int:
        if table not in {
            "players",
            "football_teams",
            "data_sources",
            "player_source_mappings",
            "data_import_runs",
            "data_import_errors",
            "raw_records",
        }:
            raise ValueError("Tabella non interrogabile")
        with self._connect() as connection:
            return int(connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])

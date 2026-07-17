"""Cohesive best-effort/strict import orchestration over the canonical repository."""

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .checksums import file_checksum, record_checksum
from .contracts import SCHEMA_VERSION, player_payload, validate_player_v1
from .importer import normalize_row, read_csv_rows
from .matching import AMBIGUOUS
from .persistence import CanonicalRepository

PARSER_VERSION = "csv-import-v1"


@dataclass
class ImportErrorDetail:
    row_number: int
    code: str
    message: str


@dataclass
class ImportResult:
    import_run_id: Optional[int]
    status: str
    total_rows: int = 0
    valid_rows: int = 0
    inserted_rows: int = 0
    updated_rows: int = 0
    skipped_rows: int = 0
    error_rows: int = 0
    errors: List[ImportErrorDetail] = field(default_factory=list)
    strict: bool = False
    force: bool = False

    def as_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["errors"] = [asdict(error) for error in self.errors]
        return result


@dataclass
class _PreparedRecord:
    row_number: int
    raw: Dict[str, str]
    payload: Optional[Dict[str, Any]] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class PlayerImportService:
    """Imports a whole file atomically for infrastructure failures and best-effort for row errors."""

    def __init__(self, repository: CanonicalRepository):
        self.repository = repository

    def _prepare(self, file_path: Path, source_code: str, season: str) -> List[_PreparedRecord]:
        prepared: List[_PreparedRecord] = []
        seen_external_ids = set()
        for row_number, raw in read_csv_rows(file_path):
            try:
                player = normalize_row(raw, row_number)
                payload = player_payload(
                    player,
                    source_code,
                    season,
                    raw.get("source_url", ""),
                    raw.get("market_value", ""),
                )
                errors = validate_player_v1(payload)
                if errors:
                    raise ValueError("; ".join(errors))
                external_id = payload.get("external_id")
                if external_id and external_id in seen_external_ids:
                    raise ValueError(f"Identificativo duplicato nel file: {external_id}")
                if external_id:
                    seen_external_ids.add(external_id)
                prepared.append(_PreparedRecord(row_number, raw, payload=payload))
            except ValueError as exc:
                prepared.append(
                    _PreparedRecord(
                        row_number, raw, error_code="validation_error", error_message=str(exc)
                    )
                )
        return prepared

    def import_file(
        self,
        file_path: Path,
        source_code: str,
        season: str,
        strict: bool = False,
        force: bool = False,
    ) -> ImportResult:
        file_path = Path(file_path)
        checksum = file_checksum(file_path)
        prepared = self._prepare(file_path, source_code, season)
        result = ImportResult(
            import_run_id=None,
            status="running",
            total_rows=len(prepared),
            strict=strict,
            force=force,
        )
        with self.repository.transaction() as connection:
            source_id = self.repository.get_or_create_source(connection, source_code)
            existing_run = self.repository.find_duplicate_run(
                connection, source_id, checksum, season
            )
            if existing_run is not None and not force:
                result.import_run_id = existing_run
                result.status = "skipped_duplicate_file"
                result.skipped_rows = result.total_rows
                return result
            run_id = self.repository.create_import_run(
                connection,
                source_id,
                SCHEMA_VERSION,
                season,
                file_path.name,
                checksum,
                PARSER_VERSION,
            )
            result.import_run_id = run_id
            for item in prepared:
                external_id = (
                    item.payload.get("external_id") if item.payload else item.raw.get("external_id")
                )
                self.repository.save_raw_record(
                    connection,
                    run_id,
                    item.row_number,
                    external_id,
                    item.raw,
                    record_checksum(item.raw),
                )
                if item.error_message:
                    result.error_rows += 1
                    detail = ImportErrorDetail(
                        item.row_number, item.error_code or "validation_error", item.error_message
                    )
                    result.errors.append(detail)
                    self.repository.save_error(
                        connection, run_id, item.row_number, detail.code, detail.message, item.raw
                    )
                else:
                    result.valid_rows += 1
            if strict and result.error_rows:
                result.status = "failed"
                result.skipped_rows = result.valid_rows
                self.repository.finalize_import_run(connection, run_id, result)
                return result
            for item in prepared:
                if not item.payload:
                    continue
                match = self.repository.match_player(connection, source_id, item.payload, season)
                if match.status == AMBIGUOUS:
                    result.error_rows += 1
                    detail = ImportErrorDetail(
                        item.row_number,
                        "ambiguous_match",
                        "Candidato ambiguo: revisione manuale richiesta",
                    )
                    result.errors.append(detail)
                    self.repository.save_error(
                        connection, run_id, item.row_number, detail.code, detail.message, item.raw
                    )
                    continue
                outcome = self.repository.upsert_player(
                    connection, source_id, item.payload, season, match
                )
                if outcome == "inserted":
                    result.inserted_rows += 1
                elif outcome == "updated":
                    result.updated_rows += 1
                else:
                    result.skipped_rows += 1
            result.status = "completed_with_errors" if result.error_rows else "completed"
            self.repository.finalize_import_run(connection, run_id, result)
        return result

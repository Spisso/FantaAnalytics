"""CSV import with deterministic validation and a non-destructive preview."""

import csv
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple, Union

from .models import ImportIssue, NormalizedPlayer
from .normalization import (
    clean_text,
    infer_fantasy_role,
    normalize_name,
    parse_bool,
    parse_date,
    parse_decimal,
    parse_market_value,
    parse_probability,
)

REQUIRED_COLUMNS = {"full_name", "team", "source_role"}


def read_csv_rows(path: Union[str, Path]) -> Iterator[Tuple[int, Dict[str, str]]]:
    """Read source rows without normalization so callers can retain invalid raw records."""
    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        headers = set(reader.fieldnames or [])
        missing = REQUIRED_COLUMNS - headers
        if missing:
            raise ValueError(f"Colonne obbligatorie mancanti: {', '.join(sorted(missing))}")
        for row_number, row in enumerate(reader, start=2):
            yield row_number, dict(row)


def _optional_int(value: object) -> Optional[int]:
    parsed = parse_decimal(value)
    return int(parsed) if parsed is not None else None


def _optional_float(value: object) -> Optional[float]:
    return parse_decimal(value)


def normalize_row(row: dict[str, str], row_number: int) -> NormalizedPlayer:
    full_name = clean_text(row.get("full_name"))
    team = clean_text(row.get("team"))
    if not full_name:
        raise ValueError("Nome giocatore obbligatorio")
    if not team:
        raise ValueError("Squadra obbligatoria")
    source_role = clean_text(row.get("source_role"))
    role = infer_fantasy_role(source_role, row.get("official_fantasy_role"))
    return NormalizedPlayer(
        external_id=clean_text(row.get("external_id"))
        or f"manual:{normalize_name(full_name)}:{team.lower()}",
        full_name=full_name,
        normalized_name=normalize_name(full_name),
        team=team,
        birth_date=parse_date(row.get("birth_date")),
        nationality=clean_text(row.get("nationality")),
        source_role=source_role,
        fantasy_role=role,
        appearances=_optional_int(row.get("appearances")),
        minutes=_optional_int(row.get("minutes")),
        goals=_optional_float(row.get("goals")),
        assists=_optional_float(row.get("assists")),
        fantasy_average=_optional_float(row.get("fantasy_average")),
        starter_probability=parse_probability(row.get("starter_probability")),
        rotation_risk=parse_probability(row.get("rotation_risk")),
        injury_risk=parse_probability(row.get("injury_risk")),
        penalty_taker=parse_bool(row.get("penalty_taker")),
        set_piece_taker=parse_bool(row.get("set_piece_taker")),
        team_strength=parse_probability(row.get("team_strength")),
        official_quotation=_optional_float(row.get("official_quotation")),
        market_value_eur=parse_market_value(row.get("market_value")),
    )


def import_csv(path: Union[str, Path]) -> Tuple[List[NormalizedPlayer], List[ImportIssue]]:
    """Return accepted records and all recoverable row-level validation issues."""
    records: List[NormalizedPlayer] = []
    issues: List[ImportIssue] = []
    seen_ids: set[str] = set()
    for row_number, row in read_csv_rows(path):
        try:
            record = normalize_row(row, row_number)
            if record.external_id in seen_ids:
                raise ValueError(f"Identificativo duplicato: {record.external_id}")
            seen_ids.add(record.external_id)
            records.append(record)
        except ValueError as exc:
            issues.append(ImportIssue(row_number=row_number, field="record", message=str(exc)))
    return records, issues


def export_csv(records: Iterable[NormalizedPlayer], path: Union[str, Path]) -> None:
    """Write a UTF-8, deterministic canonical export suitable for downstream import."""
    fields = list(NormalizedPlayer.__dataclass_fields__)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in records:
            values = record.__dict__.copy()
            values["birth_date"] = record.birth_date.isoformat() if record.birth_date else ""
            writer.writerow(values)

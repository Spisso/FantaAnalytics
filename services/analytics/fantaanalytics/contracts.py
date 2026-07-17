"""Small, dependency-free validator for the versioned local JSON contracts."""

import json
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

SCHEMA_VERSION = "player.v1"
_SCHEMA_PATH = Path(__file__).parents[3] / "contracts" / "json-schema" / "player.v1.schema.json"


def player_payload(
    player: Any, source: str, season: str, source_url: str = "", raw_market_value: str = ""
) -> Dict[str, Any]:
    """Adapt legacy ``NormalizedPlayer`` to the canonical player.v1 contract."""
    name_parts = player.full_name.split(maxsplit=1)
    return {
        "schema_version": SCHEMA_VERSION,
        "source": source,
        "external_id": player.external_id if not player.external_id.startswith("manual:") else None,
        "source_url": source_url or None,
        "first_name": name_parts[0],
        "last_name": name_parts[1] if len(name_parts) > 1 else None,
        "full_name": player.full_name,
        "birth_date": player.birth_date.isoformat() if player.birth_date else None,
        "nationalities": [player.nationality] if player.nationality else [],
        "team": player.team,
        "source_role": player.source_role,
        "inferred_fantasy_role": player.fantasy_role,
        "official_fantasy_role": None,
        "preferred_foot": None,
        "height_cm": None,
        "market_value": player.market_value_eur,
        "market_value_currency": "EUR" if player.market_value_eur is not None else None,
        "raw_market_value": raw_market_value or None,
        "season": season,
    }


def _is_type(value: Any, expected: str) -> bool:
    return {
        "string": isinstance(value, str),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
        "null": value is None,
    }.get(expected, True)


def validate_player_v1(payload: Dict[str, Any]) -> List[str]:
    """Validate the supported JSON Schema vocabulary and return stable messages."""
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    errors: List[str] = []
    for field in schema["required"]:
        if field not in payload:
            errors.append(f"{field}: campo obbligatorio mancante")
    if schema.get("additionalProperties") is False:
        for field in payload:
            if field not in schema["properties"]:
                errors.append(f"{field}: campo non consentito")
    for field, rules in schema["properties"].items():
        if field not in payload:
            continue
        value = payload[field]
        allowed_types = rules.get("type")
        if allowed_types:
            allowed_types = allowed_types if isinstance(allowed_types, list) else [allowed_types]
            if not any(_is_type(value, expected) for expected in allowed_types):
                errors.append(f"{field}: tipo non valido")
                continue
        if value is not None and "const" in rules and value != rules["const"]:
            errors.append(f"{field}: valore schema non valido")
        if value is not None and "enum" in rules and value not in rules["enum"]:
            errors.append(f"{field}: valore non ammesso")
        if isinstance(value, str) and len(value) < rules.get("minLength", 0):
            errors.append(f"{field}: lunghezza insufficiente")
        if isinstance(value, (int, float)) and value < rules.get("minimum", float("-inf")):
            errors.append(f"{field}: valore inferiore al minimo")
        if (
            isinstance(value, str)
            and rules.get("pattern")
            and not re.fullmatch(rules["pattern"], value)
        ):
            errors.append(f"{field}: formato non valido")
        if rules.get("format") == "date" and value is not None:
            try:
                date.fromisoformat(value)
            except (TypeError, ValueError):
                errors.append(f"{field}: data ISO non valida")
        if isinstance(value, list) and "items" in rules:
            item_type = rules["items"].get("type")
            if item_type and any(not _is_type(item, item_type) for item in value):
                errors.append(f"{field}: elemento con tipo non valido")
    return errors

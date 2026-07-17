"""Configurable, deterministic team-name resolution."""

from typing import Dict, Optional

from .normalization import normalize_name

TEAM_ALIASES: Dict[str, str] = {
    "inter": "Inter",
    "internazionale": "Inter",
    "fc internazionale": "Inter",
    "internazionale milano": "Inter",
    "ac milan": "Milan",
    "milan": "Milan",
    "ssc napoli": "Napoli",
    "napoli": "Napoli",
}


def resolve_team_name(value: object, aliases: Optional[Dict[str, str]] = None) -> str:
    cleaned = normalize_name(value)
    if not cleaned:
        raise ValueError("Squadra non valida")
    alias_map = {normalize_name(key): target for key, target in (aliases or TEAM_ALIASES).items()}
    return alias_map.get(cleaned, " ".join(part.capitalize() for part in cleaned.split()))

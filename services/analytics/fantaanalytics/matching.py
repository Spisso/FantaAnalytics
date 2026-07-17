"""Explicit matching outcomes; ambiguous candidates are never merged automatically."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MatchResult:
    status: str
    player_id: Optional[int] = None
    reason: str = ""


MATCHED = "matched"
CREATED = "created"
AMBIGUOUS = "ambiguous"
INVALID = "invalid"

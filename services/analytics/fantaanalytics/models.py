"""Validated normalized records shared by import and analytics code."""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass(frozen=True)
class NormalizedPlayer:
    """Canonical player input; birth date is retained instead of a stale age."""

    external_id: str
    full_name: str
    normalized_name: str
    team: str
    birth_date: Optional[date]
    nationality: Optional[str]
    source_role: Optional[str]
    fantasy_role: str
    appearances: Optional[int] = None
    minutes: Optional[int] = None
    goals: Optional[float] = None
    assists: Optional[float] = None
    fantasy_average: Optional[float] = None
    starter_probability: Optional[float] = None
    rotation_risk: Optional[float] = None
    injury_risk: Optional[float] = None
    penalty_taker: bool = False
    set_piece_taker: bool = False
    team_strength: Optional[float] = None
    official_quotation: Optional[float] = None
    market_value_eur: Optional[int] = None


@dataclass(frozen=True)
class ImportIssue:
    row_number: int
    field: str
    message: str

"""Transfermarkt fetch-to-canonical CSV adapter; persistence stays in the import service."""

import csv
from datetime import datetime
from pathlib import Path

CANONICAL_FIELDS = [
    "external_id",
    "full_name",
    "team",
    "birth_date",
    "nationality",
    "source_role",
    "market_value",
    "source_url",
]


def to_canonical_row(player):
    birth_date = player.get("birth_date") or ""
    if birth_date:
        birth_date = datetime.strptime(birth_date, "%d/%m/%Y").date().isoformat()
    return {
        "external_id": player.get("external_id") or "",
        "full_name": player.get("full_name") or player.get("name") or "",
        "team": player.get("team") or "",
        "birth_date": birth_date,
        "nationality": player.get("nationality") or "",
        "source_role": player.get("source_role") or player.get("position") or "",
        "market_value": player.get("market_value") or "",
        "source_url": player.get("profile_url") or player.get("source_url") or "",
    }


def canonicalize_players(players):
    rows = []
    seen = set()
    for player in players:
        row = to_canonical_row(player)
        external_id = row["external_id"]
        if not external_id or external_id in seen:
            continue
        seen.add(external_id)
        rows.append(row)
    return rows


def write_canonical_csv(players, destination):
    rows = canonicalize_players(players)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path, rows

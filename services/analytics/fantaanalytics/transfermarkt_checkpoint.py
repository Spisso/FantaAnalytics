"""Versioned, atomic progress state for incremental Transfermarkt imports."""

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

CHECKPOINT_VERSION = 1
SOURCE = "transfermarkt"


class CheckpointError(ValueError):
    pass


def utc_now():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def new_checkpoint(season):
    now = utc_now()
    return {
        "version": CHECKPOINT_VERSION,
        "source": SOURCE,
        "season": season,
        "created_at": now,
        "updated_at": now,
        "completed_clubs": [],
        "failed_clubs": [],
    }


def load_checkpoint(path, season):
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return new_checkpoint(season)
    except (OSError, json.JSONDecodeError) as exc:
        raise CheckpointError(f"Checkpoint non leggibile o JSON corrotto: {path}") from exc
    if payload.get("version") != CHECKPOINT_VERSION:
        raise CheckpointError("Versione checkpoint non supportata")
    if payload.get("source") != SOURCE:
        raise CheckpointError("Fonte checkpoint diversa da transfermarkt")
    if payload.get("season") != season:
        raise CheckpointError(f"Stagione checkpoint diversa: attesa {season}")
    if not isinstance(payload.get("completed_clubs"), list) or not isinstance(
        payload.get("failed_clubs"), list
    ):
        raise CheckpointError("Struttura checkpoint non valida: squadre mancanti")
    return payload


def save_checkpoint(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(payload)
    payload["updated_at"] = utc_now()
    descriptor, temporary_path = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
    except OSError:
        try:
            os.unlink(temporary_path)
        except OSError:
            pass
        raise

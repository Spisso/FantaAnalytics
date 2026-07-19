"""Incremental Transfermarkt orchestration with per-club checkpoints."""

import os
import tempfile
from pathlib import Path

from scraper.transfermarkt import TransfermarktScraper

from .import_service import PlayerImportService
from .importer import import_csv
from .normalization import normalize_name
from .persistence import CanonicalRepository
from .transfermarkt_adapter import canonicalize_players, write_canonical_csv
from .transfermarkt_checkpoint import load_checkpoint, save_checkpoint, utc_now


def default_checkpoint(season):
    return Path("data/raw") / f"transfermarkt_{season}_checkpoint.json"


def _club_matches(club, value):
    needle = normalize_name(value)
    return needle in {
        normalize_name(club["name"]),
        normalize_name(club["external_id"]),
        normalize_name(club["external_id"].split(":")[-1]),
    }


def _replace_entry(entries, external_id, entry):
    entries[:] = [item for item in entries if item.get("external_id") != external_id]
    entries.append(entry)


def _write_session_csv(rows, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_path = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=destination.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_path)
    try:
        write_canonical_csv(rows, temporary)
        os.replace(temporary, destination)
    except Exception:
        try:
            temporary.unlink()
        except OSError:
            pass
        raise


def run_progressive_scrape(args):
    scraper = TransfermarktScraper(
        season=args.season,
        pause_seconds=args.pause,
        retries=args.retries,
    )
    checkpoint_path = None if args.dry_run else Path(args.checkpoint or default_checkpoint(args.season))
    checkpoint = None
    if checkpoint_path:
        checkpoint = load_checkpoint(checkpoint_path, args.season)

    descriptors = scraper.get_club_descriptors()
    selected = descriptors
    if args.club:
        selected = [club for club in descriptors if _club_matches(club, args.club)]
        if not selected:
            raise ValueError(f"Squadra non trovata: {args.club}")
    if args.start_club:
        start_index = next(
            (index for index, club in enumerate(selected) if _club_matches(club, args.start_club)),
            None,
        )
        if start_index is None:
            raise ValueError(f"Squadra di partenza non trovata: {args.start_club}")
        selected = selected[start_index:]

    completed_ids = {
        item.get("external_id") for item in (checkpoint or {}).get("completed_clubs", [])
    }
    failed_ids = {
        item.get("external_id") for item in (checkpoint or {}).get("failed_clubs", [])
    }
    if args.retry_failed:
        selected = [club for club in selected if club["external_id"] in failed_ids]
    session_rows = []
    summary = {
        "clubs_discovered": len(descriptors),
        "clubs_considered": 0,
        "clubs_completed": 0,
        "clubs_skipped": 0,
        "clubs_failed": 0,
        "profiles_requested": 0,
        "profiles_succeeded": 0,
        "profiles_failed": 0,
        "valid_players": 0,
        "records_valid": 0,
        "records_imported": 0,
        "inserted_players": 0,
        "updated_players": 0,
        "skipped_players": 0,
        "errors": [],
    }
    import_service = None if args.dry_run else PlayerImportService(CanonicalRepository(args.database))

    for club in selected:
        if args.resume and club["external_id"] in completed_ids:
            summary["clubs_skipped"] += 1
            continue
        if args.retry_failed:
            if club["external_id"] not in failed_ids:
                summary["clubs_skipped"] += 1
                continue
        if args.max_clubs is not None and summary["clubs_considered"] >= args.max_clubs:
            break
        summary["clubs_considered"] += 1
        details = {}
        valid_rows = 0
        try:
            players, details = scraper.get_players_for_club(club["roster_url"], args.max_players)
            summary["profiles_requested"] += details.get("profiles_requested", len(players) + len(details["errors"]))
            summary["profiles_succeeded"] += details.get("profiles_succeeded", len(players))
            summary["profiles_failed"] += details.get("profiles_failed", len(details["errors"]))
            rows = canonicalize_players(players)
            session_rows.extend(players)
            valid_rows = len(rows)
            validation_errors = 0
            import_result = None
            with tempfile.TemporaryDirectory(prefix="fantaanalytics-club-") as directory:
                temporary_csv = Path(directory) / "players.csv"
                write_canonical_csv(players, temporary_csv)
                normalized, issues = import_csv(temporary_csv)
                valid_rows = len(normalized)
                validation_errors = len(issues)
                if not args.dry_run:
                    import_result = import_service.import_file(
                        temporary_csv,
                        "transfermarkt",
                        args.season,
                        force=args.force or args.retry_failed,
                    )
            if import_result:
                summary["inserted_players"] += import_result.inserted_rows
                summary["updated_players"] += import_result.updated_rows
                summary["skipped_players"] += import_result.skipped_rows
                validation_errors = import_result.error_rows
                summary["records_imported"] += import_result.inserted_rows + import_result.updated_rows
            summary["valid_players"] += valid_rows
            summary["records_valid"] += valid_rows
            errors = details["errors"]
            if errors or validation_errors:
                problems = []
                if errors:
                    problems.append(f"{len(errors)} profili non recuperati")
                if validation_errors:
                    problems.append(f"{validation_errors} record non validi")
                raise RuntimeError("; ".join(problems))
            completed_entry = {
                "external_id": club["external_id"],
                "name": details["team"] or club["name"],
                "roster_url": club["roster_url"],
                "players_discovered": details["discovered"],
                "roster_url_final": details.get("final_url"),
                "roster_http_status": details.get("http_status"),
                "roster_response_length": details.get("response_length"),
                "roster_title": details.get("title"),
                "profile_anchors": details.get("profile_anchors"),
                "unique_external_ids": details.get("unique_external_ids"),
                "links_discarded": details.get("links_discarded", []),
                "players_valid": valid_rows,
                "players_imported": (
                    (import_result.inserted_rows + import_result.updated_rows)
                    if import_result
                    else valid_rows
                ),
                "profiles_requested": details.get("profiles_requested", len(players)),
                "profiles_failed": details.get("profiles_failed", len(errors)),
                "records_valid": valid_rows,
                "records_imported": (
                    (import_result.inserted_rows + import_result.updated_rows)
                    if import_result
                    else valid_rows
                ),
                "completed_at": utc_now(),
            }
            if checkpoint is not None:
                _replace_entry(checkpoint["completed_clubs"], club["external_id"], completed_entry)
                checkpoint["failed_clubs"] = [
                    item
                    for item in checkpoint["failed_clubs"]
                    if item.get("external_id") != club["external_id"]
                ]
                save_checkpoint(checkpoint_path, checkpoint)
            summary["clubs_completed"] += 1
        except Exception as exc:
            previous = next(
                (item for item in (checkpoint or {}).get("failed_clubs", [])
                 if item.get("external_id") == club["external_id"]),
                None,
            )
            error = {
                "external_id": club["external_id"],
                "name": club["name"],
                "roster_url": club["roster_url"],
                "error": str(exc),
                "players_discovered": details.get("discovered") if "details" in locals() else None,
                "roster_url_final": details.get("final_url") if "details" in locals() else None,
                "roster_http_status": details.get("http_status") if "details" in locals() else None,
                "roster_response_length": details.get("response_length") if "details" in locals() else None,
                "roster_title": details.get("title") if "details" in locals() else None,
                "profile_anchors": details.get("profile_anchors") if "details" in locals() else None,
                "unique_external_ids": details.get("unique_external_ids") if "details" in locals() else None,
                "links_discarded": details.get("links_discarded", []) if "details" in locals() else [],
                "profiles_requested": details.get("profiles_requested") if "details" in locals() else None,
                "profiles_failed": details.get("profiles_failed") if "details" in locals() else None,
                "records_valid": valid_rows if "valid_rows" in locals() else None,
                "attempts": (previous.get("attempts", 0) if previous else 0) + 1,
                "failed_at": utc_now(),
            }
            summary["clubs_failed"] += 1
            summary["errors"].append(error)
            if checkpoint is not None:
                _replace_entry(checkpoint["failed_clubs"], club["external_id"], error)
                save_checkpoint(checkpoint_path, checkpoint)
            if not args.continue_on_error:
                raise RuntimeError(f"Squadra {club['name']} fallita: {exc}") from exc

    if args.output:
        _write_session_csv(session_rows, args.output)
    summary["checkpoint"] = str(checkpoint_path) if checkpoint_path else "nessuno (dry-run)"
    summary["session_rows"] = len(session_rows)
    return summary

"""Offline CLI for analytics and canonical import lifecycle."""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict

from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig

from .import_service import PlayerImportService
from .importer import import_csv
from .persistence import CanonicalRepository, MigrationRunner
from .pricing import LeagueConfig, predict_prices
from .scoring import score_players
from .settings import Settings

DEFAULT_DATABASE = Settings.from_env().database_url


def _print_json(value: Dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))


def run_score(source: str, destination: str) -> int:
    players, issues = import_csv(source)
    if issues:
        for issue in issues:
            print(f"Riga {issue.row_number}: {issue.message}")
    scores = score_players(players)
    prices = {price.external_id: price for price in predict_prices(scores, LeagueConfig())}
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "external_id",
        "role",
        "score",
        "tier",
        "reliability",
        "risk",
        "baseline_price",
        "max_price",
        "explanation_it",
    ]
    with destination_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for score in scores:
            price = prices[score.external_id]
            writer.writerow(
                {
                    "external_id": score.external_id,
                    "role": score.fantasy_role,
                    "score": score.score,
                    "tier": score.tier,
                    "reliability": score.reliability,
                    "risk": score.risk,
                    "baseline_price": price.baseline_price,
                    "max_price": price.maximum_recommended_price,
                    "explanation_it": score.explanation_it,
                }
            )
    print(f"Esportati {len(scores)} score in {destination_path}")
    return 0 if not issues else 1


def run_import(args: argparse.Namespace) -> int:
    result = PlayerImportService(CanonicalRepository(args.database)).import_file(
        Path(args.file), args.source, args.season, strict=args.strict, force=args.force
    )
    if args.json_output:
        _print_json(result.as_dict())
    else:
        label = (
            "Import completato" if result.status == "completed" else "Import completato con errori"
        )
        if result.status == "skipped_duplicate_file":
            label = "Import già elaborato: nessun dato duplicato"
        print(label)
        print(f"Import run: {result.import_run_id}")
        print(f"Righe totali: {result.total_rows}")
        print(
            f"Valide: {result.valid_rows}; inserite: {result.inserted_rows}; aggiornate: {result.updated_rows}"
        )
        print(f"Saltate: {result.skipped_rows}; errori: {result.error_rows}")
        for error in result.errors:
            print(f"Riga {error.row_number} [{error.code}]: {error.message}")
    return 2 if args.strict and result.error_rows else 0


def run_list(args: argparse.Namespace) -> int:
    players = CanonicalRepository(args.database).list_players(
        args.role, args.team, args.season, args.limit
    )
    if args.json_output:
        _print_json({"players": players, "count": len(players)})
    elif not players:
        print("Nessun giocatore trovato.")
    else:
        for player in players:
            print(
                f"{player['canonical_full_name']} | {player['effective_fantasy_role']} | {player['team']} | {player['season']}"
            )
    return 0


def _run_alembic(database_url: str, revision: str) -> None:
    config = AlembicConfig("alembic.ini")
    config.attributes["database_url"] = database_url
    alembic_command.upgrade(config, revision) if revision == "head" else alembic_command.downgrade(
        config, revision
    )


def run_upgrade(database) -> int:
    if "://" in str(database):
        _run_alembic(str(database), "head")
        print("Database aggiornato con Alembic")
        return 0
    migrations = MigrationRunner(database).upgrade()
    print(
        "Database aggiornato" + (f": {', '.join(migrations)}" if migrations else ": già aggiornato")
    )
    return 0


def run_downgrade(database) -> int:
    if "://" in str(database):
        _run_alembic(str(database), "base")
        print("Database riportato alla base con Alembic")
        return 0
    version = MigrationRunner(database).downgrade()
    print(f"Database downgrade: {version}" if version else "Nessuna migrazione da annullare")
    return 0


def run_reset_test(database: Path) -> int:
    if not database.name.endswith(".test.db"):
        raise ValueError("db-reset-test accetta solo database con suffisso .test.db")
    if database.exists():
        database.unlink()
    return run_upgrade(database)


def main() -> int:
    parser = argparse.ArgumentParser(description="FantaAnalytics deterministic analytics")
    subparsers = parser.add_subparsers(dest="command", required=True)
    score = subparsers.add_parser("score", help="Importa CSV e genera score/prezzi")
    score.add_argument("source")
    score.add_argument("destination")
    for name, handler in (("db-upgrade", run_upgrade), ("db-downgrade", run_downgrade)):
        command = subparsers.add_parser(name)
        command.add_argument("--database", default=DEFAULT_DATABASE)
        command.set_defaults(handler=handler)
    reset = subparsers.add_parser("db-reset-test")
    reset.add_argument("--database", type=Path, default=Path("data/processed/fantaanalytics.test.db"))
    reset.set_defaults(handler=run_reset_test)
    imported = subparsers.add_parser(
        "import-players", help="Importa giocatori nel database canonico"
    )
    imported.add_argument("--file", required=True)
    imported.add_argument("--source", required=True)
    imported.add_argument("--season", required=True)
    imported.add_argument("--database", default=DEFAULT_DATABASE)
    imported.add_argument("--strict", action="store_true")
    imported.add_argument("--force", action="store_true")
    imported.add_argument("--json-output", action="store_true")
    imported.set_defaults(handler=run_import)
    listed = subparsers.add_parser("list-players", help="Elenca i giocatori canonici importati")
    listed.add_argument("--database", default=DEFAULT_DATABASE)
    listed.add_argument("--role", choices=["P", "D", "C", "A"])
    listed.add_argument("--team")
    listed.add_argument("--season")
    listed.add_argument("--limit", type=int, default=50)
    listed.add_argument("--json-output", action="store_true")
    listed.set_defaults(handler=run_list)
    args = parser.parse_args()
    try:
        if args.command == "score":
            return run_score(args.source, args.destination)
        return args.handler(args.database) if args.command.startswith("db-") else args.handler(args)
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

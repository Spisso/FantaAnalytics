.DEFAULT_GOAL := help
PYTHON ?= $(or $(wildcard .venv/bin/python),$(wildcard venv/bin/python),python3)
DATABASE ?= data/processed/fantaanalytics.db

.PHONY: help bootstrap test test-unit lint format seed-demo import-sample list-players db-upgrade db-downgrade db-reset-test score export clean

help:
	@echo "Available targets: bootstrap test lint db-upgrade import-sample list-players seed-demo"

bootstrap:
	$(PYTHON) -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/python -m pip install -r requirements-dev.txt

test test-unit:
	$(PYTHON) -m unittest discover -s tests -v

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

seed-demo:
	@mkdir -p data/exports
	$(PYTHON) -m services.analytics.fantaanalytics.cli score data/samples/demo_players.csv data/exports/demo_player_scores.csv

db-upgrade:
	$(PYTHON) -m services.analytics.fantaanalytics.cli db-upgrade --database $(DATABASE)

db-downgrade:
	$(PYTHON) -m services.analytics.fantaanalytics.cli db-downgrade --database $(DATABASE)

db-reset-test:
	$(PYTHON) -m services.analytics.fantaanalytics.cli db-reset-test --database data/processed/fantaanalytics.test.db

import-sample: db-upgrade
	$(PYTHON) -m services.analytics.fantaanalytics.cli import-players --file data/samples/demo_players.csv --source demo --season 2026-27 --database $(DATABASE)

list-players:
	$(PYTHON) -m services.analytics.fantaanalytics.cli list-players --database $(DATABASE) --season 2026-27

score: seed-demo

export: seed-demo

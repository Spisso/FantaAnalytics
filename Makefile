.DEFAULT_GOAL := help
PYTHON ?= $(or $(wildcard .venv/bin/python),$(wildcard venv/bin/python),python3)
DATABASE ?= data/processed/fantaanalytics.db
IMPORT_RUNTIME ?= local

.PHONY: help bootstrap test test-unit lint format seed-demo import-sample import-serie-a list-players db-upgrade db-downgrade db-reset-test score export clean api-install api-test api-lint api-up api-shell api-logs api-health api-db-create api-migrate api-migrate-fresh api-seed-demo stack-up stack-down stack-test

USER_ID := $(shell id -u)
GROUP_ID := $(shell id -g)
COMPOSER_RUN = docker run --rm -u $(USER_ID):$(GROUP_ID) -v $(CURDIR)/apps/api:/app -w /app composer:2

help:
	@echo "Available targets: bootstrap test lint db-upgrade import-sample import-serie-a list-players seed-demo api-test api-lint stack-up stack-test"

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

ifeq ($(IMPORT_RUNTIME),docker)
import-serie-a:
	docker compose exec analytics alembic upgrade head
	docker compose exec analytics python -m services.analytics.fantaanalytics.cli scrape-transfermarkt --season 2026-27 --output /app/data/raw/transfermarkt_players.csv
else
import-serie-a: db-upgrade
	$(PYTHON) -m services.analytics.fantaanalytics.cli scrape-transfermarkt --season 2026-27 --database $(DATABASE) --output data/raw/transfermarkt_players.csv
endif

list-players:
	$(PYTHON) -m services.analytics.fantaanalytics.cli list-players --database $(DATABASE) --season 2026-27

score: seed-demo

export: seed-demo

api-install:
	$(COMPOSER_RUN) composer install --no-interaction --prefer-dist

api-test:
	@test -f apps/api/vendor/autoload.php || $(MAKE) api-install
	cd apps/api && php artisan test

api-lint:
	@test -f apps/api/vendor/autoload.php || $(MAKE) api-install
	apps/api/vendor/bin/pint --test

api-up:
	docker compose up -d api

api-shell:
	docker compose exec api sh

api-logs:
	docker compose logs --tail=100 api

api-health:
	curl --fail http://localhost:$${API_PORT:-8081}/api/v1/health

api-db-create:
	docker compose exec -T -e APP_POSTGRES_DB="$${APP_POSTGRES_DB:-fantaanalytics_app}" postgres sh -c 'if ! psql -U "$${POSTGRES_USER}" -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='"'"'$${APP_POSTGRES_DB}'"'"'" | grep -q 1; then createdb -U "$${POSTGRES_USER}" "$${APP_POSTGRES_DB}"; fi'

api-migrate: api-db-create
	docker compose exec -T api php artisan migrate --force

api-migrate-fresh: api-db-create
	@test "$${CONFIRM_DESTRUCTIVE}" = "1" || (echo "Impostare CONFIRM_DESTRUCTIVE=1 solo in sviluppo" && exit 1)
	docker compose exec -T api php artisan migrate:fresh --force

api-seed-demo: api-migrate
	docker compose exec -T api php artisan db:seed --force

stack-up:
	docker compose up -d postgres analytics
	docker compose exec -T analytics alembic upgrade head
	docker compose up -d api
	$(MAKE) api-migrate

stack-down:
	docker compose down

stack-test: stack-up
	docker compose exec analytics python -m services.analytics.fantaanalytics.cli import-players --file data/samples/demo_players.csv --source demo --season 2026-27
	curl --fail http://localhost:$${ANALYTICS_API_PORT:-8000}/health
	curl --fail http://localhost:$${ANALYTICS_API_PORT:-8000}/ready
	curl --fail http://localhost:$${API_PORT:-8081}/api/v1/health
	curl --fail http://localhost:$${API_PORT:-8081}/api/v1/analytics/status
	curl --fail "http://localhost:$${API_PORT:-8081}/api/v1/players?season=2026-27"

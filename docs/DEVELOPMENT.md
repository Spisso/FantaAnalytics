# Sviluppo

Prerequisito: Python 3.9+ (3.11+ consigliato). Eseguire:

```bash
make bootstrap
make test
make lint
make seed-demo
```

`make seed-demo` crea `data/exports/demo_player_scores.csv`. Non sovrascrive `.env`; le variabili di esempio sono in `.env.example`. Il vecchio `venv/` non è gestito dal Makefile: usare `.venv/` creato da bootstrap.

Persistenza e CLI locale:

```bash
make db-upgrade
make import-sample
make list-players
make db-reset-test
```

`db-reset-test` accetta solo un file con suffisso `.test.db`; non punta al database operativo. La migrazione può essere annullata con `make db-downgrade`. I comandi `db-upgrade`, `import-sample`, `list-players`, `seed-demo`, `test` e `lint` sono stati eseguiti con il `venv/` locale in questa milestone. `make bootstrap` è il percorso di installazione documentato ma non è stato eseguito qui.

`DATABASE_URL` ha priorità sul fallback `sqlite:///data/processed/fantaanalytics.db`. Nel container è configurata come URL `postgresql+psycopg`; Alembic la legge dagli stessi settings di API e CLI. Flusso PostgreSQL verificato (cold start-safe):

```bash
docker compose build analytics
make stack-up
docker compose exec analytics python -m services.analytics.fantaanalytics.cli import-players --file data/samples/demo_players.csv --source demo --season 2026-27
docker compose exec analytics python -m services.analytics.fantaanalytics.cli list-players --season 2026-27
```

`make stack-up` avvia PostgreSQL e Analytics, applica Alembic prima di avviare
Laravel e applica le migrazioni del database applicativo. Non eseguire `docker
compose up -d ... api` direttamente su un volume PostgreSQL vuoto: usare il
target per mantenere l'ordine di inizializzazione.

Ruff verifica errori e import; `E501` è escluso perché il repository conserva fixture HTML, payload CSV e query SQL leggibili che superano la soglia tipografica senza incidere sul comportamento. Le regole di upgrade automatico sono escluse per mantenere la compatibilità con Python 3.9.

## Laravel API

PHP 8.2+ è richiesto. Se Composer non è installato localmente, il Makefile usa l'immagine ufficiale:

```bash
make api-install
make api-lint
make api-test
make api-up
make api-shell
make api-logs
make api-health
```

I test usano `Http::fake()` e non richiedono Analytics reale. `PlayerIndexRequest` accetta solo `role`, `team`, `season` e `limit`; configurazione e timeout risiedono in `config/services.php`, non nei controller.

Dominio lega e database applicativo:

```bash
make api-migrate
make api-seed-demo
CONFIRM_DESTRUCTIVE=1 make api-migrate-fresh
```

`api-migrate-fresh` è intenzionalmente protetto e va usato solo in sviluppo. Il seed demo è idempotente e crea `demo@fantaanalytics.local`, una lega 2026-27 e dieci partecipanti. Le API protette usano temporaneamente l'header `X-User-ID`.

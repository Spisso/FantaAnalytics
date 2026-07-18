# Current status

## Last verified milestone

Adapter Transfermarkt collegato alla pipeline canonica Analytics.

## Currently implementing

Import Serie A tramite fixture/mock completato; verifica live separata. Vue resta fuori scope.

## Completed

- [x] Audit del checkout e preservazione del prototipo Python.
- [x] Servizio analytics Python con import CSV, score e prezzi offline.
- [x] Migrazione SQLite esplicita, repository canonico e import run tracciati.
- [x] Checksum file/riga, matching deterministico, upsert e strict/best-effort.
- [x] CLI `db-upgrade`, `import-players`, `list-players` e contratti testati.
- [x] API WSGI read-only: health, import run, player filtrabili/detail e OpenAPI.
- [x] Docker Compose con PostgreSQL 16 e analytics Gunicorn.
- [x] Alembic usa `DATABASE_URL` e crea lo schema PostgreSQL portabile.
- [x] `/health` liveness e `/ready` database/schema readiness.
- [x] Import PostgreSQL di 11 player, re-import file-first idempotente e volume persistente.
- [x] Laravel 12 API-only con health, analytics status, player e import-runs.
- [x] Client HTTP con DTO, filtri validati, timeout e mapping errori.
- [x] Stack Docker PostgreSQL → Analytics → Laravel e test di degradazione/ripristino.
- [x] CI per Python, Laravel, contratto e integrazione PostgreSQL.
- [x] Database `fantaanalytics_app`, migrazioni users/league domain e rollback.
- [x] Aggregate lega transazionale, owner participant, rules e roster defaults.
- [x] Policy owner/participant, guest participant, participant limit e seed demo idempotente.
- [x] API CRUD leghe, rules, roster rules e participants.
- [x] Scraper Transfermarkt con external ID stabile, URL deduplicate, pausa e retry limitati.
- [x] Adapter CSV canonico e comando `scrape-transfermarkt` con import SQLAlchemy idempotente.
- [x] `main.py`, Makefile e container Analytics usano la pipeline canonica, non il DB legacy.

## Remaining

- [ ] Frontend Vue.
- [ ] Proiezioni, asta live, analisi rosa, optimizer e coach.
- [ ] CI, E2E applicativo e hardening di produzione.

## Tests last executed

- preview live controllata Transfermarkt — 1 club, 3 profili, 3 record validi, nessun campo mancante e nessuna persistenza.
- `make test` — 42 test superati, inclusi limiti/dry-run scraper senza richieste HTTP reali.
- `make db-upgrade DATABASE=/private/tmp/fantaanalytics-accept.test.db` — migrazione `001` applicata.
- `make import-sample DATABASE=/private/tmp/fantaanalytics-accept.test.db` — 11 player inseriti.
- `make list-players DATABASE=/private/tmp/fantaanalytics-accept.test.db` — 11 player interrogati.
- `make seed-demo` — 11 score esportati.
- `make lint` — superato.
- `docker compose exec analytics alembic upgrade head` — revisione `001` applicata a PostgreSQL.
- import demo PostgreSQL — 11 player inseriti; secondo import saltato come duplicato; conteggio 11.
- endpoint health/readiness/list/detail/import-runs — HTTP 200.
- `docker compose restart postgres` — volume persistente, readiness verde e conteggio ancora 11.
- `make api-test` — 19 test Laravel, 84 assertion superati.
- `make api-migrate` e `make api-seed-demo` — PostgreSQL applicativo verificato con 10 partecipanti.
- `make api-lint` — Laravel Pint superato.
- endpoint Laravel reali — health/status/list/detail/import-runs HTTP 200 su porta 8081.
- Analytics fermato — Laravel health 200, status degradato 200, players 503; ripristino verificato.
- build Docker Analytics/Laravel e `make stack-test` — superati nella revisione finale.
- import Transfermarkt con mock nel container su PostgreSQL temporaneo — 1 player inserito, CSV raw scrivibile e cleanup completato.
- `api-db-create` — creazione e seconda esecuzione idempotente verificate con `fantaanalytics_app_codex_test`, poi rimosso.

## Known limitations

- Il listino demo è intenzionalmente ridotto e fittizio; non è un dataset Serie A reale.
- Il prezzo è una baseline deterministica, non un modello addestrato né una raccomandazione d'asta live.
- Vue, autenticazione e dominio leghe/aste/rose non sono ancora implementati.
- SQLite è il backend locale/test; PostgreSQL è il backend Docker verificato.
- Lo scraping live dipende da raggiungibilità, termini e markup Transfermarkt; CAPTCHA e controlli di accesso non vengono aggirati.
- `database/transfermarkt.db` non è presente nell'indice Git; `database/*.db`, `*.sqlite3` e `data/raw/*` restano ignorati.

## Exact next action

Verificare manualmente l'import contro la fonte solo se consentito, poi riprendere il dominio asta senza introdurre Vue o realtime.

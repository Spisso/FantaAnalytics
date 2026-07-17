# Current status

## Last verified milestone

PostgreSQL end-to-end: Alembic → schema canonico → import demo idempotente → API/CLI → persistenza del volume.

## Currently implementing

Repository SQLAlchemy condiviso tra SQLite e PostgreSQL, con configurazione `DATABASE_URL` unica e health/readiness separate.

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

## Remaining

- [ ] Laravel e frontend Vue.
- [ ] Proiezioni, asta live, analisi rosa, optimizer e coach.
- [ ] CI, E2E applicativo e hardening di produzione.

## Tests last executed

- `make test` — 31 test superati (27 originali più settings, readiness e redazione segreti).
- `make db-upgrade DATABASE=/private/tmp/fantaanalytics-accept.test.db` — migrazione `001` applicata.
- `make import-sample DATABASE=/private/tmp/fantaanalytics-accept.test.db` — 11 player inseriti.
- `make list-players DATABASE=/private/tmp/fantaanalytics-accept.test.db` — 11 player interrogati.
- `make seed-demo` — 11 score esportati.
- `make lint` — superato.
- `docker compose exec analytics alembic upgrade head` — revisione `001` applicata a PostgreSQL.
- import demo PostgreSQL — 11 player inseriti; secondo import saltato come duplicato; conteggio 11.
- endpoint health/readiness/list/detail/import-runs — HTTP 200.
- `docker compose restart postgres` — volume persistente, readiness verde e conteggio ancora 11.

## Known limitations

- Il listino demo è intenzionalmente ridotto e fittizio; non è un dataset Serie A reale.
- Il prezzo è una baseline deterministica, non un modello addestrato né una raccomandazione d'asta live.
- Nessun servizio Laravel/Vue, autenticazione o database PostgreSQL è ancora presente.
- SQLite è il backend locale/test; PostgreSQL è il backend Docker verificato.
- `database/transfermarkt.db` è ancora nel commit corrente: il sandbox non permette scritture nell'indice Git per eseguire il richiesto `git rm --cached`.

## Exact next action

Aggiungere CI con un service PostgreSQL per eseguire automaticamente migrazione e smoke test d'import.

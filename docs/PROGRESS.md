# Current status

## Last verified milestone

Persistenza canonica: CSV demo → contratto `player.v1` → import run/raw provenance → upsert idempotente → query CLI.

## Currently implementing

Fondazione monorepo e modello dati Python: repository SQLite e API WSGI read-only sono pronti; PostgreSQL resta il prossimo confine infrastrutturale.

## Completed

- [x] Audit del checkout e preservazione del prototipo Python.
- [x] Servizio analytics Python con import CSV, score e prezzi offline.
- [x] Migrazione SQLite esplicita, repository canonico e import run tracciati.
- [x] Checksum file/riga, matching deterministico, upsert e strict/best-effort.
- [x] CLI `db-upgrade`, `import-players`, `list-players` e contratti testati.
- [x] API WSGI read-only: health, import run, player filtrabili/detail e OpenAPI.

## Remaining

- [ ] PostgreSQL/Laravel e frontend Vue.
- [ ] Proiezioni, asta live, analisi rosa, optimizer e coach.
- [ ] Docker Compose, CI, E2E e hardening.

## Tests last executed

- `make test` — 27 test superati.
- `make db-upgrade DATABASE=/private/tmp/fantaanalytics-accept.test.db` — migrazione `001` applicata.
- `make import-sample DATABASE=/private/tmp/fantaanalytics-accept.test.db` — 11 player inseriti.
- `make list-players DATABASE=/private/tmp/fantaanalytics-accept.test.db` — 11 player interrogati.
- `make seed-demo` — 11 score esportati.
- `make lint` — superato.

## Known limitations

- Il listino demo è intenzionalmente ridotto e fittizio; non è un dataset Serie A reale.
- Il prezzo è una baseline deterministica, non un modello addestrato né una raccomandazione d'asta live.
- Nessun servizio Laravel/Vue, autenticazione o database PostgreSQL è ancora presente.
- SQLite è il backend locale/test; non è un sostituto dichiarato del PostgreSQL di produzione.
- `database/transfermarkt.db` è ancora nel commit corrente: il sandbox non permette scritture nell'indice Git per eseguire il richiesto `git rm --cached`.

## Exact next action

Introdurre una configurazione PostgreSQL d'integrazione dietro il repository, senza cambiare le regole di import o il contratto `player.v1`.
